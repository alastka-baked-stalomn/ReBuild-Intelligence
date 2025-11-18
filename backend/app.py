from __future__ import annotations

import os
from pathlib import Path
from typing import List

import logging

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from fastapi.encoders import jsonable_encoder

from algorithm.processor import AlgorithmProcessor, ProjectInputs, UploadedFileMeta

logging.basicConfig(level=logging.INFO)

UPLOAD_DIR = Path(__file__).parent / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="ReBuild Intelligence API", description="Material reuse planning service")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

processor = AlgorithmProcessor()


def _save_files(files: List[UploadFile], subdir: str) -> List[UploadedFileMeta]:
    saved: List[UploadedFileMeta] = []
    target_dir = UPLOAD_DIR / subdir
    target_dir.mkdir(parents=True, exist_ok=True)

    for file in files:
        if not file:
            continue
        contents = file.file.read()
        path = target_dir / file.filename
        with open(path, "wb") as f:
            f.write(contents)
        saved.append(
            UploadedFileMeta(
                filename=file.filename,
                content_type=file.content_type or "application/octet-stream",
                size_kb=round(len(contents) / 1024, 2),
                path=str(path),
            )
        )
    return saved


@app.post("/api/process")
async def process_project(
    project_name: str = Form(...),
    description: str = Form(...),
    transport_plan: str = Form(""),
    human_built: str = Form("true"),
    site_location: str = Form(""),
    soil_profile: str = Form(""),
    hazard_profile: str = Form(""),
    demolition_notes: str = Form(""),
    lidar_notes: str = Form(""),
    asset_files: List[UploadFile] = File(default_factory=list),
    scan_files: List[UploadFile] = File(default_factory=list),
):
    asset_meta = _save_files(asset_files, "assets")
    scan_meta = _save_files(scan_files, "scans")

    inputs = ProjectInputs(
        project_name=project_name,
        description=description,
        transport_plan=transport_plan,
        human_built=human_built.lower() in {"true", "1", "yes"},
        site_location=site_location,
        soil_profile=soil_profile,
        hazard_profile=hazard_profile,
        demolition_notes=demolition_notes,
        lidar_notes=lidar_notes,
        files=asset_meta,
        scans=scan_meta,
    )

    result = processor.process(inputs)
    return JSONResponse(jsonable_encoder(result))


@app.post("/api/export/obj")
async def export_geometry() -> Response:
    if not processor.has_cached_project():
        raise HTTPException(
            status_code=400,
            detail="Run /api/process at least once before requesting an OBJ export.",
        )
    try:
        archive = processor.build_geometry_archive()
    except Exception as exc:  # pragma: no cover - runtime safeguard
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return Response(
        content=archive,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=pieces.zip"},
    )


@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok"}
