from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import numpy as np


@dataclass
class UploadedFileMeta:
    filename: str
    content_type: str
    size_kb: float


@dataclass
class ProjectInputs:
    project_name: str
    description: str
    transport_plan: str
    human_built: bool
    site_location: str
    soil_profile: str
    hazard_profile: str
    demolition_notes: str
    lidar_notes: str
    files: List[UploadedFileMeta] = field(default_factory=list)
    scans: List[UploadedFileMeta] = field(default_factory=list)


@dataclass
class PiecePlan:
    piece_id: str
    mass_kg: float
    center_of_mass: Dict[str, float]
    optimal_cut_angle: float
    waste_reduction: float
    reuse_score: float


@dataclass
class AlgorithmResult:
    project_name: str
    summary: str
    piece_plans: List[PiecePlan]
    cutting_instructions: List[str]
    reuse_breakdown: Dict[str, float]
    disaster_simulation: Dict[str, str]
    pollution_model: Dict[str, float]
    structural_analysis: Dict[str, float]
    cost_and_carbon: Dict[str, float]
    recommendations: List[str]


class AlgorithmProcessor:
    """High level processor that mocks the behaviour of the future AI pipeline."""

    def __init__(self) -> None:
        # Seed a deterministic generator so that previews are reproducible for demo purposes.
        self._rng = random.Random(42)

    def process(self, inputs: ProjectInputs) -> AlgorithmResult:
        pieces = self._generate_piece_plans(inputs)
        cutting_instructions = self._generate_cutting_plan(pieces, inputs)
        reuse_breakdown = self._estimate_reuse(inputs, pieces)
        disaster_simulation = self._simulate_disasters(inputs)
        pollution_model = self._estimate_pollution(inputs)
        structural_analysis = self._run_structural_analysis(pieces)
        cost_and_carbon = self._estimate_cost_and_carbon(inputs, reuse_breakdown)
        recommendations = self._generate_recommendations(reuse_breakdown, inputs)

        summary = (
            f"Processed {inputs.project_name} with {len(inputs.files)} uploaded assets. "
            f"Estimated that {reuse_breakdown['reused_pct']:.1f}% of the structure "
            "can be built from reclaimed material."
        )

        return AlgorithmResult(
            project_name=inputs.project_name,
            summary=summary,
            piece_plans=pieces,
            cutting_instructions=cutting_instructions,
            reuse_breakdown=reuse_breakdown,
            disaster_simulation=disaster_simulation,
            pollution_model=pollution_model,
            structural_analysis=structural_analysis,
            cost_and_carbon=cost_and_carbon,
            recommendations=recommendations,
        )

    # ------------------------------------------------------------------
    # Synthetic algorithm components
    # ------------------------------------------------------------------
    def _generate_piece_plans(self, inputs: ProjectInputs) -> List[PiecePlan]:
        base_count = max(len(inputs.files), 3)
        lidar_bonus = len(inputs.scans) * 2
        piece_count = min(base_count + lidar_bonus, 12)

        pieces: List[PiecePlan] = []
        for idx in range(piece_count):
            mass = 120 + 20 * math.sin(idx) + self._rng.uniform(-15, 15)
            coordinates = {
                "x": round(0.5 * idx + self._rng.uniform(-0.25, 0.25), 2),
                "y": round(self._rng.uniform(0.1, 4.0), 2),
                "z": round(self._rng.uniform(-0.5, 0.5), 2),
            }
            angle = round((idx * 17.5) % 180, 2)
            waste_reduction = round(15 + self._rng.uniform(0, 25), 2)
            reuse_score = round(50 + self._rng.uniform(-10, 30), 2)

            pieces.append(
                PiecePlan(
                    piece_id=f"piece-{idx+1}",
                    mass_kg=round(mass, 2),
                    center_of_mass=coordinates,
                    optimal_cut_angle=angle,
                    waste_reduction=waste_reduction,
                    reuse_score=reuse_score,
                )
            )
        return pieces

    def _generate_cutting_plan(self, pieces: List[PiecePlan], inputs: ProjectInputs) -> List[str]:
        plan = []
        for piece in pieces:
            instruction = (
                f"Use KUKA beam saw at {piece.optimal_cut_angle}° for {piece.piece_id} to "
                f"retain {piece.waste_reduction}% of volume for facade modules."
            )
            plan.append(instruction)
        if "conveyor" in inputs.transport_plan.lower():
            plan.append(
                "Sync conveyor belt speed with scan throughput (0.5 m/s) to "
                "maintain continuous material flow."
            )
        return plan

    def _estimate_reuse(self, inputs: ProjectInputs, pieces: List[PiecePlan]) -> Dict[str, float]:
        descriptive_factor = min(len(inputs.description) / 500, 1.5)
        transport_factor = 1.1 if "rail" in inputs.transport_plan.lower() else 1.0
        hazard_penalty = 0.9 if "earthquake" in inputs.hazard_profile.lower() else 1.0
        lidar_bonus = 0.05 * len(inputs.scans)

        reused_pct = max(0.0, min(95.0, 40 * descriptive_factor * transport_factor * hazard_penalty + lidar_bonus))
        new_pct = max(0.0, 100 - reused_pct)
        adaptive_roof_pct = min(30.0, new_pct * 0.3)
        reclaimed_volume = reused_pct * len(pieces) * 1.2

        return {
            "reused_pct": round(reused_pct, 2),
            "new_pct": round(new_pct, 2),
            "roof_new_pct": round(adaptive_roof_pct, 2),
            "reclaimed_volume_m3": round(reclaimed_volume, 2),
        }

    def _simulate_disasters(self, inputs: ProjectInputs) -> Dict[str, str]:
        hazard_keywords = inputs.hazard_profile.lower()
        result = {
            "seismic": "Peak drift 0.9% (within code limits)",
            "wind": "Vortex shedding mitigated with brise-soleil",
            "flood": "1.2m freeboard recommended",
        }
        if "earthquake" in hazard_keywords:
            result["seismic"] = "Base isolation recommended; predicted drift 1.7%"
        if "flood" in hazard_keywords:
            result["flood"] = "Raise plinth by 0.8m; relocate electrical rooms"
        if "hurricane" in hazard_keywords:
            result["wind"] = "Add tuned mass damper; double facade anchors"
        return result

    def _estimate_pollution(self, inputs: ProjectInputs) -> Dict[str, float]:
        traffic_factor = 1.3 if "truck" in inputs.transport_plan.lower() else 1.0
        population_density = 0.8 if "rural" in inputs.site_location.lower() else 1.1
        light_pollution = 45 * population_density
        noise_pollution = 60 * traffic_factor

        return {
            "light_db": round(light_pollution, 1),
            "noise_db": round(noise_pollution, 1),
        }

    def _run_structural_analysis(self, pieces: List[PiecePlan]) -> Dict[str, float]:
        masses = np.array([piece.mass_kg for piece in pieces])
        mean_mass = float(np.mean(masses))
        stress = 0.85 * mean_mass / max(len(pieces), 1)
        safety_factor = 1.5 * (100 / (stress + 1e-3))
        vibration = 0.25 * np.std(masses)

        return {
            "mean_piece_mass": round(mean_mass, 2),
            "global_stress_index": round(stress, 2),
            "safety_factor": round(safety_factor, 2),
            "vibration_risk": round(vibration, 2),
        }

    def _estimate_cost_and_carbon(self, inputs: ProjectInputs, reuse: Dict[str, float]) -> Dict[str, float]:
        reused_pct = reuse["reused_pct"]
        demolition_complexity = 1.2 if "selective" in inputs.demolition_notes.lower() else 1.0
        lidar_cost = 2_000 * len(inputs.scans)
        baseline_cost = 250_000 * demolition_complexity
        savings = baseline_cost * (reused_pct / 120)
        carbon_savings = reused_pct * 1.8

        return {
            "baseline_cost": round(baseline_cost + lidar_cost, 2),
            "reclaimed_savings": round(savings, 2),
            "net_cost": round(baseline_cost + lidar_cost - savings, 2),
            "co2_saved_tons": round(carbon_savings, 2),
        }

    def _generate_recommendations(self, reuse: Dict[str, float], inputs: ProjectInputs) -> List[str]:
        recs = []
        if reuse["reused_pct"] < 60:
            recs.append("Increase selective demolition to expose longer beams for reuse.")
        else:
            recs.append("Current demolition strategy already optimizes reclaimed beams.")
        if reuse["roof_new_pct"] > 10:
            recs.append("Consider modular polycarbonate roofing to reduce new material share.")
        if "lidar" not in inputs.lidar_notes.lower():
            recs.append("Add higher resolution LiDAR scans for better fitting tolerance.")
        recs.append("Run pre-demolition robotic path planning to reduce handling time.")
        return recs
