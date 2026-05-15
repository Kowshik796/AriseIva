"""
main.py — Arise IVA | Speech → ISL Gloss FastAPI server.

Full pipeline per request:
  POST /process
    → validate input        (schemas.py)
    → normalize text        (normalizer.py)
    → build ISL gloss       (gloss_engine.py)
    → map gloss to videos   (video_mapper.py)
    → log request/response  (logger.py)
    → return JSON response
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from .schemas       import TranslateRequest, TranslateResponse
from .normalizer    import normalize
from .gloss_engine  import build_gloss
from .video_mapper  import map_gloss_to_videos, get_video_path
from .logger        import log_request, log_response, log_error

# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Arise IVA — Speech to ISL API",
    version="2.0.0",
    description=(
        "Converts English sentences into Indian Sign Language gloss sequences "
        "and returns matched .mp4 video paths for the React frontend player."
    ),
)

# ── CORS — allow React frontend on port 5173 ──────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Exception handlers ────────────────────────────────────────────────────────

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors  = exc.errors()
    message = errors[0]["msg"] if errors else "Validation error"
    return JSONResponse(status_code=422, content={"error": message})


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    log_error(str(exc))
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error"},
    )

# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {"status": "ok", "service": "Arise IVA Speech-to-ISL API v2"}


@app.get("/health")
async def health():
    """Health check polled by the React StatusIndicators component."""
    return {"backend": "ok", "model": "loaded"}


@app.post("/process", response_model=TranslateResponse)
async def process(payload: TranslateRequest):
    """
    Convert an English sentence to an ISL gloss sequence + video paths.

    Example:
      Input:  { "text": "I go to school tomorrow" }
      Output: {
        "gloss":       ["TOMORROW", "ME", "GO", "SCHOOL"],
        "video_paths": ["/signs/TOMORROW.mp4", "/signs/ME.mp4",
                        "/signs/GO.mp4",       "/signs/SCHOOL.mp4"],
        "word_count":  4,
        "gloss_count": 4,
        "video_count": 4,
        "skipped":     []
      }
    """
    raw_text = payload.text.strip()
    log_request(raw_text)

    # Step 1 — Normalize: lowercase, strip punctuation, remove fillers, stem
    tokens = normalize(raw_text)

    # Step 2 — Build ISL gloss: reorder grammar + map via dictionary
    gloss = build_gloss(tokens)

    # Step 3 — Map each gloss token to its frontend video path
    video_paths = map_gloss_to_videos(gloss)

    # Track which gloss tokens had no video (for frontend fallback display)
    skipped = [g for g in gloss if get_video_path(g) is None]

    log_response(gloss)

    return TranslateResponse(
        gloss=gloss,
        video_paths=video_paths,
        word_count=len(tokens),
        gloss_count=len(gloss),
        video_count=len(video_paths),
        skipped=skipped,
    )