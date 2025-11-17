# ReBuild Intelligence

Prototype stack for uploading demolition intelligence, running a synthetic AI algorithm that optimizes reuse, and visualising the suggested material flow.

## Getting started

### Backend API
1. Create a virtual environment and install dependencies:
   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Start the API:
   ```bash
   uvicorn app:app --reload --port 8000
   ```
3. The main endpoints are:
   - `GET /api/health` health probe
   - `POST /api/process` form-data endpoint accepting metadata plus `asset_files` and `scan_files` uploads.

### Frontend
1. Serve the static files in `frontend/` using any HTTP server, e.g.:
   ```bash
   cd frontend
   python -m http.server 5173
   ```
2. Open http://localhost:5173 and submit the form. The UI streams files to the backend, renders analytics cards, and shows a 3D voxelised interpretation of the pieces.
3. If the frontend is served from another host (for example, a different machine or via a tunnel), update the `data-api-base` attribute on the `<body>` tag inside `frontend/index.html` so that it points to the reachable backend URL (the script falls back to `http(s)://<current-host>:8000`).

## Algorithm mock
The backend now runs a richer synthetic pipeline:
- Center of mass, waste and reuse score per salvaged piece, plus detailed KUKA cutting plans.
- Material feasibility reasoning that flags which elements can be reclaimed, which must be new (e.g. adaptive roofs), and how to tweak plans to increase recycled share.
- Natural disaster simulations paired with sound/light pollution estimates so you can judge flood, wind, noise, and glare constraints.
- Structural analytics augmented with deterministic finite element outputs (node stresses, displacement, utilisation).
- Full cost, carbon, and CO₂ savings accounting including the value of reclaimed stock.

All calculations remain deterministic which keeps demos consistent even while we fake AI-driven intelligence.
