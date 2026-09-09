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