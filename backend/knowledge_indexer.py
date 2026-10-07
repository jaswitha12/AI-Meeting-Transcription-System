
from .knowledge_repository import get_all_meeting_knowledge
from .embedding_service import generate_embedding
from .vector_store import add_embedding


def index_meeting_knowledge(meeting: dict) -> int:
    """
    Index a meeting's transcript and structured information
    in ChromaDB.
    """

    meeting_id = meeting.get("id")

    if meeting_id is None:
        raise ValueError("Meeting ID is required for indexing.")

    records = []

    transcript = meeting.get("transcript")
    if transcript and transcript.strip():
        records.append(("transcript", transcript))

    summary = meeting.get("summary")
    if summary and summary.strip():
        records.append(("summary", summary))

    for point in meeting.get("key_points", []):
        if point and str(point).strip():
            records.append(("key_point", str(point)))

    for decision in meeting.get("decisions", []):
        if decision and str(decision).strip():
            records.append(("decision", str(decision)))

    for action in meeting.get("action_items", []):
        if isinstance(action, dict):
            text = (
                f"Task: {action.get('task', '')}; "
                f"Assigned to: {action.get('assigned_to', '')}; "
                f"Deadline: {action.get('deadline', '')}; "
                f"Priority: {action.get('priority', '')}; "
                f"Status: {action.get('status', '')}"
            )
            if action.get("task"):
                records.append(("action_item", text))

    for participant in meeting.get("participants", []):
        if isinstance(participant, dict):
            text = (
                f"Participant: {participant.get('name', '')}; "
                f"Role: {participant.get('role', '')}; "
                f"Responsibilities: "
                f"{', '.join(participant.get('responsibilities', []))}"
            )
            if participant.get("name"):
                records.append(("participant", text))

    for index, (content_type, text) in enumerate(records):
        embedding = generate_embedding(text)

        add_embedding(
            record_id=f"meeting_{meeting_id}_{content_type}_{index}",
            text=text,
            embedding=embedding,
            meeting_id=int(meeting_id),
            content_type=content_type,
        )

    return len(records)


def index_all_meetings() -> dict:
    """Index all meetings currently stored in SQLite."""

    meetings = get_all_meeting_knowledge()
    total_records = 0

    for meeting in meetings:
        total_records += index_meeting_knowledge(meeting)

    return {
        "meetings_processed": len(meetings),
        "records_indexed": total_records,
    }