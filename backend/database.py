import json
import sqlite3
from pathlib import Path
from datetime import datetime

from .schemas import MeetingIntelligence


# ============================================================
# DATABASE CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATABASE_PATH = BASE_DIR / "meetings.db"


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():
    """
    Create a connection to the SQLite database.
    """

    connection = sqlite3.connect(DATABASE_PATH)

    connection.row_factory = sqlite3.Row

    # Enable foreign-key support
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


# ============================================================
# INITIALIZE DATABASE
# ============================================================

def initialize_database():
    """
    Create the required database tables if they do not exist.

    Existing tables and existing data are preserved.
    """

    connection = get_connection()
    cursor = connection.cursor()

    # --------------------------------------------------------
    # MEETINGS
    # --------------------------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS meetings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename VARCHAR(255) NOT NULL,
            transcript TEXT NOT NULL,
            summary TEXT,
            key_points TEXT,
            decisions TEXT,
            action_items TEXT,
            participants TEXT,
            created_at VARCHAR(50)
        )
        """
    )

    # --------------------------------------------------------
    # PARTICIPANTS
    # --------------------------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS participants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            meeting_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            role TEXT,
            FOREIGN KEY (meeting_id)
                REFERENCES meetings(id)
                ON DELETE CASCADE
        )
        """
    )

    # --------------------------------------------------------
    # RESPONSIBILITIES
    # --------------------------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS responsibilities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            participant_id INTEGER NOT NULL,
            responsibility TEXT NOT NULL,
            FOREIGN KEY (participant_id)
                REFERENCES participants(id)
                ON DELETE CASCADE
        )
        """
    )

    # --------------------------------------------------------
    # KEY POINTS
    # --------------------------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS key_points (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            meeting_id INTEGER NOT NULL,
            point TEXT NOT NULL,
            FOREIGN KEY (meeting_id)
                REFERENCES meetings(id)
                ON DELETE CASCADE
        )
        """
    )

    # --------------------------------------------------------
    # DECISIONS
    # --------------------------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS decisions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            meeting_id INTEGER NOT NULL,
            decision TEXT NOT NULL,
            FOREIGN KEY (meeting_id)
                REFERENCES meetings(id)
                ON DELETE CASCADE
        )
        """
    )

    # --------------------------------------------------------
    # ACTION ITEMS
    # --------------------------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS action_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            meeting_id INTEGER NOT NULL,
            task TEXT NOT NULL,
            assigned_to TEXT,
            deadline TEXT,
            priority TEXT,
            status TEXT,
            FOREIGN KEY (meeting_id)
                REFERENCES meetings(id)
                ON DELETE CASCADE
        )
        """
    )

    # --------------------------------------------------------
    # DEADLINES
    # --------------------------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS deadlines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            meeting_id INTEGER NOT NULL,
            deadline TEXT NOT NULL,
            FOREIGN KEY (meeting_id)
                REFERENCES meetings(id)
                ON DELETE CASCADE
        )
        """
    )

    # --------------------------------------------------------
    # PRIORITIES
    # --------------------------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS priorities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            meeting_id INTEGER NOT NULL,
            priority TEXT NOT NULL,
            FOREIGN KEY (meeting_id)
                REFERENCES meetings(id)
                ON DELETE CASCADE
        )
        """
    )

    connection.commit()
    connection.close()


# ============================================================
# SAVE MEETING
# ============================================================

