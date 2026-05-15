"""
run_server.py — Entry point for the Arise IVA Speech-to-ISL backend.

Usage:
    python run_server.py

Server starts at:
    http://localhost:8000

API docs available at:
    http://localhost:8000/docs      (Swagger UI)
    http://localhost:8000/redoc     (ReDoc)
"""

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,          # auto-reload on file changes during development
        log_level="info",
    )