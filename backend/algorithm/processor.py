from __future__ import annotations

import json
import math
import os
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import numpy as np
from openai import OpenAI


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
class MaterialFeasibility:
    reusable_components: List[str]
    needs_new_components: List[str]
    suggested_plan_changes: List[str]
    recycled_ratio: float
    roof_new_pct: float


@dataclass
class AlgorithmResult:
    project_name: str
    summary: str
    piece_plans: List[PiecePlan]
    cutting_instructions: List[str]
    reuse_breakdown: Dict[str, float]
    disaster_simulation: Dict[str, str]
    pollution_model: Dict[str, float]
    environmental_impact: Dict[str, float]
    structural_analysis: Dict[str, float]
    finite_element_analysis: Dict[str, float]
    cost_and_carbon: Dict[str, float]
    recommendations: List[str]
    material_feasibility: MaterialFeasibility
    ai_engineering: str


class AlgorithmProcessor:
    """High level processor that mocks the behaviour of the future AI pipeline."""

    def __init__(self) -> None:
        # Seed a deterministic generator so that previews are reproducible for demo purposes.
        self._rng = random.Random(42)
        api_key = os.getenv("OPENAI_API_KEY")
        self._client: Optional[OpenAI] = OpenAI(api_key=api_key) if api_key else None
        self._model = os.environ.get("OPENAI_MODEL", "gpt-4.1-mini")

    def process(self, inputs: ProjectInputs) -> AlgorithmResult:
        pieces = self._generate_piece_plans(inputs)
        cutting_instructions = self._generate_cutting_plan(pieces, inputs)
        reuse_breakdown = self._estimate_reuse(inputs, pieces)
        disaster_simulation = self._simulate_disasters(inputs)
        pollution_model = self._estimate_pollution(inputs)
        environmental_impact = self._run_environmental_models(inputs, pollution_model)
        structural_analysis = self._run_structural_analysis(pieces)
        finite_element_analysis = self._run_finite_element_analysis(pieces, structural_analysis)
        cost_and_carbon = self._estimate_cost_and_carbon(inputs, reuse_breakdown)
        recommendations = self._generate_recommendations(reuse_breakdown, inputs)
        material_feasibility = self._assess_material_feasibility(reuse_breakdown, inputs, pieces)
        ai_engineering = self._run_llm_engineering(
            inputs,
            pieces,
            reuse_breakdown,
            structural_analysis,
            disaster_simulation,
            environmental_impact,
            cost_and_carbon,
        )

        summary = (
            f"Processed {inputs.project_name} with {len(inputs.files)} uploaded assets. "
            f"Estimated that {reuse_breakdown['reused_pct']:.1f}% of the structure can be reclaimed "
            "while KUKA cutting plans cover every salvaged piece."
        )

        return AlgorithmResult(
            project_name=inputs.project_name,
            summary=summary,
            piece_plans=pieces,
            cutting_instructions=cutting_instructions,
            reuse_breakdown=reuse_breakdown,
            disaster_simulation=disaster_simulation,
            pollution_model=pollution_model,
            environmental_impact=environmental_impact,
            structural_analysis=structural_analysis,
            finite_element_analysis=finite_element_analysis,
            cost_and_carbon=cost_and_carbon,
            recommendations=recommendations,
            material_feasibility=material_feasibility,
            ai_engineering=ai_engineering,
        )

    def _run_llm_engineering(
        self,
        inputs: ProjectInputs,
        pieces: List[PiecePlan],
        reuse: Dict[str, float],
        structural: Dict[str, float],
        disasters: Dict[str, str],
        environmental: Dict[str, float],
        cost: Dict[str, float],
    ) -> str:
        """Invoke OpenAI to synthesize realistic engineering reasoning."""

        if not self._client:
            return (
                "AI engineering reasoning unavailable. Set OPENAI_API_KEY "
                "to enable OpenAI-assisted commentary."
            )

        def _file_summary(items: List[UploadedFileMeta]) -> Dict[str, object]:
            return {
                "count": len(items),
                "total_kb": round(sum(f.size_kb for f in items), 2),
                "types": sorted({f.content_type for f in items}),
                "filenames": [f.filename for f in items[:6]],
            }

        payload = {
            "metadata": {
                "project_name": inputs.project_name,
                "description": inputs.description,
                "transport_plan": inputs.transport_plan,
                "site_location": inputs.site_location,
                "soil_profile": inputs.soil_profile,
                "hazard_profile": inputs.hazard_profile,
                "demolition_notes": inputs.demolition_notes,
            },
            "asset_files": _file_summary(inputs.files),
            "scan_files": _file_summary(inputs.scans),
            "piece_plans": [
                {
                    "id": piece.piece_id,
                    "mass_kg": piece.mass_kg,
                    "center_of_mass": piece.center_of_mass,
                    "reuse_score": piece.reuse_score,
                    "optimal_cut_angle": piece.optimal_cut_angle,
                    "waste_reduction": piece.waste_reduction,
                }
                for piece in pieces
            ],
            "reuse_breakdown": reuse,
            "structural_analysis": structural,
            "disaster_simulation": disasters,
            "environmental_impact": environmental,
            "cost_and_carbon": cost,
        }

        context = json.dumps(payload, indent=2)
        system_prompt = (
            "You are ReBuild Intelligence, an adaptive reuse structural engineer. "
            "Provide rigorous, practical guidance for cutting, reusing, and reinforcing salvaged materials."
        )
        user_prompt = (
            "Using the following project context, produce an engineering brief that includes: "
            "(1) overall feasibility and critical warnings, (2) how to improve reuse ratios, "
            "(3) KUKA cutting/handling strategies, (4) what must be newly fabricated versus reusable, "
            "(5) hazard-specific mitigation aligned to the disaster data, and (6) critique of cost and CO2 numbers.\n"
            "Reference actual values from the context without inventing new numbers.\n"
            f"Context:\n{context}"
        )

        try:
            response = self._client.responses.create(
                model=self._model,
                input=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            text_chunks: List[str] = []
            for item in getattr(response, "output", []) or []:
                if getattr(item, "type", "") in {"output_text", "text"}:
                    text_chunks.append(getattr(item, "text", ""))
                elif getattr(item, "type", "") == "message":
                    for content in getattr(item, "content", []) or []:
                        if getattr(content, "type", "") == "text":
                            text_chunks.append(getattr(content, "text", ""))
            for choice in getattr(response, "choices", []) or []:
                message = getattr(choice, "message", None)
                if message and isinstance(getattr(message, "content", None), str):
                    text_chunks.append(message.content)
            final_text = "\n".join(chunk.strip() for chunk in text_chunks if chunk)
            if final_text:
                return final_text
        except Exception as exc:  # pragma: no cover - network failure fallback
            return (
                "AI engineering reasoning unavailable: "
                "set OPENAI_API_KEY and OPENAI_MODEL to enable live synthesis. "
                f"Details: {exc}"
            )

        return "AI engineering reasoning unavailable: empty response from model."

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

    def _run_environmental_models(
        self, inputs: ProjectInputs, pollution: Dict[str, float]
    ) -> Dict[str, float]:
        """Layer additional sound/light simulations on top of the coarse pollution model."""

        hazard = inputs.hazard_profile.lower()
        disaster_multiplier = 1.2 if "flood" in hazard else 1.0
        cultural_buffer = 0.9 if "historic" in inputs.description.lower() else 1.0
        sound_peak = pollution["noise_db"] * disaster_multiplier
        light_lux = 320 * cultural_buffer + 15 * len(inputs.files)

        return {
            **pollution,
            "sound_peak_db": round(sound_peak, 1),
            "light_intrusion_lux": round(light_lux, 1),
            "nighttime_glare_index": round(light_lux / 12, 2),
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

    def _run_finite_element_analysis(
        self, pieces: List[PiecePlan], structural: Dict[str, float]
    ) -> Dict[str, float]:
        node_count = max(len(pieces) * 8, 16)
        # synthetic nodal stress distribution
        load_vector = np.linspace(0.7, 1.3, node_count)
        random_offsets = np.array([self._rng.uniform(-0.08, 0.08) for _ in range(node_count)])
        stress_map = load_vector + random_offsets
        critical_idx = int(np.argmax(stress_map))
        max_displacement = float(np.max(stress_map) * 12)
        utilization = structural["global_stress_index"] / (structural["safety_factor"] + 1e-3)

        return {
            "node_count": node_count,
            "critical_node": f"node-{critical_idx + 1}",
            "max_displacement_mm": round(max_displacement, 2),
            "stress_utilization_pct": round(utilization * 100, 1),
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
            "recycled_material_value": round(reused_pct * 950, 2),
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

    def _assess_material_feasibility(
        self, reuse: Dict[str, float], inputs: ProjectInputs, pieces: List[PiecePlan]
    ) -> MaterialFeasibility:
        reusable_components = ["façade panels", "floor slabs", "timber joists"]
        needs_new_components = ["roof membranes"]

        if "brick" in inputs.demolition_notes.lower():
            reusable_components.append("salvaged brick cladding")
        if reuse["reused_pct"] < 50:
            needs_new_components.append("primary core shear walls")
        if len(inputs.scans) > 0:
            reusable_components.append("precision steel nodes")

        suggested_changes = [
            "Retune KUKA cut angles for thicker slabs if more recycled share is needed.",
            "Swap to laminated skylights to keep the adaptive roof lightweight.",
        ]
        if reuse["reused_pct"] < 70:
            suggested_changes.append("Relocate conveyor buffer closer to demolition face to limit waste.")
        if "flood" in inputs.hazard_profile.lower():
            suggested_changes.append("Raise reused modules by 0.6m to clear flood design level.")

        recycled_ratio = reuse["reused_pct"] / 100
        return MaterialFeasibility(
            reusable_components=reusable_components,
            needs_new_components=needs_new_components,
            suggested_plan_changes=suggested_changes,
            recycled_ratio=round(recycled_ratio, 2),
            roof_new_pct=reuse["roof_new_pct"],
        )
