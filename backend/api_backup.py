import os
import shutil
import tempfile
from functools import lru_cache
import whisper
from fastapi import UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from .zoom_service import get_zoom_transcript, get_zoom_recordings
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from .knowledge_indexer import index_meeting_knowledge, index_all_meetings
from .rag_service import generate_grounded_answer
from .embedding_service import generate_embedding
from .vector_store import search_embeddings
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .processing import process_transcript
from .database import (
    initialize_database,
    save_meeting,
    get_full_meeting,
    get_meeting_history,
)

from .auth_service import (
    register_user,
    authenticate_user,
    create_session,
    get_user_from_token,
    delete_session,
)


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="MeetIQ Meeting Intelligence API",
    description="AI-powered meeting transcription and intelligence backend",
    version="1.0.0"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5175",
        "http://127.0.0.1:5175",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# INITIALIZE DATABASE
# ============================================================

initialize_database()


# ============================================================
# REQUEST MODELS
# ============================================================
# REQUEST MODELS

class RegisterRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str

class AnalyzeRequest(BaseModel):
    transcript: str
    filename: str = "meeting_transcript"


class RAGRequest(BaseModel):
    question: str


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5

    # Date filters
    start_date: str | None = None
    end_date: str | None = None

    # Metadata filter
    content_type: str | None = None
class ZoomTranscriptRequest(BaseModel):
    meeting_id: str   


# ============================================================
# AUTHENTICATION ENDPOINTS
# ============================================================

security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
):
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Please log in.",
        )

    user = get_user_from_token(credentials.credentials)

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired session. Please log in again.",
        )

    return user


@app.post("/auth/register")
def register(request: RegisterRequest):
    try:
        user_id = register_user(request.email, request.password)
        return {
            "message": "Registration successful. Please log in.",
            "user_id": user_id,
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/auth/login")
def login(request: LoginRequest):
    user = authenticate_user(request.email, request.password)

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password.",
        )

    token = create_session(user["id"])

    return {
        "message": "Login successful.",
        "access_token": token,
        "token_type": "bearer",
        "expires_in": 43200,
        "user": user,
    }


@app.get("/auth/me")
def current_user(user=Depends(get_current_user)):
    return {"user": user}


@app.post("/auth/logout")
def logout(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    user=Depends(get_current_user),
):
    delete_session(credentials.credentials)
    return {"message": "Logged out successfully."}



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
        # 3. Save complete meeting
        # ----------------------------------------------------

        meeting_id = save_meeting(
            intelligence=intelligence,
            transcript=request.transcript,
            filename=request.filename
        )
        saved_meeting = get_full_meeting(meeting_id)

        indexed_count = index_meeting_knowledge(saved_meeting)  

       

        # ----------------------------------------------------
        # 5. Return response
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


# ============================================================
# GET ALL MEETINGS
# ============================================================

@app.get("/meetings")
def get_meetings():
    """
    Return all previously processed meetings.
    """

    try:

        meetings = get_meeting_history()

        return {
            "success": True,
            "count": len(meetings),
            "data": meetings
        }

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=f"Could not retrieve meetings: {error}"
        )


# ============================================================
# GET MEETING BY ID
# ============================================================

@app.get("/meetings/{meeting_id}")
def get_meeting_by_id(meeting_id: int):
    """
    Return complete information for one meeting.
    """

    try:

        meeting = get_full_meeting(
            meeting_id
        )

        if not meeting:

            raise HTTPException(
                status_code=404,
                detail=f"Meeting {meeting_id} not found."
            )

        return {
            "success": True,
            "data": meeting
        }

    except HTTPException:
        raise

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=f"Could not retrieve meeting: {error}"
        )


# ============================================================
# RAG QUESTION ANSWERING
# ============================================================

@app.post("/rag-question")
def rag_question(request: RAGRequest):
    """
    Answer a question using retrieved meeting knowledge.
    """

    try:

        if not request.question.strip():

            raise HTTPException(
                status_code=400,
                detail="Question cannot be empty."
            )

        result = generate_grounded_answer(
            request.question
        )

        return {
            "success": True,
            "data": result
        }

    except HTTPException:
        raise

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


# ============================================================
# SEMANTIC / HYBRID SEARCH
# ============================================================

