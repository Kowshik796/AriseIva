import os
import sys
from pathlib import Path

# Add backend folders to python path so their internal imports work
sys.path.insert(0, str(Path(__file__).parent / "backend" / "speechtosign"))
sys.path.insert(0, str(Path(__file__).parent / "backend" / "signtospeech"))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from a2wsgi import WSGIMiddleware

# Import the FastAPI app
from backend.speechtosign.app.main import app as isl_app

# Import the Flask app
from backend.signtospeech.app.main import app as gesture_app

# Create the main wrapper app
app = FastAPI(title="Arise IVA Unified System")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the ISL backend at /api/isl
app.mount("/api/isl", isl_app)

# Mount the Gesture Flask backend at /api/gesture
app.mount("/api/gesture", WSGIMiddleware(gesture_app))

# Mount the frontend static files
frontend_dist = Path(__file__).parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")
else:
    @app.get("/")
    def root():
        return {"message": "Frontend not built yet. Run 'npm run build' in frontend folder."}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
