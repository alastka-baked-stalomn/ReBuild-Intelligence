from __future__ import annotations

import math
from typing import Iterable, List

from .processor import PiecePlan


def _normalize_center(center: dict | None, idx: int) -> tuple[float, float, float]:
    if not isinstance(center, dict):
        center = {}
    fallback_x = idx * 0.65 - 2.0
    return (
        float(center.get("x", fallback_x)),
        float(center.get("y", 0.6 + idx * 0.05)),
        float(center.get("z", 0.0)),
    )


def _piece_vertices(piece: PiecePlan, idx: int) -> List[tuple[float, float, float]]:
    width = 0.6
    depth = 0.6
    height = max(0.25, min(2.5, piece.mass_kg / 120 if piece.mass_kg else 0.4))
    half_w = width / 2
    half_d = depth / 2
    half_h = height / 2

    base_vertices = [
        (-half_w, -half_h, -half_d),
        (half_w, -half_h, -half_d),
        (half_w, half_h, -half_d),
        (-half_w, half_h, -half_d),
        (-half_w, -half_h, half_d),
        (half_w, -half_h, half_d),
        (half_w, half_h, half_d),
        (-half_w, half_h, half_d),
    ]

    angle = math.radians(piece.optimal_cut_angle or 0.0)
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)

    cx, cy, cz = _normalize_center(piece.center_of_mass, idx)

    rotated = []
    for x, y, z in base_vertices:
        rx = x * cos_a - z * sin_a
        rz = x * sin_a + z * cos_a
        rotated.append((rx + cx, y + cy, rz + cz))
    return rotated


def pieces_to_obj(pieces: Iterable[PiecePlan]) -> str:
    lines: List[str] = ["# ReBuild Intelligence OBJ export"]
    vertex_offset = 0
    for idx, piece in enumerate(pieces):
        name = piece.piece_id or f"piece-{idx + 1}"
        vertices = _piece_vertices(piece, idx)
        lines.append(f"o {name}")
        for vx, vy, vz in vertices:
            lines.append(f"v {vx:.6f} {vy:.6f} {vz:.6f}")
        faces = [
            (1, 2, 3, 4),
            (5, 6, 7, 8),
            (1, 5, 8, 4),
            (2, 6, 7, 3),
            (4, 3, 7, 8),
            (1, 2, 6, 5),
        ]
        for a, b, c, d in faces:
            lines.append(
                f"f {vertex_offset + a} {vertex_offset + b} {vertex_offset + c} {vertex_offset + d}"
            )
        vertex_offset += len(vertices)
    return "\n".join(lines) + "\n"
