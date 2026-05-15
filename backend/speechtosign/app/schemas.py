"""
schemas.py — Pydantic models for request / response validation.
"""

from pydantic import BaseModel, field_validator


class TranslateRequest(BaseModel):
    text: str

    @field_validator("text")
    @classmethod
    def validate_text(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Input text must not be empty or whitespace.")
        if len(v) > 1000:
            raise ValueError("Input text must not exceed 1000 characters.")
        return v


class TranslateResponse(BaseModel):
    gloss:        list[str]   # ISL gloss tokens  e.g. ["TOMORROW","ME","GO","SCHOOL"]
    video_paths:  list[str]   # frontend video paths e.g. ["/signs/TOMORROW.mp4", ...]
    word_count:   int         # number of normalized input tokens
    gloss_count:  int         # number of gloss tokens produced
    video_count:  int         # number of matched video files
    skipped:      list[str]   # gloss tokens with no video (for debugging)