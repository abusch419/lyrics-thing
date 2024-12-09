from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.lib.notion import (
    process_database,
    generate_lyrics,
    get_all_lyrics_with_metadata,
)

api_router = APIRouter()


class HelloWorldResponse(BaseModel):
    message: str


@api_router.get("/", response_model=HelloWorldResponse)
def get_root():
    return {"message": "Hello world!"}


@api_router.get("/analyze-lyrics")
@api_router.post("/analyze-lyrics")
def analyze_lyrics():
    try:
        result = process_database()
        return {
            "status": "success",
            "message": "Lyrics analysis complete",
            "processed": result["processed"],
            "skipped": result["skipped"],
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


class LyricsRequest(BaseModel):
    prompt: str


class LyricsResponse(BaseModel):
    lyrics: str
    explanation: str
    suggested_moods: list[str]
    suggested_themes: list[str]


@api_router.get("/songs")
def get_songs():
    """Get all songs with their metadata"""
    try:
        songs = get_all_lyrics_with_metadata()
        return {"status": "success", "songs": songs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/generate-lyrics", response_model=LyricsResponse)
def create_lyrics(request: LyricsRequest):
    """Generate new lyrics based on user prompt"""
    try:
        result = generate_lyrics(request.prompt)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
