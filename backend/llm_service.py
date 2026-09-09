import os
import json
import time
import requests

from dotenv import load_dotenv
from pydantic import ValidationError

from .schemas import MeetingIntelligence
from .prompts import MEETING_ANALYSIS_PROMPT


# ============================================================
# ENVIRONMENT CONFIGURATION
# ============================================================

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

MODEL_NAME = "qwen/qwen-2.5-7b-instruct"

REQUEST_TIMEOUT = 120
MAX_RETRIES = 3
TEMPERATURE = 0.2


# ============================================================
# CLEAN JSON RESPONSE
# ============================================================

def clean_json_response(content: str) -> str:
    """
    Clean Markdown code fences and whitespace
    from the LLM response.
    """

    if not content:
        raise ValueError(
            "LLM returned an empty response."
        )

    content = content.strip()

    if content.startswith("```json"):
        content = content[7:]

    elif content.startswith("```"):
        content = content[3:]

    if content.endswith("```"):
        content = content[:-3]

    return content.strip()


# ============================================================
# NORMALIZE LLM RESULT
# ============================================================

def normalize_llm_result(result: dict) -> dict:
    """
    Normalize common LLM formatting variations before
    Pydantic validation.

    This function does not invent meeting information.
    It only converts safe structural variations.
    """

    if not isinstance(result, dict):
        raise ValueError(
            "LLM response must be a JSON object."
        )

    # --------------------------------------------------------
    # Ensure top-level list fields exist
    # --------------------------------------------------------

    list_fields = [
        "key_points",
        "decisions",
        "participants",
        "action_items",
        "deadlines",
        "priorities",
    ]

    for field in list_fields:

        if field not in result or result[field] is None:

            result[field] = []

        elif not isinstance(result[field], list):

            if isinstance(result[field], str):

                result[field] = [
                    result[field]
                ]

            else:

                result[field] = []


    # ========================================================
    # PARTICIPANTS
    # ========================================================

    normalized_participants = []

    for participant in result["participants"]:

        if not isinstance(participant, dict):
            continue

        name = participant.get("name")

        if not name:
            continue

        name = str(name).strip()

        role = participant.get("role")

        if role is not None:
            role = str(role).strip()

        responsibilities = participant.get(
            "responsibilities",
            []
        )

        if responsibilities is None:

            responsibilities = []

        elif isinstance(responsibilities, str):

            responsibilities = [
                responsibilities
            ]

        elif not isinstance(
            responsibilities,
            list
        ):

            responsibilities = []


        clean_responsibilities = []

        for responsibility in responsibilities:

            if responsibility is None:
                continue

            responsibility = str(
                responsibility
            ).strip()

            if responsibility:
                clean_responsibilities.append(
                    responsibility
                )


        normalized_participants.append(
            {
                "name": name,
                "role": role,
                "responsibilities": clean_responsibilities,
            }
        )


    # --------------------------------------------------------
    # Remove duplicate participants
    # --------------------------------------------------------

    unique_participants = []

    seen_names = set()

    for participant in normalized_participants:

        name_key = participant["name"].lower()

        if name_key in seen_names:
            continue

        seen_names.add(name_key)

        unique_participants.append(
            participant
        )

    result["participants"] = unique_participants


    # ========================================================
    # ACTION ITEMS
    # ========================================================

    normalized_action_items = []

    for action in result["action_items"]:

        if not isinstance(action, dict):
            continue

        task = action.get("task")

        if not task:
            continue

        task = str(task).strip()


        # ----------------------------------------------------
        # Assigned participant
        # ----------------------------------------------------

        assigned_to = action.get(
            "assigned_to"
        )

        if isinstance(
            assigned_to,
            list
        ):

            if assigned_to:

                assigned_to = str(
                    assigned_to[0]
                ).strip()

            else:

                assigned_to = None

        elif assigned_to is not None:

            assigned_to = str(
                assigned_to
            ).strip()


        # ----------------------------------------------------
        # Deadline
        # ----------------------------------------------------

        deadline = action.get(
            "deadline"
        )

        if isinstance(
            deadline,
            list
        ):

            if deadline:

                deadline = str(
                    deadline[0]
                ).strip()

            else:

                deadline = None

        elif deadline is not None:

            deadline = str(
                deadline
            ).strip()


        # ----------------------------------------------------
        # Priority
        # ----------------------------------------------------

        priority = action.get(
            "priority"
        )

        if isinstance(
            priority,
            list
        ):

            if priority:

                priority = str(
                    priority[0]
                ).strip()

            else:

                priority = None

        elif priority is not None:

            priority = str(
                priority
            ).strip()


        # ----------------------------------------------------
        # Status
        # ----------------------------------------------------

        status = action.get(
            "status"
        )

        if isinstance(
            status,
            list
        ):

            if status:

                status = str(
                    status[0]
                ).strip()

            else:

                status = "Pending"

        elif status is None:

            status = "Pending"

        else:

            status = str(
                status
            ).strip()

            if not status:
                status = "Pending"


        normalized_action_items.append(
            {
                "task": task,
                "assigned_to": (
                    assigned_to
                    if assigned_to
                    else None
                ),
                "deadline": (
                    deadline
                    if deadline
                    else None
                ),
                "priority": (
                    priority
                    if priority
                    else None
                ),
                "status": status,
            }
        )


    result["action_items"] = (
        normalized_action_items
    )


    # ========================================================
    # STRING LIST FIELDS
    # ========================================================

    string_list_fields = [
        "key_points",
        "decisions",
        "deadlines",
        "priorities",
    ]

    for field in string_list_fields:

        cleaned_items = []

        for item in result[field]:

            if item is None:
                continue

            item = str(item).strip()

            if item:

                cleaned_items.append(
                    item
                )

        result[field] = cleaned_items


    # ========================================================
    # SUMMARY
    # ========================================================

    summary = result.get(
        "summary",
        ""
    )

    if summary is None:

        summary = ""

    elif not isinstance(
        summary,
        str
    ):

        summary = str(summary)


    result["summary"] = summary.strip()


    return result


