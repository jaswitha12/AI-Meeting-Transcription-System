from .llm_service import analyze_meeting
from .validation import validate_meeting_result


def process_transcript(transcript: str):
    """
    Complete meeting processing pipeline.

    Transcript
       ↓
    LLM analysis
       ↓
    Validation
       ↓
    Structured meeting result
    """

    if not transcript or not transcript.strip():
        raise ValueError("Transcript cannot be empty.")

    result = analyze_meeting(transcript)

    validated_result = validate_meeting_result(result)

    return validated_result