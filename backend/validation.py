from .schemas import MeetingIntelligence


def validate_meeting_result(result) -> MeetingIntelligence:
    """
    Validate the structured meeting intelligence
    returned by the LLM.

    The result is converted into the
    MeetingIntelligence Pydantic model.
    """

    if result is None:
        raise ValueError("Meeting result cannot be None.")

    # If the result is already a MeetingIntelligence object
    if isinstance(result, MeetingIntelligence):
        return result

    # Validate dictionary/object against the schema
    try:
        validated_result = MeetingIntelligence.model_validate(result)

    except Exception as error:
        raise ValueError(
            "Invalid meeting intelligence structure."
        ) from error

    return validated_result