def save_meeting(
    intelligence: MeetingIntelligence,
    transcript: str = "",
    filename: str = "meeting_transcript"
) -> int:
    """
    Save complete meeting intelligence into SQLite.

    Parameters
    ----------
    intelligence:
        Validated MeetingIntelligence object.

    transcript:
        Original meeting transcript.

    filename:
        Name of the uploaded meeting file.

    Returns
    -------
    int
        ID of the newly saved meeting.
    """

    # --------------------------------------------------------
    # Validate input
    # --------------------------------------------------------

    if not isinstance(
        intelligence,
        MeetingIntelligence
    ):
        intelligence = MeetingIntelligence.model_validate(
            intelligence
        )

    if not transcript or not transcript.strip():
        raise ValueError("Transcript cannot be empty.")

    if not filename or not filename.strip():
        filename = "meeting_transcript"

    connection = get_connection()
    cursor = connection.cursor()

    try:

        # ====================================================
        # 1. SAVE MAIN MEETING
        # ====================================================

        created_at = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        cursor.execute(
            """
            INSERT INTO meetings (
                filename,
                transcript,
                summary,
                key_points,
                decisions,
                action_items,
                participants,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                filename,
                transcript,
                intelligence.summary,

                json.dumps(
                    intelligence.key_points,
                    ensure_ascii=False
                ),

                json.dumps(
                    intelligence.decisions,
                    ensure_ascii=False
                ),

                json.dumps(
                    [
                        item.model_dump()
                        for item in intelligence.action_items
                    ],
                    ensure_ascii=False
                ),

                json.dumps(
                    [
                        participant.model_dump()
                        for participant
                        in intelligence.participants
                    ],
                    ensure_ascii=False
                ),

                created_at
            )
        )

        meeting_id = cursor.lastrowid

        # ====================================================
        # 2. SAVE KEY POINTS
        # ====================================================

        for point in intelligence.key_points:

            if not point:
                continue

            cursor.execute(
                """
                INSERT INTO key_points (
                    meeting_id,
                    point
                )
                VALUES (?, ?)
                """,
                (
                    meeting_id,
                    point
                )
            )

        # ====================================================
        # 3. SAVE DECISIONS
        # ====================================================

        for decision in intelligence.decisions:

            if not decision:
                continue

            cursor.execute(
                """
                INSERT INTO decisions (
                    meeting_id,
                    decision
                )
                VALUES (?, ?)
                """,
                (
                    meeting_id,
                    decision
                )
            )

        # ====================================================
        # 4. SAVE PARTICIPANTS
        # ====================================================

        participant_ids = {}

        for participant in intelligence.participants:

            name = participant.name.strip()

            if not name:
                continue

            normalized_name = name.lower()

            # ------------------------------------------------
            # Avoid duplicate participant records
            # ------------------------------------------------

            if normalized_name in participant_ids:

                participant_id = participant_ids[
                    normalized_name
                ]

            else:

                cursor.execute(
                    """
                    SELECT id
                    FROM participants
                    WHERE meeting_id = ?
                    AND LOWER(name) = LOWER(?)
                    LIMIT 1
                    """,
                    (
                        meeting_id,
                        name
                    )
                )

                existing = cursor.fetchone()

                if existing:

                    participant_id = existing["id"]

                else:

                    cursor.execute(
                        """
                        INSERT INTO participants (
                            meeting_id,
                            name,
                            role
                        )
                        VALUES (?, ?, ?)
                        """,
                        (
                            meeting_id,
                            name,
                            participant.role
                        )
                    )

                    participant_id = cursor.lastrowid

                participant_ids[
                    normalized_name
                ] = participant_id

            # ------------------------------------------------
            # Save responsibilities
            # ------------------------------------------------

            for responsibility in participant.responsibilities:

                if not responsibility:
                    continue

                # Avoid duplicate responsibilities
                cursor.execute(
                    """
                    SELECT id
                    FROM responsibilities
                    WHERE participant_id = ?
                    AND responsibility = ?
                    LIMIT 1
                    """,
                    (
                        participant_id,
                        responsibility
                    )
                )

                existing_responsibility = cursor.fetchone()

                if not existing_responsibility:

                    cursor.execute(
                        """
                        INSERT INTO responsibilities (
                            participant_id,
                            responsibility
                        )
                        VALUES (?, ?)
                        """,
                        (
                            participant_id,
                            responsibility
                        )
                    )

        # ====================================================
        # 5. SAVE ACTION ITEMS
        # ====================================================

        for action in intelligence.action_items:

            cursor.execute(
                """
                INSERT INTO action_items (
                    meeting_id,
                    task,
                    assigned_to,
                    deadline,
                    priority,
                    status
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    meeting_id,
                    action.task,
                    action.assigned_to,
                    action.deadline,
                    action.priority,
                    action.status
                )
            )

        # ====================================================
        # 6. SAVE DEADLINES
        # ====================================================

        for deadline in intelligence.deadlines:

            if not deadline:
                continue

            cursor.execute(
                """
                INSERT INTO deadlines (
                    meeting_id,
                    deadline
                )
                VALUES (?, ?)
                """,
                (
                    meeting_id,
                    deadline
                )
            )

        # ====================================================
        # 7. SAVE PRIORITIES
        # ====================================================

        for priority in intelligence.priorities:

            if not priority:
                continue

            cursor.execute(
                """
                INSERT INTO priorities (
                    meeting_id,
                    priority
                )
                VALUES (?, ?)
                """,
                (
                    meeting_id,
                    priority
                )
            )

        # ====================================================
        # 8. COMMIT ALL DATA
        # ====================================================

        connection.commit()

        print(
            f"Meeting saved successfully. ID: {meeting_id}"
        )

        return meeting_id

    except Exception:

        # Roll back everything if any operation fails
        connection.rollback()

        raise

    finally:

        connection.close()


