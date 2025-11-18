from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import numpy as np
import trimesh
from trimesh import transformations


logger = logging.getLogger(__name__)


@dataclass
class PieceGeometry:
    """Container for fully transformed meshes ready for export."""

    piece_id: str
    mesh: trimesh.Trimesh
    source_path: Optional[Path] = None
    metadata: Dict[str, float] = field(default_factory=dict)


class GeometryPipeline:
    """Geometry utilities that convert LiDAR scans into printable meshes."""

    SUPPORTED_EXTS = {".obj", ".stl", ".ply", ".fbx"}

    @classmethod
    def build_piece_meshes(
        cls,
        pieces: Iterable["PiecePlan"],
        scan_paths: List[Path],
    ) -> List[PieceGeometry]:
        geometries: List[PieceGeometry] = []
        scan_cycle = list(path for path in scan_paths if path and path.exists())
        for idx, piece in enumerate(pieces):
            piece_id = cls._sanitize_piece_id(piece.piece_id or f"piece-{idx + 1}")
            mesh: Optional[trimesh.Trimesh] = None
            source_path: Optional[Path] = None
            if scan_cycle:
                candidate = scan_cycle[idx % len(scan_cycle)]
                if candidate.suffix.lower() in cls.SUPPORTED_EXTS:
                    mesh = cls.load_mesh(candidate)
                    source_path = candidate
            if mesh is None:
                mesh = cls._synthetic_box(piece, idx)
                logger.info("Using synthetic geometry for %s", piece_id)

            mesh = cls.slice_with_kuka(mesh, piece.optimal_cut_angle)
            mesh = cls.apply_plan_transform(mesh, piece, idx)
            mesh = cls.remesh_watertight(mesh)

            geometries.append(
                PieceGeometry(
                    piece_id=piece_id,
                    mesh=mesh,
                    source_path=source_path,
                    metadata={
                        "cut_angle": float(piece.optimal_cut_angle or 0.0),
                        "mass_kg": float(piece.mass_kg or 0.0),
                    },
                )
            )
        return geometries

    @classmethod
    def load_mesh(cls, path: Path) -> trimesh.Trimesh:
        logger.info("Loading real scan mesh from %s", path)
        mesh = trimesh.load(path, force="mesh", skip_materials=True, process=True)
        if isinstance(mesh, trimesh.Scene):
            mesh = trimesh.util.concatenate(tuple(mesh.geometry.values()))
        mesh = cls._normalize_units(mesh)
        return mesh

    @staticmethod
    def _normalize_units(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
        extents = mesh.bounding_box.extents
        max_extent = float(extents.max()) if extents.size else 0.0
        scale = 1.0
        if max_extent and max_extent < 50:  # assume meters, convert to millimeters
            scale = 1000.0
        elif max_extent > 100000:  # already in millimeters, convert to meters? keep mm
            scale = 1.0
        normalized = mesh.copy()
        if scale != 1.0:
            normalized.apply_scale(scale)
            logger.info("Normalized mesh scale by %.1f to millimeters", scale)
        return normalized

    @classmethod
    def slice_with_kuka(cls, mesh: trimesh.Trimesh, angle_deg: float) -> trimesh.Trimesh:
        angle = math.radians(angle_deg or 0.0)
        normal = np.array([math.cos(angle), 0.0, math.sin(angle)], dtype=float)
        normal /= np.linalg.norm(normal) or 1.0
        origin = mesh.centroid
        logger.info("Applying KUKA cut at %.2f°", angle_deg or 0.0)
        sliced = cls._keep_halfspace(mesh, origin, normal)
        return sliced

    @classmethod
    def apply_plan_transform(
        cls,
        mesh: trimesh.Trimesh,
        piece: "PiecePlan",
        piece_index: int = 0,
    ) -> trimesh.Trimesh:
        mesh = mesh.copy()
        center = piece.center_of_mass or {}
        fallback = cls._fallback_center(piece_index)
        translation = np.array(
            [
                float(center.get("x", fallback[0])),
                float(center.get("y", fallback[1])),
                float(center.get("z", fallback[2])),
            ],
            dtype=float,
        )
        rotation = math.radians(piece.optimal_cut_angle or 0.0)
        transform = transformations.euler_matrix(0.0, rotation, 0.0, "sxyz")
        transform[:3, 3] = translation
        mesh.apply_transform(transform)
        logger.info("Applied reuse transform to %s (translation=%s)", piece.piece_id, translation)
        return mesh

    @staticmethod
    def remesh_watertight(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
        mesh = mesh.copy()
        if not mesh.is_watertight:
            logger.info("Mesh not watertight; repairing...")
        mesh.remove_duplicate_faces()
        mesh.remove_degenerate_faces()
        mesh.fill_holes()
        mesh.remove_unreferenced_vertices()
        if not mesh.is_watertight:
            logger.info("Watertight check failed initially; running convex hull patch")
            mesh = mesh.convex_hull
        logger.info("Watertight check: %s", mesh.is_watertight)
        return mesh

    @staticmethod
    def _fallback_center(index: int) -> tuple[float, float, float]:
        return (index * 650.0 - 1500.0, 500.0 + index * 50.0, index * 120.0)

    @classmethod
    def _synthetic_box(cls, piece: "PiecePlan", idx: int) -> trimesh.Trimesh:
        width = 600.0
        depth = 600.0
        height = max(200.0, min(2500.0, (piece.mass_kg or 400.0) * 4))
        mesh = trimesh.creation.box(extents=(width, height, depth))
        return mesh

    @staticmethod
    def _sanitize_piece_id(piece_id: str) -> str:
        safe = piece_id.replace(" ", "-").lower()
        return safe

    @classmethod
    def _keep_halfspace(
        cls,
        mesh: trimesh.Trimesh,
        plane_origin: np.ndarray,
        plane_normal: np.ndarray,
        tol: float = 1e-6,
    ) -> trimesh.Trimesh:
        vertices = mesh.vertices
        faces = mesh.faces
        distances = (vertices - plane_origin).dot(plane_normal)
        new_vertices = vertices.tolist()
        new_faces: List[List[int]] = []
        edge_vertex_cache: Dict[tuple[int, int], int] = {}

        for face in faces:
            face_dist = distances[face]
            if np.all(face_dist >= -tol):
                new_faces.append(face.tolist())
                continue
            if np.all(face_dist < tol * -1):
                continue
            clipped = cls._clip_face(
                face,
                face_dist,
                vertices,
                edge_vertex_cache,
                new_vertices,
                tol,
            )
            if len(clipped) >= 3:
                anchor = clipped[0]
                for i in range(1, len(clipped) - 1):
                    new_faces.append([anchor, clipped[i], clipped[i + 1]])

        if not new_faces:
            logger.warning("Plane clipping removed all faces; returning original mesh")
            return mesh.copy()

        sliced_mesh = trimesh.Trimesh(vertices=np.array(new_vertices), faces=np.array(new_faces), process=True)
        sliced_mesh.remove_unreferenced_vertices()
        sliced_mesh.fill_holes()
        return sliced_mesh

    @staticmethod
    def _clip_face(
        face: np.ndarray,
        face_dist: np.ndarray,
        vertices: np.ndarray,
        edge_vertex_cache: Dict[tuple[int, int], int],
        new_vertices: List[List[float]],
        tol: float,
    ) -> List[int]:
        clipped: List[int] = []
        for i in range(len(face)):
            current_index = int(face[i])
            next_index = int(face[(i + 1) % len(face)])
            current_dist = float(face_dist[i])
            next_dist = float(face_dist[(i + 1) % len(face)])
            if current_dist >= -tol:
                clipped.append(current_index)
            intersects = (current_dist >= -tol and next_dist < -tol) or (current_dist < -tol and next_dist >= -tol)
            if intersects:
                edge_key = tuple(sorted((current_index, next_index)))
                if edge_key in edge_vertex_cache:
                    new_index = edge_vertex_cache[edge_key]
                else:
                    direction = vertices[next_index] - vertices[current_index]
                    denom = current_dist - next_dist
                    t = 0.0 if denom == 0 else current_dist / denom
                    point = vertices[current_index] + direction * t
                    new_vertices.append(point.tolist())
                    new_index = len(new_vertices) - 1
                    edge_vertex_cache[edge_key] = new_index
                clipped.append(new_index)
        return clipped


from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from .processor import PiecePlan
