# MeetIQ – AI Meeting Transcription and Intelligence System

MeetIQ is an AI-powered meeting transcription and intelligence system that converts audio/video meeting recordings into text and extracts actionable meeting information using Artificial Intelligence.

## Project Overview

The system combines speech recognition, Large Language Models, structured data validation, database persistence, and a Streamlit web interface.

The main objective is to transform an unstructured meeting conversation into structured and useful information such as:

- Meeting summary
- Key discussion points
- Decisions
- Action items
- Participants
- Responsibilities
- Deadlines
- Priorities

---

## Milestone 1

Milestone 1 focused on the basic meeting transcription pipeline.

### Features

- Audio/video file upload
- Speech-to-text transcription using Whisper
- FFmpeg-based audio processing
- Support for common audio/video formats
- Transcript generation
- Basic transcription accuracy testing
- Local summarization

---

## Milestone 2

Milestone 2 extends the system from simple transcription to meeting intelligence.

### Features

- OpenRouter LLM integration
- Prompt engineering for meeting analysis
- Structured JSON output
- Pydantic-based output validation
- Meeting summarization
- Key point extraction
- Action item extraction
- Participant identification
- Responsibility mapping
- Deadline extraction
- Priority extraction
- Action item status tracking
- SQLite database persistence
- Meeting history
- Original transcript viewing
- End-to-end backend integration
- WER and CER based transcription accuracy testing

---

## System Pipeline

```text
Meeting Audio / Video
        |
        v
Whisper Speech Recognition
        |
        v
Generated Transcript
        |
        v
OpenRouter + LLM
        |
        v
Structured JSON Output
        |
        v
Pydantic Validation
        |
        v
SQLite Database
        |
        v
Streamlit Web Interface
        |
        v
Meeting Intelligence

---

## Milestone 3 – Meeting Knowledge & RAG

Milestone 3 extends MeetIQ with a knowledge retrieval system that allows
users to ask questions about previously processed meetings using semantic
search and Retrieval-Augmented Generation (RAG).

### Features

- Meeting knowledge repository
- Text embedding generation
- Vector database integration
- Semantic similarity search
- Retrieval-Augmented Generation (RAG)
- Grounded question answering
- Meeting source identification
- FastAPI RAG endpoint
- Streamlit Knowledge Search interface
- Context-based answer generation
- Protection against unsupported information

### Milestone 3 Pipeline

Previously Processed Meetings
        |
        v
Knowledge Repository
        |
        v
Text Embedding
        |
        v
Vector Database
        |
        v
Semantic Search
        |
        v
Relevant Meeting Context
        |
        v
LLM
        |
        v
Grounded Answer + Sources

### Knowledge Search

Users can enter natural-language questions about previously processed
meetings through the Knowledge Search interface.

The system:

1. Converts the question into an embedding.
2. Searches the vector database for relevant meeting information.
3. Retrieves the most relevant meeting context.
4. Sends the retrieved context to the LLM.
5. Generates a grounded answer using only the retrieved information.
6. Displays the answer along with the relevant meeting sources.

### Example

Question:

"Which meeting discussed database migration?"

Result:

"Meeting ID: 1 discussed database migration."

The system also displays the meeting ID and retrieved information as the
source of the answer.

### RAG API

The system provides a FastAPI endpoint:

`POST /rag-question`

Example request:

```json
{
  "question": "Which meeting discussed database migration?"
}