@app.post("/search")
def semantic_search(request: SearchRequest):
    """
    Search meeting knowledge using hybrid retrieval.

    Optional filters:

        start_date   = YYYY-MM-DD
        end_date     = YYYY-MM-DD
        content_type = metadata value
    """

    try:

        # ----------------------------------------------------
        # 1. Validate search query
        # ----------------------------------------------------

        if not request.query.strip():

            raise HTTPException(
                status_code=400,
                detail="Search query cannot be empty."
            )

        # ----------------------------------------------------
        # 2. Validate top_k
        # ----------------------------------------------------

        if request.top_k < 1:

            raise HTTPException(
                status_code=400,
                detail="top_k must be greater than 0."
            )

        # ----------------------------------------------------
        # 3. Validate start date
        # ----------------------------------------------------

        start_date = None

        if request.start_date:

            try:

                start_date = datetime.strptime(
                    request.start_date,
                    "%Y-%m-%d"
                )

            except ValueError:

                raise HTTPException(
                    status_code=400,
                    detail="start_date must use YYYY-MM-DD format."
                )

        # ----------------------------------------------------
        # 4. Validate end date
        # ----------------------------------------------------

        end_date = None

        if request.end_date:

            try:

                end_date = datetime.strptime(
                    request.end_date,
                    "%Y-%m-%d"
                )

            except ValueError:

                raise HTTPException(
                    status_code=400,
                    detail="end_date must use YYYY-MM-DD format."
                )

        # ----------------------------------------------------
        # 5. Validate date range
        # ----------------------------------------------------

        if start_date and end_date:

            if start_date > end_date:

                raise HTTPException(
                    status_code=400,
                    detail="start_date cannot be after end_date."
                )

        # ----------------------------------------------------
        # 6. Validate content type
        # ----------------------------------------------------

        if request.content_type:

            if not request.content_type.strip():

                raise HTTPException(
                    status_code=400,
                    detail="content_type cannot be empty."
                )

        # ----------------------------------------------------
        # 7. Generate query embedding
        # ----------------------------------------------------

        query_embedding = generate_embedding(
            request.query
        )

        # ----------------------------------------------------
        # 8. Search vector database
        # ----------------------------------------------------

        results = search_embeddings(
            query_embedding,
            request.query,
            request.top_k
        )

        documents = results.get(
            "documents",
            [[]]
        )[0]

        metadatas = results.get(
            "metadatas",
            [[]]
        )[0]

        distances = results.get(
            "distances",
            [[]]
        )[0]

        # ----------------------------------------------------
        # 9. Build filtered search results
        # ----------------------------------------------------

        search_results = []

        for index, document in enumerate(documents):

            # ------------------------------------------------
            # Get metadata
            # ------------------------------------------------

            metadata = {}

            if index < len(metadatas):

                metadata = metadatas[index] or {}

            # ------------------------------------------------
            # Get meeting ID
            # ------------------------------------------------

            meeting_id = metadata.get(
                "meeting_id"
            )

            # ------------------------------------------------
            # Get distance
            # ------------------------------------------------

            distance = None

            if index < len(distances):

                distance = distances[index]

            # ------------------------------------------------
            # Apply content_type metadata filter
            # ------------------------------------------------

            if request.content_type:

                result_content_type = metadata.get(
                    "content_type"
                )

                if result_content_type != request.content_type:

                    continue

            # ------------------------------------------------
            # Apply date filtering
            # ------------------------------------------------

            if start_date or end_date:

                if meeting_id is None:

                    continue

                meeting = get_full_meeting(
                    int(meeting_id)
                )

                if not meeting:

                    continue

                created_at = meeting.get(
                    "created_at"
                )

                if not created_at:

                    continue

                try:

                    meeting_date = datetime.strptime(
                        created_at[:10],
                        "%Y-%m-%d"
                    )

                except ValueError:

                    continue

                # --------------------------------------------
                # Start date filter
                # --------------------------------------------

                if (
                    start_date
                    and meeting_date < start_date
                ):

                    continue

                # --------------------------------------------
                # End date filter
                # --------------------------------------------

                if (
                    end_date
                    and meeting_date > end_date
                ):

                    continue

            # ------------------------------------------------
            # Add valid result
            # ------------------------------------------------

            search_results.append(
                {
                    "meeting_id": meeting_id,

                    "content_type": metadata.get(
                        "content_type",
                        "Unknown"
                    ),

                    "content": document,

                    "distance": distance
                }
            )

        # ----------------------------------------------------
        # 10. Return final response
        # ----------------------------------------------------

        return {
            "success": True,

            "query": request.query,

            "start_date": request.start_date,

            "end_date": request.end_date,

            "content_type": request.content_type,

            "count": len(search_results),

            "results": search_results
        }

    except HTTPException:
        raise

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )
# ============================================================
# ZOOM TRANSCRIPT
# ============================================================
@app.post("/zoom-process")
def zoom_process():
    return {
        "success": True,
        "message": "Zoom processing endpoint is ready.",
        "status": "waiting_for_recording"
    }
    try:
        recordings = get_zoom_recordings()

        return {
            "success": True,
            "recordings": recordings
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve Zoom recordings: {error}"
        )
    """
    Retrieve a transcript from Zoom using a meeting ID.
    """

    try:
        transcript = get_zoom_transcript(request.meeting_id)

        return {
            "success": True,
            "meeting_id": request.meeting_id,
            "transcript": transcript
        }

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve Zoom transcript: {error}"
        )

@app.post("/index-meetings")
def index_existing_meetings():
    try:
        result = index_all_meetings()
        return {
            "success": True,
            "message": "Meeting knowledge indexing completed.",
            "data": result
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Meeting indexing failed: {str(e)}"
        )

from functools import lru_cache
import os
import shutil
import tempfile

import whisper
from fastapi import UploadFile, File, HTTPException


@lru_cache(maxsize=1)
def load_whisper_model():
    return whisper.load_model("base")


@app.post("/transcribe")
def transcribe_upload(file: UploadFile = File(...)):
    allowed_extensions = {
        ".mp3", ".wav", ".m4a", ".aac", ".flac",
        ".mp4", ".mov", ".avi", ".mkv",
    }

    filename = os.path.basename(file.filename or "meeting.wav")
    extension = os.path.splitext(filename)[1].lower()

    if extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail="Unsupported audio/video format.",
        )

    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=extension,
        ) as temp_file:
            temp_path = temp_file.name
            shutil.copyfileobj(file.file, temp_file)

        if os.path.getsize(temp_path) > 200 * 1024 * 1024:
            raise HTTPException(
                status_code=413,
                detail="File exceeds 200 MB.",
            )

        model = load_whisper_model()
        result = model.transcribe(temp_path)
        transcript = result.get("text", "").strip()

        if not transcript:
            raise HTTPException(
                status_code=422,
                detail="No speech was detected.",
            )

        intelligence = process_transcript(transcript)

        meeting_id = save_meeting(
            intelligence=intelligence,
            transcript=transcript,
            filename=filename,
        )

        saved_meeting = get_full_meeting(meeting_id)

        return {
            "success": True,
            "meeting_id": meeting_id,
            "transcript": transcript,
            "data": saved_meeting,
        }

    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Transcription failed: {error}",
        )
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
        file.file.close()
        