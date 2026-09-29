import json

from backend.database import get_meeting_history, get_full_meeting
from backend.embedding_service import generate_embedding
from backend.vector_store import add_embedding


def build_meeting_text(meeting):
    """Combine important meeting information into searchable text."""

    parts = []

    if meeting.get("filename"):
        parts.append(f"Filename: {meeting['filename']}")

    if meeting.get("transcript"):
        parts.append(f"Transcript: {meeting['transcript']}")

    if meeting.get("summary"):
        parts.append(f"Summary: {meeting['summary']}")

    if meeting.get("key_points"):
        parts.append(
            f"Key Points: {json.dumps(meeting['key_points'], ensure_ascii=False)}"
        )

    if meeting.get("decisions"):
        parts.append(
            f"Decisions: {json.dumps(meeting['decisions'], ensure_ascii=False)}"
        )

    if meeting.get("action_items"):
        parts.append(
            f"Action Items: {json.dumps(meeting['action_items'], ensure_ascii=False)}"
        )

    if meeting.get("participants"):
        parts.append(
            f"Participants: {json.dumps(meeting['participants'], ensure_ascii=False)}"
        )

    if meeting.get("deadlines"):
        parts.append(
            f"Deadlines: {json.dumps(meeting['deadlines'], ensure_ascii=False)}"
        )

    return "\n".join(parts)


def main():
    meetings = get_meeting_history()

    print(f"Found {len(meetings)} meetings.")

    indexed = 0

    for meeting in meetings:
        meeting_id = meeting["id"]
        full_meeting = get_full_meeting(meeting_id)

        if not full_meeting:
            print(f"Skipping Meeting {meeting_id}: no data found.")
            continue

        text = build_meeting_text(full_meeting)

        if not text.strip():
            print(f"Skipping Meeting {meeting_id}: no searchable content.")
            continue

        print(f"Indexing Meeting {meeting_id}...")

        embedding = generate_embedding(text)

        add_embedding(
            record_id=f"meeting-{meeting_id}-knowledge",
            text=text,
            embedding=embedding,
            meeting_id=meeting_id,
            content_type="meeting_knowledge"
        )

        indexed += 1

    print()
    print(f"Successfully indexed {indexed} meetings.")


if __name__ == "__main__":
    main()