# ============================================================
# ANALYZE MEETING
# ============================================================

def analyze_meeting(
    transcript: str
) -> MeetingIntelligence:

    # ========================================================
    # CHECK API KEY
    # ========================================================

    if not OPENROUTER_API_KEY:

        raise ValueError(
            "OPENROUTER_API_KEY is not configured. "
            "Please check your .env file."
        )


    # ========================================================
    # CHECK TRANSCRIPT
    # ========================================================

    if not transcript or not transcript.strip():

        raise ValueError(
            "Transcript cannot be empty."
        )


    # ========================================================
    # CREATE PROMPT
    # ========================================================

    prompt = MEETING_ANALYSIS_PROMPT.replace(
        "{transcript}",
        transcript
    )


    # ========================================================
    # REQUEST HEADERS
    # ========================================================

    headers = {
        "Authorization": (
            f"Bearer {OPENROUTER_API_KEY}"
        ),
        "Content-Type": "application/json",
    }


    # ========================================================
    # REQUEST PAYLOAD
    # ========================================================

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "user",
                "content": prompt,
            }
        ],
        "temperature": TEMPERATURE,
        "max_tokens": 4000,
    }


    # ========================================================
    # SEND REQUEST
    # ========================================================

    response = None

    for attempt in range(
        1,
        MAX_RETRIES + 1
    ):

        try:

            print(
                f"Sending request to OpenRouter "
                f"(attempt {attempt}/{MAX_RETRIES})..."
            )


            response = requests.post(
                OPENROUTER_URL,
                headers=headers,
                json=payload,
                timeout=REQUEST_TIMEOUT,
            )


            # ------------------------------------------------
            # SUCCESSFUL HTTP RESPONSE
            # ------------------------------------------------

            if response.ok:

                break


            # ------------------------------------------------
            # HTTP ERROR
            # ------------------------------------------------

            print(
                f"OpenRouter returned HTTP "
                f"{response.status_code}"
            )

            print(
                "OpenRouter error:",
                response.text
            )


            # ------------------------------------------------
            # RETRY TEMPORARY ERRORS
            # ------------------------------------------------

            if response.status_code in [
                408,
                429,
                500,
                502,
                503,
                504,
            ]:

                if attempt < MAX_RETRIES:

                    wait_time = 2 ** attempt

                    print(
                        f"Retrying in "
                        f"{wait_time} seconds..."
                    )

                    time.sleep(
                        wait_time
                    )

                    continue


            response.raise_for_status()


        except requests.exceptions.Timeout:

            print(
                "OpenRouter request timed out."
            )

            if attempt < MAX_RETRIES:

                wait_time = 2 ** attempt

                print(
                    f"Retrying in "
                    f"{wait_time} seconds..."
                )

                time.sleep(
                    wait_time
                )

                continue

            raise


        except requests.exceptions.RequestException as error:

            print(
                "OpenRouter request failed:",
                str(error)
            )

            if attempt < MAX_RETRIES:

                wait_time = 2 ** attempt

                print(
                    f"Retrying in "
                    f"{wait_time} seconds..."
                )

                time.sleep(
                    wait_time
                )

                continue

            raise


    # ========================================================
    # CHECK RESPONSE
    # ========================================================

    if response is None:

        raise RuntimeError(
            "No response received from OpenRouter."
        )


    # ========================================================
    # PARSE OPENROUTER RESPONSE
    # ========================================================

    try:

        data = response.json()

    except ValueError as error:

        raise ValueError(
            "OpenRouter returned an invalid "
            "JSON response."
        ) from error


    # ========================================================
    # EXTRACT LLM CONTENT
    # ========================================================

    try:

        content = data["choices"][0]["message"]["content"]

    except (
        KeyError,
        IndexError,
        TypeError
    ) as error:

        print(
            "\n========== "
            "UNEXPECTED OPENROUTER RESPONSE "
            "=========="
        )

        print(
            json.dumps(
                data,
                indent=2,
                ensure_ascii=False
            )
        )

        print(
            "========================================"
        )

        raise ValueError(
            "Unexpected OpenRouter response structure."
        ) from error


    # ========================================================
    # CLEAN LLM CONTENT
    # ========================================================

    content = clean_json_response(
        content
    )


    # ========================================================
    # CONVERT STRING TO JSON
    # ========================================================

    try:

        result = json.loads(
            content
        )

    except json.JSONDecodeError as error:

        print(
            "\n========== INVALID LLM JSON =========="
        )

        print(
            content
        )

        print(
            "======================================"
        )

        raise ValueError(
            "LLM returned invalid JSON."
        ) from error


    # ========================================================
    # NORMALIZE LLM RESULT
    # ========================================================

    try:

        result = normalize_llm_result(
            result
        )

    except Exception as error:

        print(
            "\n========== NORMALIZATION ERROR =========="
        )

        print(
            str(error)
        )

        print(
            "\nRaw result:"
        )

        print(
            json.dumps(
                result,
                indent=2,
                ensure_ascii=False
            )
        )

        print(
            "========================================="
        )

        raise ValueError(
            "Unable to normalize LLM response."
        ) from error


    # ========================================================
    # PYDANTIC VALIDATION
    # ========================================================

    try:

        validated_result = (
            MeetingIntelligence.model_validate(
                result
            )
        )

    except ValidationError as error:

        print(
            "\n========== INVALID STRUCTURE =========="
        )

        print(
            json.dumps(
                result,
                indent=2,
                ensure_ascii=False
            )
        )

        print(
            "\n========== VALIDATION ERROR =========="
        )

        print(
            error
        )

        print(
            "======================================"
        )

        raise ValueError(
            "LLM response does not match "
            "the MeetingIntelligence schema."
        ) from error


    # ========================================================
    # SUCCESS
    # ========================================================

    print(
        "LLM response validated successfully."
    )

    return validated_result