# ============================================================
# GET MEETING
# ============================================================

def get_meeting(meeting_id: int):
    """
    Retrieve the main meeting record.
    """

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM meetings
        WHERE id = ?
        """,
        (meeting_id,)
    )

    meeting = cursor.fetchone()

    connection.close()

    return meeting


# ============================================================
# GET FULL MEETING
# ============================================================

def get_full_meeting(meeting_id: int):
    """
    Retrieve a complete meeting including:

    - Summary
    - Transcript
    - Key points
    - Decisions
    - Action items
    - Participants
    - Responsibilities
    - Deadlines
    - Priorities
    """

    connection = get_connection()
    cursor = connection.cursor()

    # --------------------------------------------------------
    # Main meeting
    # --------------------------------------------------------

    cursor.execute(
        """
        SELECT *
        FROM meetings
        WHERE id = ?
        """,
        (meeting_id,)
    )

    meeting = cursor.fetchone()

    if not meeting:
        connection.close()
        return None

    # --------------------------------------------------------
    # Key points
    # --------------------------------------------------------

    cursor.execute(
        """
        SELECT point
        FROM key_points
        WHERE meeting_id = ?
        """,
        (meeting_id,)
    )

    key_points = [
        row["point"]
        for row in cursor.fetchall()
    ]

    # --------------------------------------------------------
    # Decisions
    # --------------------------------------------------------

    cursor.execute(
        """
        SELECT decision
        FROM decisions
        WHERE meeting_id = ?
        """,
        (meeting_id,)
    )

    decisions = [
        row["decision"]
        for row in cursor.fetchall()
    ]

    # --------------------------------------------------------
    # Action items
    # --------------------------------------------------------

    cursor.execute(
        """
        SELECT
            task,
            assigned_to,
            deadline,
            priority,
            status
        FROM action_items
        WHERE meeting_id = ?
        """,
        (meeting_id,)
    )

    action_items = [
        dict(row)
        for row in cursor.fetchall()
    ]

    # --------------------------------------------------------
    # Participants
    # --------------------------------------------------------

    cursor.execute(
        """
        SELECT
            id,
            name,
            role
        FROM participants
        WHERE meeting_id = ?
        """,
        (meeting_id,)
    )

    participant_rows = cursor.fetchall()

    participants = []

    for participant in participant_rows:

        cursor.execute(
            """
            SELECT responsibility
            FROM responsibilities
            WHERE participant_id = ?
            """,
            (participant["id"],)
        )

        responsibilities = [
            row["responsibility"]
            for row in cursor.fetchall()
        ]

        participants.append(
            {
                "name": participant["name"],
                "role": participant["role"],
                "responsibilities": responsibilities
            }
        )

    # --------------------------------------------------------
    # Deadlines
    # --------------------------------------------------------

    cursor.execute(
        """
        SELECT deadline
        FROM deadlines
        WHERE meeting_id = ?
        """,
        (meeting_id,)
    )

    deadlines = [
        row["deadline"]
        for row in cursor.fetchall()
    ]

    # --------------------------------------------------------
    # Priorities
    # --------------------------------------------------------

    cursor.execute(
        """
        SELECT priority
        FROM priorities
        WHERE meeting_id = ?
        """,
        (meeting_id,)
    )

    priorities = [
        row["priority"]
        for row in cursor.fetchall()
    ]

    connection.close()

    # --------------------------------------------------------
    # Return complete structured meeting
    # --------------------------------------------------------

    return {
        "id": meeting["id"],
        "filename": meeting["filename"],
        "transcript": meeting["transcript"],
        "summary": meeting["summary"],
        "key_points": key_points,
        "decisions": decisions,
        "action_items": action_items,
        "participants": participants,
        "deadlines": deadlines,
        "priorities": priorities,
        "created_at": meeting["created_at"]
    }


# ============================================================
# GET MEETING HISTORY
# ============================================================

def get_meeting_history():
    """
    Return all saved meetings for the Meeting History page.
    """

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            filename,
            summary,
            created_at
        FROM meetings
        ORDER BY id DESC
        """
    )

    meetings = [
        dict(row)
        for row in cursor.fetchall()
    ]

    connection.close()

    return meetings