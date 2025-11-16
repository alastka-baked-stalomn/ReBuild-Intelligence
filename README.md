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

## Algorithm mock
The backend produces:
- Center of mass + cutting plans per piece.
- Simulated KUKA robot slicing instructions with conveyor timing hints.
- Disaster, pollution, and structural summaries driven by the provided metadata.
- Cost, carbon, and recommendations for maximising recycled share.

All calculations are deterministic, enabling consistent demos for the final presentation with styrofoam pieces, LiDAR scans, and randomly cut blocks.
