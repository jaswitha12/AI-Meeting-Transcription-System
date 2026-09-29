from .database import get_meeting_history, get_full_meeting


def get_all_meeting_knowledge():
    """
    Retrieve all historical meetings and their complete information.
    """

    meetings = get_meeting_history()
    knowledge_records = []

    for meeting in meetings:
        meeting_id = meeting["id"]

        full_meeting = get_full_meeting(meeting_id)

        if full_meeting:
            knowledge_records.append(full_meeting)

    return knowledge_records