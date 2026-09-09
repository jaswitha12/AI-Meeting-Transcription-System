from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .processing import process_transcript
from .database import initialize_database, save_meeting, get_full_meeting


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="MeetIQ Meeting Intelligence API",
    description="AI-powered meeting transcription and intelligence backend",
    version="1.0.0"
)


# ============================================================
# INITIALIZE DATABASE
# ============================================================

initialize_database()


# ============================================================
# REQUEST MODEL
# ============================================================

class AnalyzeRequest(BaseModel):
    transcript: str
    filename: str = "meeting_transcript"


# ============================================================
# ROOT ENDPOINT
# ============================================================

@app.get("/")
def root():
    return {
        "message": "MeetIQ Meeting Intelligence API",
        "status": "running"
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


# ============================================================
# ANALYZE MEETING
# ============================================================

@app.post("/analyze")
def analyze_meeting(request: AnalyzeRequest):
    """
    Complete meeting processing pipeline.

    Transcript
        ↓
    OpenRouter LLM
        ↓
    Validation
        ↓
    SQLite Database
        ↓
    Structured Response
    """

    try:

        # ----------------------------------------------------
        # 1. Validate transcript
        # ----------------------------------------------------

        if not request.transcript.strip():
            raise HTTPException(
                status_code=400,
                detail="Transcript cannot be empty."
            )

        # ----------------------------------------------------
        # 2. Process transcript using LLM
        # ----------------------------------------------------

        intelligence = process_transcript(
            request.transcript
        )

        # ----------------------------------------------------
        # 3. Save complete meeting to database
        # ----------------------------------------------------

        meeting_id = save_meeting(
            intelligence=intelligence,
            transcript=request.transcript,
            filename=request.filename
        )

        # ----------------------------------------------------
        # 4. Retrieve saved meeting
        # ----------------------------------------------------

        saved_meeting = get_full_meeting(
            meeting_id
        )

        # ----------------------------------------------------
        # 5. Return API response
        # ----------------------------------------------------

        return {
            "success": True,
            "meeting_id": meeting_id,
            "data": saved_meeting
        }

    except HTTPException:
        raise

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )