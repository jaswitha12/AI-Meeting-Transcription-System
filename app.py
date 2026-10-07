import os
import requests
import streamlit as st
from sympy import python
import whisper
from backend.database import (
    get_meeting_history,
    get_full_meeting,
    save_meeting
)
from backend.processing import process_transcript
from backend.llm_service import analyze_meeting

# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="MeetIQ | Meeting Intelligence",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# CONFIGURATION
# ============================================================

BACKEND_URL = "http://127.0.0.1:8000"

UPLOAD_FOLDER = "uploads"
TRANSCRIPT_FOLDER = "transcripts"
SUMMARY_FOLDER = "summaries"

SUPPORTED_FILES = [
    "mp3", "wav", "m4a", "aac", "flac",
    "mp4", "mov", "avi", "mkv"
]

MAX_FILE_SIZE_MB = 200

for folder in [
    UPLOAD_FOLDER,
    TRANSCRIPT_FOLDER,
    SUMMARY_FOLDER
]:
    os.makedirs(folder, exist_ok=True)


# ============================================================
# SESSION STATE
# ============================================================

if "transcript" not in st.session_state:
    st.session_state["transcript"] = ""

if "transcript_filename" not in st.session_state:
    st.session_state["transcript_filename"] = ""

if "meeting_data" not in st.session_state:
    st.session_state["meeting_data"] = {}

if "meeting_id" not in st.session_state:
    st.session_state["meeting_id"] = None

if "analysis_done" not in st.session_state:
    st.session_state["analysis_done"] = False

if "accuracy_result" not in st.session_state:
    st.session_state["accuracy_result"] = None


# ============================================================
# WHISPER MODEL
# ============================================================

@st.cache_resource
def load_whisper_model():
    return whisper.load_model("base")


# ============================================================
# ACCURACY
# ============================================================

def normalize_text(text):
    return " ".join(
        text.lower().strip().split()
    )


def calculate_accuracy(reference_text, generated_text):

    from jiwer import wer, cer

    reference = normalize_text(reference_text)
    generated = normalize_text(generated_text)

    if not reference:
        raise ValueError(
            "Reference transcript is empty."
        )

    if not generated:
        raise ValueError(
            "Whisper transcript is empty."
        )

    word_error_rate = wer(
        reference,
        generated
    )

    character_error_rate = cer(
        reference,
        generated
    )

    accuracy = max(
        0.0,
        (1.0 - word_error_rate) * 100.0
    )

    return {
        "accuracy": accuracy,
        "wer": word_error_rate * 100.0,
        "cer": character_error_rate * 100.0
    }


# ============================================================
# BACKEND STATUS
# ============================================================

def backend_is_available():

    try:

        response = requests.get(
            f"{BACKEND_URL}/health",
            timeout=5
        )

        return response.status_code == 200

    except requests.exceptions.RequestException:

        return False


backend_available = backend_is_available()




# ============================================================
# LOGIN AND REGISTRATION
# ============================================================

if "access_token" not in st.session_state:
    st.session_state["access_token"] = None

if "user_email" not in st.session_state:
    st.session_state["user_email"] = None

# ============================================================
# LOGIN PAGE STYLING
# ============================================================

st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #F3F6FF, #EAF0FF, #FFFFFF);
    color: #263451;
}

[data-testid="stHeader"] {
    background: transparent;
}

[data-testid="stMainBlockContainer"] {
    max-width: 1050px;
    padding-top: 3rem;
}

h1, h2, h3, p, label {
    color: #263451;
}

div[data-baseweb="input"] {
    background: #FFFFFF;
    border: 1px solid #D5DFF5;
    border-radius: 10px;
}

div[data-baseweb="input"] input {
    color: #263451;
}

div[data-testid="stForm"] {
    background: #FFFFFF;
    border: 1px solid #DCE4F7;
    border-radius: 16px;
    padding: 1.3rem;
    box-shadow: 0 8px 28px rgba(75, 102, 170, 0.08);
}

div[data-testid="stFormSubmitButton"] button {
    background: #5278E8;
    color: #FFFFFF;
    border: none;
    border-radius: 10px;
    min-height: 44px;
    font-weight: 600;
}

div[data-testid="stFormSubmitButton"] button:hover {
    background: #3E63D1;
    color: #FFFFFF;
}

button[data-baseweb="tab"] {
    color: #52658C;
}

button[data-baseweb="tab"][aria-selected="true"] {
    color: #365FC9;
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# LOGIN FORM
# ============================================================

if not st.session_state["access_token"]:

    st.title("🎙️ MeetIQ")
    st.subheader("Welcome to your meeting intelligence workspace")
    st.write("Log in to continue or create a new account.")

    if not backend_available:
        st.error("Backend is offline. Start FastAPI and try again.")
        st.stop()

    login_tab, register_tab = st.tabs(["Login", "Register"])

    # ---------------- LOGIN ----------------

    with login_tab:
        with st.form("login_form"):
            login_email = st.text_input(
                "Email",
                key="login_email",
            )
            login_password = st.text_input(
                "Password",
                type="password",
                key="login_password",
            )
            login_submitted = st.form_submit_button(
                "Log in",
                use_container_width=True,
            )

        if login_submitted:
            try:
                response = requests.post(
                    f"{BACKEND_URL}/auth/login",
                    json={
                        "email": login_email,
                        "password": login_password,
                    },
                    timeout=15,
                )

                if response.status_code == 200:
                    result = response.json()

                    st.session_state["access_token"] = (
                        result["access_token"]
                    )
                    st.session_state["user_email"] = (
                        result["user"]["email"]
                    )

                    st.rerun()

                else:
                    st.error(
                        response.json().get(
                            "detail",
                            "Login failed.",
                        )
                    )

            except requests.exceptions.RequestException:
                st.error("Could not connect to the backend.")

    # ---------------- REGISTRATION ----------------

    with register_tab:
        with st.form("register_form"):
            register_email = st.text_input(
                "Email address",
                key="register_email",
            )
            register_password = st.text_input(
                "Password (minimum 8 characters)",
                type="password",
                key="register_password",
            )
            register_submitted = st.form_submit_button(
                "Create account",
                use_container_width=True,
            )

        if register_submitted:
            try:
                response = requests.post(
                    f"{BACKEND_URL}/auth/register",
                    json={
                        "email": register_email,
                        "password": register_password,
                    },
                    timeout=15,
                )

                if response.status_code == 200:
                    st.success(
                        "Account created. Select Login to continue."
                    )
                else:
                    st.error(
                        response.json().get(
                            "detail",
                            "Registration failed.",
                        )
                    )

            except requests.exceptions.RequestException:
                st.error("Could not connect to the backend.")

    st.stop()


# ============================================================
# SIDEBAR STYLE
# ============================================================

st.markdown(
    """
    <style>

    /* Sidebar */
    section[data-testid="stSidebar"] {
        min-width: 260px;
        max-width: 280px;
    }

    /* Sidebar title */
    .sidebar-brand {
        padding: 10px 8px 4px 8px;
    }

    .sidebar-brand h1 {
        font-size: 27px;
        margin-bottom: 2px;
        font-weight: 700;
    }

    .sidebar-brand p {
        font-size: 13px;
        margin-top: 0;
        color: #777;
    }

    .workspace-label {
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 1.5px;
        color: #888;
        margin-top: 20px;
        margin-bottom: 8px;
    }

    .system-label {
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 1.5px;
        color: #888;
        margin-top: 22px;
        margin-bottom: 8px;
    }

    /* Main page */
    .main-title {
        text-align: center;
        margin-bottom: 0;
    }

    .main-subtitle {
        text-align: center;
        color: #777;
        margin-top: 0;
    }

    /* Prevent unnecessary giant spacing */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# SIDEBAR NAVIGATION
# ============================================================

with st.sidebar:

    st.markdown(
        """
        <div class="sidebar-brand">
            <h1>🎙️ MeetIQ</h1>
            <p>Turn meetings into intelligence.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="workspace-label">WORKSPACE</div>',
        unsafe_allow_html=True
    )

    menu_items = [
    "🏠 Dashboard",
    "🎙️ Generate Transcript",
    "🧠 Meeting Intelligence",
    "📊 Meeting Details & Analytics",
    "✅ Decisions",
    "👥 Participants & Responsibilities",
    "📅 Deadlines",
    "🔥 Priorities",
    "🎯 Transcription Accuracy Testing",
    "📚 Meeting History",
    "🔎 Knowledge Search",
    "🎥 Zoom Integration"
]

    selected_page = st.radio(
        "Workspace",
        menu_items,
        label_visibility="collapsed"
    )

    st.divider()

    st.markdown(
        '<div class="system-label">SYSTEM</div>',
        unsafe_allow_html=True
    )

    if backend_available:

        st.success(
            "🟢 AI ENGINE ONLINE"
        )

        st.caption(
            "API backend connected"
        )

    else:

        st.error(
            "🔴 AI ENGINE OFFLINE"
        )

        st.caption(
            "Start the backend:"
        )

        st.code(
            "uvicorn backend.api:app --reload"
        )

    if st.session_state["meeting_id"]:

        st.divider()

        st.caption(
            "CURRENT MEETING"
        )

        st.write(
            f"Meeting #{st.session_state['meeting_id']}"
        )


# ============================================================
# MAIN HEADER
# ============================================================

st.markdown(
    '<h1 class="main-title">🎙️ MeetIQ</h1>',
    unsafe_allow_html=True
)

st.markdown(
    '<p class="main-subtitle">'
    'AI-powered meeting transcription and intelligence'
    '</p>',
    unsafe_allow_html=True
)

st.divider()


# ============================================================
# 0. PROFESSIONAL DASHBOARD
# ============================================================

if selected_page == "🏠 Dashboard":

    # -------------------- CUSTOM DASHBOARD STYLE --------------------
    st.markdown("""
    <style>
    .dashboard-banner {
        padding: 28px;
        border-radius: 16px;
        background: linear-gradient(120deg, #152347, #3949AB);
        color: white;
        margin-bottom: 24px;
    }
    .dashboard-banner h1 {
        color: white;
        margin-bottom: 8px;
        font-size: 32px;
    }
    .dashboard-banner p {
        color: #E0E7FF;
        font-size: 15px;
        margin-bottom: 0;
    }
    .section-heading {
        font-size: 21px;
        font-weight: 700;
        margin-top: 12px;
        margin-bottom: 12px;
    }
    </style>
    """, unsafe_allow_html=True)

    # -------------------- WELCOME BANNER --------------------
    st.markdown("""
    <div class="dashboard-banner">
        <h1>Welcome to MeetIQ 👋</h1>
        <p>
            Your intelligent workspace for meeting transcripts,
            decisions, action items, and AI-powered insights.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # -------------------- LOAD MEETING DATA --------------------
    try:
        meetings = get_meeting_history()
        if meetings is None:
            meetings = []
    except Exception as error:
        meetings = []
        st.error(f"Could not load meeting history: {error}")

    # -------------------- CALCULATE METRICS --------------------
    total_meetings = len(meetings)
    total_action_items = 0
    total_decisions = 0
    total_participants = 0

    for meeting in meetings:
        meeting_id = meeting.get("id")

        if not meeting_id:
            continue

        try:
            full_meeting = get_full_meeting(int(meeting_id))

            if not full_meeting:
                continue

            actions = full_meeting.get("action_items") or []
            decisions = full_meeting.get("decisions") or []
            participants = full_meeting.get("participants") or []

            if isinstance(actions, list):
                total_action_items += len(actions)

            if isinstance(decisions, list):
                total_decisions += len(decisions)

            if isinstance(participants, list):
                total_participants += len(participants)

        except Exception:
            continue

    # -------------------- METRIC CARDS --------------------
    st.markdown(
        '<div class="section-heading">📈 Meeting Overview</div>',
        unsafe_allow_html=True
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("📚 Total Meetings", total_meetings)

    with col2:
        st.metric("📌 Action Items", total_action_items)

    with col3:
        st.metric("✅ Decisions", total_decisions)

    with col4:
        st.metric("👥 Participants", total_participants)

    st.divider()

    # -------------------- SYSTEM STATUS --------------------
    st.markdown(
        '<div class="section-heading">⚙️ System Status</div>',
        unsafe_allow_html=True
    )

    status_col1, status_col2 = st.columns(2)

    with status_col1:
        if backend_available:
            st.success("🟢 AI Backend Connected")
        else:
            st.error("🔴 AI Backend Offline")

    with status_col2:
        st.info(f"📊 {total_meetings} meetings stored in history")

    st.divider()

    # -------------------- RECENT MEETINGS --------------------
    st.markdown(
        '<div class="section-heading">🕒 Recent Meetings</div>',
        unsafe_allow_html=True
    )

    if not meetings:
        st.info("No meetings available yet. Generate your first transcript to get started.")

    else:
        for meeting in meetings[:5]:
            meeting_id = meeting.get("id", "Unknown")
            filename = meeting.get("filename", "Unknown file")
            summary = meeting.get("summary") or "No summary available."
            created_at = meeting.get("created_at", "Unknown")

            with st.container(border=True):
                col1, col2 = st.columns([3, 1])

                with col1:
                    st.markdown(f"**📄 Meeting #{meeting_id} — {filename}**")
                    st.write(summary)

                with col2:
                    st.caption("Created")
                    st.write(str(created_at))

    st.divider()

    # -------------------- MEETING KNOWLEDGE SEARCH --------------------
    st.markdown(
        '<div class="section-heading">🔎 Search Meeting Knowledge</div>',
        unsafe_allow_html=True
    )

    with st.container(border=True):
        dashboard_query = st.text_input(
            "Search your previous meetings",
            placeholder="Example: Which meeting discussed database migration?",
            key="dashboard_search"
        )

        if st.button("🔍 Search Meetings", key="dashboard_search_button"):

            if not dashboard_query.strip():
                st.warning("Please enter a search query.")

            elif not backend_available:
                st.error("The AI backend is not available.")

            else:
                try:
                    search_response = requests.post(
                        f"{BACKEND_URL}/search",
                        json={"query": dashboard_query, "top_k": 5},
                        timeout=30
                    )

                    if search_response.status_code != 200:
                        st.error("Meeting search failed.")
                    else:
                        results = search_response.json().get("results", [])

                        if not results:
                            st.info("No relevant meetings found.")
                        else:
                            st.success(f"Found {len(results)} result(s).")

                            for result in results:
                                st.markdown(
                                    f"**Meeting #{result.get('meeting_id', 'Unknown')}**"
                                )
                                st.write(
                                    result.get("content", "No content available.")
                                )
                                st.caption(
                                    f"Content type: {result.get('content_type', 'Unknown')}"
                                )
                                st.divider()

                except requests.exceptions.Timeout:
                    st.error("Search timed out. Please try again.")

                except requests.exceptions.RequestException as error:
                    st.error(f"Search request failed: {error}")

    st.divider()

    # -------------------- AI MEETING ASSISTANT --------------------
    st.markdown(
        '<div class="section-heading">🤖 AI Meeting Assistant</div>',
        unsafe_allow_html=True
    )

    with st.container(border=True):
        dashboard_question = st.text_input(
            "Ask a question about your meetings",
            placeholder="Example: What decisions were made in previous meetings?",
            key="dashboard_question"
        )

        if st.button("🤖 Ask MeetIQ AI", key="dashboard_ask_button"):

            if not dashboard_question.strip():
                st.warning("Please enter a question.")

            elif not backend_available:
                st.error("The AI backend is not available.")

            else:
                try:
                    rag_response = requests.post(
                        f"{BACKEND_URL}/rag-question",
                        json={"question": dashboard_question},
                        timeout=120
                    )

                    if rag_response.status_code != 200:
                        st.error("The AI assistant request failed.")
                    else:
                        rag_data = rag_response.json().get("data", {})
                        answer = rag_data.get("answer", "No answer available.")
                        sources = rag_data.get("sources", [])

                        st.success("🤖 AI Answer")
                        st.write(answer)

                        if sources:
                            st.markdown("**Sources**")
                            for source in sources:
                                st.markdown(
                                    f"- Meeting #{source.get('meeting_id', 'Unknown')}"
                                )

                except requests.exceptions.Timeout:
                    st.error("The AI assistant timed out. Please try again.")

                except requests.exceptions.RequestException as error:
                    st.error(f"AI assistant request failed: {error}")
# ============================================================
# 1.5 MEETING DETAILS & ANALYTICS
# ============================================================

elif selected_page == "📊 Meeting Details & Analytics":

    st.header("📊 Meeting Details & Analytics")

    st.write(
        "Select a meeting to view its complete information, "
        "transcript, summary, decisions, action items, "
        "participants, deadlines, and analytics."
    )

    # --------------------------------------------------------
    # LOAD MEETING LIST
    # --------------------------------------------------------

    try:

        meetings = get_meeting_history()

    except Exception as error:

        st.error(
            f"❌ Could not load meetings: {error}"
        )

        meetings = []

    if not meetings:

        st.info(
            "📭 No meetings are available."
        )

    else:

        # ----------------------------------------------------
        # MEETING SELECTION
        # ----------------------------------------------------

        meeting_options = {}

        for meeting in meetings:

            meeting_id = meeting.get(
                "id"
            )

            filename = meeting.get(
                "filename",
                "Unknown"
            )

            created_at = meeting.get(
                "created_at",
                "Unknown"
            )

            meeting_options[
                f"Meeting #{meeting_id} | "
                f"{filename} | "
                f"{created_at}"
            ] = meeting_id

        selected_meeting_label = st.selectbox(
            "🔍 Select a Meeting",
            list(meeting_options.keys())
        )

        selected_meeting_id = meeting_options[
            selected_meeting_label
        ]

        # ----------------------------------------------------
        # LOAD FULL MEETING
        # ----------------------------------------------------

        try:

            meeting = get_full_meeting(
                selected_meeting_id
            )

        except Exception as error:

            st.error(
                f"❌ Could not load meeting details: "
                f"{error}"
            )

            meeting = None

        if not meeting:

            st.error(
                "❌ Meeting details could not be found."
            )

        else:

            st.success(
                f"✅ Meeting #{selected_meeting_id} loaded successfully."
            )

            # ------------------------------------------------
            # BASIC MEETING INFORMATION
            # ------------------------------------------------

            st.subheader(
                "📌 Meeting Information"
            )

            col1, col2, col3 = st.columns(3)

            with col1:

                st.metric(
                    "Meeting ID",
                    meeting.get(
                        "id",
                        "Unknown"
                    )
                )

            with col2:

                st.write(
                    "**Filename**"
                )

                st.write(
                    meeting.get(
                        "filename",
                        "Unknown"
                    )
                )

            with col3:

                st.write(
                    "**Created At**"
                )

                st.write(
                    meeting.get(
                        "created_at",
                        "Unknown"
                    )
                )

            st.divider()

            # ------------------------------------------------
            # SUMMARY
            # ------------------------------------------------

            st.subheader(
                "📝 Meeting Summary"
            )

            summary = meeting.get(
                "summary",
                ""
            )

            if summary:

                st.info(summary)

            else:

                st.info(
                    "No summary available."
                )

            # ------------------------------------------------
            # KEY POINTS
            # ------------------------------------------------

            st.subheader(
                "🔑 Key Points"
            )

            key_points = meeting.get(
                "key_points",
                []
            )

            if key_points:

                for point in key_points:

                    st.markdown(
                        f"- {point}"
                    )

            else:

                st.info(
                    "No key points available."
                )

            st.divider()

            # ------------------------------------------------
            # TRANSCRIPT
            # ------------------------------------------------

            st.subheader(
                "📄 Full Transcript"
            )

            transcript = meeting.get(
                "transcript",
                ""
            )

            if transcript:

                st.text_area(
                    "Meeting Transcript",
                    transcript,
                    height=300,
                    disabled=True
                )

            else:

                st.info(
                    "No transcript available."
                )

            st.divider()

            # ------------------------------------------------
            # DECISIONS
            # ------------------------------------------------

            st.subheader(
                "✅ Decisions"
            )

            decisions = meeting.get(
                "decisions",
                []
            )

            if decisions:

                for index, decision in enumerate(
                    decisions,
                    start=1
                ):

                    st.markdown(
                        f"**{index}.** {decision}"
                    )

            else:

                st.info(
                    "No decisions recorded."
                )

            # ------------------------------------------------
            # ACTION ITEMS
            # ------------------------------------------------

            st.subheader(
                "📌 Action Items"
            )

            action_items = meeting.get(
                "action_items",
                []
            )

            if action_items:

                for index, action in enumerate(
                    action_items,
                    start=1
                ):

                    task = action.get(
                        "task",
                        "Unknown task"
                    )

                    assigned_to = action.get(
                        "assigned_to"
                    )

                    deadline = action.get(
                        "deadline"
                    )

                    priority = action.get(
                        "priority"
                    )

                    status = action.get(
                        "status"
                    )

                    with st.container(
                        border=True
                    ):

                        st.markdown(
                            f"### {index}. {task}"
                        )

                        c1, c2, c3, c4 = st.columns(4)

                        with c1:

                            st.write(
                                "**Assigned To**"
                            )

                            st.write(
                                assigned_to
                                if assigned_to
                                else "Unknown"
                            )

                        with c2:

                            st.write(
                                "**Deadline**"
                            )

                            st.write(
                                deadline
                                if deadline
                                else "Not specified"
                            )

                        with c3:

                            st.write(
                                "**Priority**"
                            )

                            st.write(
                                priority
                                if priority
                                else "Not specified"
                            )

                        with c4:

                            st.write(
                                "**Status**"
                            )

                            st.write(
                                status
                                if status
                                else "Pending"
                            )

            else:

                st.info(
                    "No action items recorded."
                )

            st.divider()

            # ------------------------------------------------
            # PARTICIPANTS
            # ------------------------------------------------

            st.subheader(
                "👥 Participants"
            )

            participants = meeting.get(
                "participants",
                []
            )

            if participants:

                for participant in participants:

                    name = participant.get(
                        "name",
                        "Unknown"
                    )

                    role = participant.get(
                        "role"
                    )

                    responsibilities = participant.get(
                        "responsibilities",
                        []
                    )

                    with st.container(
                        border=True
                    ):

                        st.markdown(
                            f"### 👤 {name}"
                        )

                        st.write(
                            f"**Role:** "
                            f"{role or 'Not specified'}"
                        )

                        if responsibilities:

                            st.write(
                                "**Responsibilities:**"
                            )

                            for responsibility in responsibilities:

                                st.markdown(
                                    f"- {responsibility}"
                                )

            else:

                st.info(
                    "No participants recorded."
                )

            st.divider()

            # ------------------------------------------------
            # DEADLINES
            # ------------------------------------------------

            st.subheader(
                "📅 Deadlines"
            )

            deadlines = meeting.get(
                "deadlines",
                []
            )

            if deadlines:

                for deadline in deadlines:

                    st.markdown(
                        f"- 📅 {deadline}"
                    )

            else:

                st.info(
                    "No deadlines recorded."
                )

            # ------------------------------------------------
            # PRIORITIES
            # ------------------------------------------------

            st.subheader(
                "🔥 Priorities"
            )

            priorities = meeting.get(
                "priorities",
                []
            )

            if priorities:

                for priority in priorities:

                    st.markdown(
                        f"- {priority}"
                    )

            else:

                st.info(
                    "No priorities recorded."
                )

            st.divider()
            total_key_points = len(
                key_points if isinstance(key_points, list) else []
            )
            total_decisions = len(
                decisions if isinstance(decisions, list) else []
            )
            total_action_items = len(
                action_items if isinstance(action_items, list) else []
            )
            total_participants = len(
                participants if isinstance(participants, list) else []
            )
            total_deadlines = len(
                deadlines if isinstance(deadlines, list) else []
            )
            total_priorities = len(
                priorities if isinstance(priorities, list) else []
            )
        # ------------------------------------------------
            # PROFESSIONAL MEETING ANALYTICS DASHBOARD
            # ------------------------------------------------
            import pandas as pd

            st.subheader("📊 Meeting Analytics")
            st.caption(
                "Overview of the selected meeting's intelligence"
            )

            # METRIC CARDS
            m1, m2, m3, m4 = st.columns(4)

            with m1:
                with st.container(border=True):
                    st.caption("🔑 Key Points")
                    st.metric("Total", total_key_points)

            with m2:
                with st.container(border=True):
                    st.caption("✅ Decisions")
                    st.metric("Total", total_decisions)

            with m3:
                with st.container(border=True):
                    st.caption("📌 Action Items")
                    st.metric("Total", total_action_items)

            with m4:
                with st.container(border=True):
                    st.caption("👥 Participants")
                    st.metric("Total", total_participants)

            st.markdown("### 📈 Meeting Insights")

            # DATA FOR OVERVIEW CHART
            overview_df = pd.DataFrame({
                "Category": [
                    "Key Points",
                    "Decisions",
                    "Action Items",
                    "Participants",
                    "Deadlines",
                    "Priorities",
                ],
                "Count": [
                    total_key_points,
                    total_decisions,
                    total_action_items,
                    total_participants,
                    total_deadlines,
                    total_priorities,
                ],
            })

            # ACTION ITEM STATUS COUNTS
            status_counts = {
                "Pending": 0,
                "In Progress": 0,
                "Completed": 0,
            }

            for item in action_items:
                if not isinstance(item, dict):
                    continue

                status = str(
                    item.get("status") or "Pending"
                ).strip().lower()

                if status in ("completed", "complete", "done"):
                    status_counts["Completed"] += 1
                elif status in (
                    "in progress",
                    "in-progress",
                    "ongoing",
                ):
                    status_counts["In Progress"] += 1
                else:
                    status_counts["Pending"] += 1

            chart1, chart2 = st.columns(2)

            with chart1:
                with st.container(border=True):
                    st.markdown("#### Meeting Overview")
                    st.bar_chart(
                        overview_df.set_index("Category")["Count"],
                        height=300,
                    )

            with chart2:
                with st.container(border=True):
                    st.markdown("#### Action Item Status")

                    status_df = pd.DataFrame({
                        "Status": list(status_counts.keys()),
                        "Tasks": list(status_counts.values()),
                    })

                    st.bar_chart(
                        status_df.set_index("Status"),
                        height=300,
                    )

            # OVERVIEW TABLE
            st.markdown("### 📋 Meeting Overview")

            with st.container(border=True):
                st.dataframe(
                    overview_df.rename(columns={
                        "Category": "Metric",
                        "Count": "Value",
                    }),
                    hide_index=True,
                    use_container_width=True,
                )

           

# ============================================================
# 1. GENERATE TRANSCRIPT
# ============================================================

if selected_page == "🎙️ Generate Transcript":

    st.header("1. Generate Transcript")

    st.write(
        "Upload an audio or video meeting recording "
        "and generate a Whisper transcript."
    )

    st.info(
        "🎵 Audio: MP3, WAV, M4A, AAC, FLAC\n\n"
        "🎬 Video: MP4, MOV, AVI, MKV\n\n"
        "📦 Maximum file size: 200 MB"
    )

    uploaded_file = st.file_uploader(
        "📂 Upload Meeting Recording",
        type=SUPPORTED_FILES,
        key="meeting_recording"
    )

    if uploaded_file is not None:

        extension = uploaded_file.name.split(".")[-1].lower()
        size_mb = uploaded_file.size / (1024 * 1024)

        if size_mb > MAX_FILE_SIZE_MB:
            st.error(
                f"❌ File is too large. Maximum allowed size is "
                f"{MAX_FILE_SIZE_MB} MB."
            )
            st.stop()

        # Clear previous results when a different recording is uploaded.
        if (
            st.session_state["transcript_filename"]
            and st.session_state["transcript_filename"]
            != uploaded_file.name
        ):
            st.session_state["transcript"] = ""
            st.session_state["transcript_filename"] = ""
            st.session_state["meeting_data"] = {}
            st.session_state["meeting_id"] = None
            st.session_state["analysis_done"] = False
            st.session_state["accuracy_result"] = None

        col1, col2, col3 = st.columns(3)

        with col1:
            st.write("**File:**", uploaded_file.name)

        with col2:
            st.write("**Size:**", f"{size_mb:.2f} MB")

        with col3:
            st.write("**Type:**", extension.upper())

        file_path = os.path.join(
            UPLOAD_FOLDER,
            uploaded_file.name
        )

        with open(file_path, "wb") as file:
            file.write(uploaded_file.getbuffer())

        st.success("📁 File uploaded successfully!")

        if st.button(
            "🎙️ Generate Transcript",
            type="primary",
            use_container_width=True
        ):

            try:
                # Step 1: Load Whisper.
                with st.spinner("🔄 Loading Whisper model..."):
                    model = load_whisper_model()

                # Step 2: Generate transcript.
                with st.spinner(
                    "🎧 Processing recording and generating transcript..."
                ):
                    result = model.transcribe(
                        file_path,
                        fp16=False
                    )

                transcript = result["text"].strip()

                if not transcript:
                    st.error("❌ Transcript is empty.")
                    st.stop()

                # Step 3: Store transcript in session state.
                st.session_state["transcript"] = transcript
                st.session_state["transcript_filename"] = uploaded_file.name
                st.session_state["meeting_data"] = {}
                st.session_state["meeting_id"] = None
                st.session_state["analysis_done"] = False
                st.session_state["accuracy_result"] = None

                # Step 4: Save transcript as a text file.
                base_name = os.path.splitext(
                    uploaded_file.name
                )[0]

                transcript_path = os.path.join(
                    TRANSCRIPT_FOLDER,
                    f"{base_name}_transcript.txt"
                )

                with open(
                    transcript_path,
                    "w",
                    encoding="utf-8"
                ) as file:
                    file.write(transcript)

                st.success("✅ Transcript generated successfully!")

                # Step 5: Analyze transcript using the LLM.
                with st.spinner("🤖 Analyzing meeting transcript..."):
                    meeting_result = process_transcript(transcript)

                # Step 6: Convert the validated result to a dictionary.
                if hasattr(meeting_result, "model_dump"):
                    meeting_result = meeting_result.model_dump()
                elif hasattr(meeting_result, "dict"):
                    meeting_result = meeting_result.dict()

                # Step 7: Save the meeting and AI analysis to SQLite.
                with st.spinner("💾 Saving meeting to database..."):
                    meeting_id = save_meeting(
                        intelligence=meeting_result,
                        transcript=transcript,
                        filename=uploaded_file.name
                    )

                # Step 8: Store the results and database ID.
                st.session_state["meeting_data"] = meeting_result
                st.session_state["meeting_id"] = meeting_id
                st.session_state["analysis_done"] = True

                st.success("✅ Meeting analysis generated successfully!")
                st.success(
                    f"💾 Meeting saved to database. "
                    f"Meeting ID: {meeting_id}"
                )

            except Exception as error:
                st.error(
                    f"❌ Processing or database saving failed: {error}"
                )

    # ============================================================
    # DISPLAY GENERATED TRANSCRIPT
    # ============================================================

    if st.session_state["transcript"]:

        st.divider()
        st.subheader("📄 Generated Text")

        st.text_area(
            "Whisper Generated Transcript",
            st.session_state["transcript"],
            height=300
        )

        base_name = os.path.splitext(
            st.session_state["transcript_filename"]
        )[0]

        st.download_button(
            "📥 Download Transcript",
            st.session_state["transcript"],
            file_name=f"{base_name}_transcript.txt",
            mime="text/plain",
            use_container_width=True
        )

        # ========================================================
        # DISPLAY MEETING INTELLIGENCE
        # ========================================================

        if st.session_state.get("analysis_done", False):

            meeting_data = st.session_state.get("meeting_data", {})

            st.divider()
            st.subheader("🤖 Meeting Intelligence")

            st.markdown("### 📝 Summary")
            st.write(
                meeting_data.get("summary")
                or "No summary available."
            )

            st.markdown("### 🔑 Key Points")
            for point in meeting_data.get("key_points") or []:
                st.markdown(f"- {point}")

            st.markdown("### ✅ Decisions")
            for decision in meeting_data.get("decisions") or []:
                st.markdown(f"- {decision}")

            st.markdown("### 📌 Action Items")

            for item in meeting_data.get("action_items") or []:

                if isinstance(item, dict):
                    st.markdown(
                        f"**Task:** {item.get('task') or 'Not specified'}"
                    )
                    st.write(
                        f"Assigned to: {item.get('assigned_to') or 'Not specified'}"
                    )
                    st.write(
                        f"Deadline: {item.get('deadline') or 'Not specified'}"
                    )
                    st.write(
                        f"Priority: {item.get('priority') or 'Not specified'}"
                    )
                    st.write(
                        f"Status: {item.get('status') or 'Pending'}"
                    )
                    st.divider()
                else:
                    st.markdown(f"- {item}")

            st.markdown("### 👥 Participants")

            for person in meeting_data.get("participants") or []:

                if isinstance(person, dict):
                    st.markdown(
                        f"- **{person.get('name') or 'Not specified'}**"
                    )
                else:
                    st.markdown(f"- {person}")

            st.markdown("### 📅 Deadlines")

            for deadline in meeting_data.get("deadlines") or []:
                st.markdown(f"- {deadline}")

            st.markdown("### 🎯 Priorities")

            for priority in meeting_data.get("priorities") or []:
                st.markdown(f"- {priority}")
# ============================================================
# 2. MEETING INTELLIGENCE
# ============================================================

elif selected_page == "🧠 Meeting Intelligence":

    st.header(
        "2. Meeting Intelligence"
    )

    if not st.session_state["transcript"]:

        st.info(
            "ℹ️ Generate a transcript first."
        )

    elif not backend_available:

        st.error(
            "❌ AI backend is not connected."
        )

    else:

        if st.button(
            "🧠 Generate Meeting Intelligence",
            type="primary",
            use_container_width=True
        ):

            try:

                with st.spinner(
                    "🤖 Analyzing meeting with AI..."
                ):

                    response = requests.post(
                        f"{BACKEND_URL}/analyze",
                        json={
                            "filename":
                                st.session_state[
                                    "transcript_filename"
                                ],

                            "transcript":
                                st.session_state[
                                    "transcript"
                                ]
                        },
                        timeout=180
                    )

                if response.status_code != 200:

                    st.error(
                        "❌ AI processing failed."
                    )

                    try:
                        st.code(
                            str(
                                response.json()
                            )
                        )
                    except Exception:
                        st.code(
                            response.text
                        )

                else:

                    data = response.json()

                    st.session_state[
                        "meeting_id"
                    ] = data.get(
                        "meeting_id"
                    )

                    st.session_state[
                        "meeting_data"
                    ] = data.get(
                        "data",
                        {}
                    )

                    st.session_state[
                        "analysis_done"
                    ] = True

                    st.success(
                        "✅ Meeting analyzed "
                        "and saved successfully!"
                    )

            except requests.exceptions.Timeout:

                st.error(
                    "❌ Backend request timed out."
                )

            except requests.exceptions.ConnectionError:

                st.error(
                    "❌ Could not connect "
                    "to the MeetIQ backend."
                )

            except Exception as error:

                st.error(
                    f"❌ AI processing failed: {error}"
                )


        if st.session_state["analysis_done"]:

            data = st.session_state[
                "meeting_data"
            ]

            st.success(
                f"Meeting ID: "
                f"{st.session_state['meeting_id']}"
            )

            st.subheader(
                "📝 Summary"
            )

            st.write(
                data.get(
                    "summary",
                    "No summary available."
                )
            )

            st.subheader(
                "🔑 Key Points"
            )

            key_points = data.get(
                "key_points",
                []
            )

            if key_points:

                for point in key_points:

                    st.markdown(
                        f"- {point}"
                    )

            else:

                st.info(
                    "No key points identified."
                )

            # ------------------------------------------------
            # Action Items
            # ------------------------------------------------

            st.subheader(
                "📌 Action Items"
            )

            action_items = data.get(
                "action_items",
                []
            )

            if action_items:

                for action in action_items:

                    task = action.get(
                        "task",
                        "Unknown task"
                    )

                    assigned_to = action.get(
                        "assigned_to"
                    )

                    deadline = action.get(
                        "deadline"
                    )

                    priority = action.get(
                        "priority"
                    )

                    status = action.get(
                        "status"
                    )

                    with st.container(
                        border=True
                    ):

                        st.markdown(
                            f"### 📌 {task}"
                        )

                        col1, col2 = st.columns(2)

                        with col1:

                            st.write(
                                f"**👤 Assigned to:** "
                                f"{assigned_to or 'Unknown'}"
                            )

                            st.write(
                                f"**📅 Deadline:** "
                                f"{deadline or 'Not specified'}"
                            )

                        with col2:

                            st.write(
                                f"**🔥 Priority:** "
                                f"{priority or 'Not specified'}"
                            )

                            st.write(
                                f"**⏳ Status:** "
                                f"{status or 'Pending'}"
                            )

            else:

                st.info(
                    "No action items identified."
                )


# ============================================================
# 3. DECISIONS
# ============================================================

elif selected_page == "✅ Decisions":

    st.header(
        "3. Decisions"
    )

    if not st.session_state["analysis_done"]:

        st.info(
            "ℹ️ Generate Meeting Intelligence first."
        )

    else:

        decisions = (
            st.session_state[
                "meeting_data"
            ].get(
                "decisions",
                []
            )
        )

        if decisions:

            for decision in decisions:

                st.container(
                    border=True
                ).markdown(
                    f"### ✅ {decision}"
                )

        else:

            st.info(
                "No decisions identified."
            )


# ============================================================
# 4. PARTICIPANTS & RESPONSIBILITIES
# ============================================================

elif selected_page == (
    "👥 Participants & Responsibilities"
):

    st.header(
        "4. Participants & Responsibilities"
    )

    if not st.session_state["analysis_done"]:

        st.info(
            "ℹ️ Generate Meeting Intelligence first."
        )

    else:

        participants = (
            st.session_state[
                "meeting_data"
            ].get(
                "participants",
                []
            )
        )

        if not participants:

            st.info(
                "No participants identified."
            )

        else:

            for participant in participants:
                
                name = participant.get("name")

                if not name or str(name).strip().lower() in ("null", "none", ""):
                    name = "Unknown Participant"

                role = participant.get(
                    "role"
                )

                responsibilities = (
                    participant.get(
                        "responsibilities",
                        []
                    )
                )

                with st.container(
                    border=True
                ):

                    st.subheader(
                        f"👤 {name}"
                    )

                    st.write(
                        f"**Role:** "
                        f"{role or 'Not specified'}"
                    )

                    st.write(
                        "**Responsibilities:**"
                    )

                    if responsibilities:

                        for responsibility in (
                            responsibilities
                        ):

                            st.markdown(
                                f"- {responsibility}"
                            )

                    else:

                        st.write(
                            "None identified."
                        )


# ============================================================
# 5. DEADLINES
# ============================================================

elif selected_page == "📅 Deadlines":

    st.header(
        "5. Deadlines"
    )

    if not st.session_state["analysis_done"]:

        st.info(
            "ℹ️ Generate Meeting Intelligence first."
        )

    else:

        data = st.session_state[
            "meeting_data"
        ]

        deadlines = data.get(
            "deadlines",
            []
        )

        if deadlines:

            for deadline in deadlines:

                st.markdown(
                    f"### 📅 {deadline}"
                )

        else:

            st.info(
                "No deadlines identified."
            )

        actions = data.get(
            "action_items",
            []
        )

        if actions:

            st.divider()

            st.subheader(
                "📌 Action Item Deadlines"
            )

            for action in actions:

                deadline = action.get(
                    "deadline"
                )

                if deadline:

                    st.markdown(
                        f"- **{action.get('task', 'Task')}** "
                        f"→ {deadline}"
                    )


# ============================================================
# 6. PRIORITIES
# ============================================================

elif selected_page == "🔥 Priorities":

    st.header(
        "6. Priorities"
    )

    if not st.session_state["analysis_done"]:

        st.info(
            "ℹ️ Generate Meeting Intelligence first."
        )

    else:

        data = st.session_state[
            "meeting_data"
        ]

        priorities = data.get(
            "priorities",
            []
        )

        if priorities:

            for priority in priorities:

                st.markdown(
                    f"### 🔥 {priority}"
                )

        else:

            st.info(
                "No priorities identified."
            )

        actions = data.get(
            "action_items",
            []
        )

        if actions:

            st.divider()

            st.subheader(
                "📌 Action Item Priorities"
            )

            for action in actions:

                priority = action.get(
                    "priority"
                )

                if priority:

                    st.markdown(
                        f"- **{action.get('task', 'Task')}** "
                        f"→ {priority}"
                    )


# ============================================================
# 7. TRANSCRIPTION ACCURACY TESTING
# ============================================================

elif selected_page == (
    "🎯 Transcription Accuracy Testing"
):

    st.header(
        "7. Transcription Accuracy Testing"
    )

    st.write(
        "Compare the Whisper-generated transcript "
        "with the correct reference transcript."
    )

    if not st.session_state["transcript"]:

        st.info(
            "ℹ️ Generate the Whisper transcript first "
            "from '1. Generate Transcript'."
        )

    else:

        st.success(
            "✅ Whisper transcript is ready for comparison."
        )

        st.subheader(
            "📄 Whisper Generated Transcript"
        )

        st.text_area(
            "Generated Transcript",
            st.session_state["transcript"],
            height=250,
            disabled=True
        )

        st.divider()

        st.subheader(
            "📄 Upload Reference Transcript"
        )

        reference_file = st.file_uploader(
            "Reference Transcript (.txt)",
            type=["txt"],
            key="reference_transcript"
        )

        if reference_file is not None:

            try:

                reference_text = (
                    reference_file
                    .getvalue()
                    .decode("utf-8")
                    .strip()
                )

                if not reference_text:

                    st.error(
                        "❌ Reference transcript is empty."
                    )

                else:

                    st.success(
                        "✅ Reference transcript uploaded successfully."
                    )

                    if st.button(
                        "📊 Calculate Accuracy",
                        type="primary",
                        use_container_width=True
                    ):

                        try:

                            result = calculate_accuracy(
                                reference_text,
                                st.session_state[
                                    "transcript"
                                ]
                            )

                            st.session_state[
                                "accuracy_result"
                            ] = result

                        except ImportError:

                            st.error(
                                "❌ jiwer is not installed."
                            )

                            st.code(
                                "pip install jiwer"
                            )

                        except Exception as error:

                            st.error(
                                f"❌ Accuracy calculation failed: "
                                f"{error}"
                            )

            except UnicodeDecodeError:

                st.error(
                    "❌ Reference transcript must be "
                    "a UTF-8 .txt file."
                )


        # Results remain visible after reruns.
        if st.session_state[
            "accuracy_result"
        ] is not None:

            result = st.session_state[
                "accuracy_result"
            ]

            st.divider()

            st.subheader(
                "📊 Accuracy Test Results"
            )

            col1, col2, col3 = st.columns(3)

            with col1:

                st.metric(
                    "Word Accuracy",
                    f"{result['accuracy']:.2f}%"
                )

            with col2:

                st.metric(
                    "Word Error Rate",
                    f"{result['wer']:.2f}%"
                )

            with col3:

                st.metric(
                    "Character Error Rate",
                    f"{result['cer']:.2f}%"
                )

            if result["accuracy"] >= 90:

                st.success(
                    "🎉 Accuracy target achieved! "
                    "The transcription accuracy "
                    "is ≥ 90%."
                )

            else:

                st.warning(
                    "⚠️ Accuracy is below 90%. "
                    "More testing or model improvement "
                    "may be required."
                )

            st.subheader(
                "Accuracy Testing Checklist"
            )

            st.write(
                "✅ Reference transcript compared"
            )

            st.write(
                "✅ Missing/incorrect words evaluated "
                "using Word Error Rate"
            )

            st.write(
                f"✅ Calculated accuracy: "
                f"{result['accuracy']:.2f}%"
            )

            if result["accuracy"] >= 90:

                st.write(
                    "✅ Requirement achieved: ≥ 90%"
                )

            else:

                st.write(
                    "❌ Requirement not yet achieved: < 90%"
                )
                # ============================================================
# 8. MEETING HISTORY
# ============================================================

elif selected_page == "📚 Meeting History":

    st.header("8. Meeting History")

    st.write(
        "View previously processed meetings stored "
        "in the SQLite database."
    )

    try:

        meetings = get_meeting_history()

        if not meetings:

            st.info(
                "📭 No meetings have been saved yet."
            )

        else:

            st.success(
                f"📚 {len(meetings)} meeting(s) "
                "stored in the database."
            )

            st.subheader("Saved Meetings")

            # ------------------------------------------------
            # DATABASE-STYLE HISTORY TABLE
            # ------------------------------------------------

            history_rows = []

            for meeting in meetings:

                history_rows.append(
                    {
                        "ID": meeting.get("id"),
                        "Filename": meeting.get(
                            "filename",
                            "Unknown"
                        ),
                        "Summary": meeting.get(
                            "summary",
                            "No summary available."
                        ),
                        "Created At": meeting.get(
                            "created_at",
                            "Unknown"
                        )
                    }
                )

            st.dataframe(
                history_rows,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "ID": st.column_config.NumberColumn(
                        "Meeting ID"
                    ),
                    "Filename": st.column_config.TextColumn(
                        "File"
                    ),
                    "Summary": st.column_config.TextColumn(
                        "Summary"
                    ),
                    "Created At": st.column_config.TextColumn(
                        "Created"
                    )
                }
            )

            st.caption(
                "The table above represents meeting records "
                "persisted in the SQLite database."
            )

            st.divider()

            st.subheader("Open a Saved Meeting")

            # ------------------------------------------------
            # VIEW MEETING BUTTONS
            # ------------------------------------------------

            for meeting in meetings:

                meeting_id = meeting.get(
                    "id"
                )

                if st.button(
                    f"🔍 View Meeting #{meeting_id}",
                    key=f"view_{meeting_id}"
                ):

                    try:

                        full_meeting = (
                            get_full_meeting(
                                meeting_id
                            )
                        )

                        if full_meeting:

                            st.session_state[
                                "history_meeting"
                            ] = full_meeting

                        else:

                            st.error(
                                "Meeting record not found."
                            )

                    except Exception as error:

                        st.error(
                            f"❌ Could not load meeting: "
                            f"{error}"
                        )


            # ------------------------------------------------
            # SELECTED MEETING DETAILS
            # ------------------------------------------------

            if (
                "history_meeting"
                in st.session_state
            ):

                meeting = st.session_state[
                    "history_meeting"
                ]

                st.divider()

                st.subheader(
                    "📋 Meeting Details"
                )

                st.write(
                    f"**Meeting ID:** "
                    f"{meeting.get('id')}"
                )

                st.write(
                    f"**Filename:** "
                    f"{meeting.get('filename')}"
                )

                st.write(
                    f"**Created:** "
                    f"{meeting.get('created_at')}"
                )

                # Original Transcript
                st.subheader(
                    "🎙️ Original Transcript"
                )

                transcript = meeting.get(
                    "transcript",
                    ""
                )

                if transcript:

                    with st.expander(
                        "📄 Show Original Transcript"
                    ):

                        st.text_area(
                            "Stored Transcript",
                            transcript,
                            height=300,
                            disabled=True
                        )

                else:

                    st.info(
                        "No transcript stored for this meeting."
                    )

                # Summary
                st.subheader(
                    "📝 Summary"
                )

                st.write(
                    meeting.get(
                        "summary",
                        "No summary available."
                    )
                )

                # Key Points
                st.subheader(
                    "🔑 Key Points"
                )

                key_points = meeting.get(
                    "key_points",
                    []
                )

                if key_points:

                    for point in key_points:

                        st.markdown(
                            f"- {point}"
                        )

                else:

                    st.info(
                        "No key points."
                    )

                # Decisions
                st.subheader(
                    "✅ Decisions"
                )

                decisions = meeting.get(
                    "decisions",
                    []
                )

                if decisions:

                    for decision in decisions:

                        st.markdown(
                            f"- {decision}"
                        )

                else:

                    st.info(
                        "No decisions."
                    )

                # Participants
                st.subheader(
                    "👥 Participants & Responsibilities"
                )

                participants = meeting.get(
                    "participants",
                    []
                )

                if participants:

                    for participant in participants:

                        st.markdown(
                            f"**👤 "
                            f"{participant.get('name', 'Unknown')}**"
                        )

                        role = participant.get(
                            "role"
                        )

                        if role:

                            st.write(
                                f"Role: {role}"
                            )

                        responsibilities = (
                            participant.get(
                                "responsibilities",
                                []
                            )
                        )

                        for responsibility in (
                            responsibilities
                        ):

                            st.markdown(
                                f"- {responsibility}"
                            )

                else:

                    st.info(
                        "No participants."
                    )

                # Action Items
                st.subheader(
                    "📌 Action Items"
                )

                action_items = meeting.get(
                    "action_items",
                    []
                )

                if action_items:

                    for action in action_items:

                        task = action.get(
                            "task",
                            "Unknown task"
                        )

                        assigned_to = action.get(
                            "assigned_to"
                        )

                        deadline = action.get(
                            "deadline"
                        )

                        priority = action.get(
                            "priority"
                        )

                        status = action.get(
                            "status"
                        )

                        st.markdown(
                            f"**Task:** {task}"
                        )

                        st.write(
                            f"Assigned to: "
                            f"{assigned_to or 'Unknown'}"
                        )

                        st.write(
                            f"Deadline: "
                            f"{deadline or 'Not specified'}"
                        )

                        st.write(
                            f"Priority: "
                            f"{priority or 'Not specified'}"
                        )

                        st.write(
                            f"Status: "
                            f"{status or 'Pending'}"
                        )

                        st.divider()

                else:

                    st.info(
                        "No action items."
                    )

                # Deadlines
                st.subheader(
                    "📅 Deadlines"
                )

                deadlines = meeting.get(
                    "deadlines",
                    []
                )

                if deadlines:

                    for deadline in deadlines:

                        st.markdown(
                            f"- {deadline}"
                        )

                else:

                    st.info(
                        "No deadlines."
                    )

                # Priorities
                st.subheader(
                    "🔥 Priorities"
                )

                priorities = meeting.get(
                    "priorities",
                    []
                )

                if priorities:

                    for priority in priorities:

                        st.markdown(
                            f"- {priority}"
                        )

                else:

                    st.info(
                        "No priorities."
                    )

    except Exception as error:

        st.error(
            f"❌ Could not load meeting history: "
            f"{error}"
        )
# ============================================================
# 9. KNOWLEDGE SEARCH & AI ASSISTANT
# ============================================================

elif selected_page == "🔎 Knowledge Search":

    st.header("🔎 Knowledge Search & AI Assistant")

    st.write(
        "Ask questions about previously processed meetings "
        "using semantic search and RAG."
    )

    st.divider()

    # --------------------------------------------------------
    # QUESTION INPUT
    # --------------------------------------------------------

    question = st.text_area(
        "🤖 Ask a question about your meetings",
        placeholder=(
            "Example: Which meeting discussed database migration?"
        ),
        height=100,
        key="knowledge_question"
    )

    ask_button = st.button(
        "🤖 Ask AI Assistant",
        type="primary",
        key="knowledge_ask_button"
    )

    # --------------------------------------------------------
    # PROCESS QUESTION
    # --------------------------------------------------------

    if ask_button:

        if not question.strip():

            st.warning(
                "⚠️ Please enter a question first."
            )

        elif not backend_available:

            st.error(
                "❌ AI backend is not available."
            )

        else:

            with st.spinner(
                "🤖 Searching meetings and generating answer..."
            ):

                try:

                    response = requests.post(
                        f"{BACKEND_URL}/rag-question",
                        json={
                            "question": question.strip()
                        },
                        timeout=120
                    )

                    # ----------------------------------------
                    # API ERROR
                    # ----------------------------------------

                    if response.status_code != 200:

                        try:

                            error_data = response.json()

                            error_message = error_data.get(
                                "detail",
                                "Unknown API error."
                            )

                        except Exception:

                            error_message = (
                                "The AI service returned an error."
                            )

                        st.error(
                            f"❌ {error_message}"
                        )

                    else:

                        result = response.json().get(
                            "data",
                            {}
                        )

                        # ------------------------------------
                        # ANSWER
                        # ------------------------------------

                        answer = result.get(
                            "answer",
                            "No answer was generated."
                        )

                        st.subheader(
                            "🤖 AI Answer"
                        )

                        st.success(
                            answer
                        )

                        # ------------------------------------
                        # SOURCES
                        # ------------------------------------

                        sources = result.get(
                            "sources",
                            []
                        )

                        if sources:

                            st.subheader(
                                "📚 Source Meetings"
                            )

                            # Remove duplicate meeting IDs
                            unique_sources = []

                            seen_meetings = set()

                            for source in sources:

                                meeting_id = source.get(
                                    "meeting_id"
                                )

                                if meeting_id in seen_meetings:
                                    continue

                                seen_meetings.add(
                                    meeting_id
                                )

                                unique_sources.append(
                                    source
                                )

                            # --------------------------------
                            # DISPLAY SOURCES
                            # --------------------------------

                            for source in unique_sources:

                                meeting_id = source.get(
                                    "meeting_id",
                                    "Unknown"
                                )

                                content = source.get(
                                    "content",
                                    "No context available."
                                )

                                meeting_date = "Unknown"

                                # Get meeting date from database
                                try:

                                    if meeting_id != "Unknown":

                                        meeting = get_full_meeting(
                                            int(meeting_id)
                                        )

                                        if meeting:

                                           meeting_date = (
    meeting.get("created_at")
    or meeting.get("date")
    or meeting.get("meeting_date")
    or "Date unavailable"
)

                                except Exception:

                                    meeting_date = "Unknown"

                                with st.container(
                                    border=True
                                ):

                                    st.markdown(
                                        f"### 📌 Meeting #{meeting_id}"
                                    )

                                    st.caption(
                                        f"📅 Meeting Date: "
                                        f"{meeting_date}"
                                    )

                                    st.write(
                                        content
                                    )

                        else:

                            st.info(
                                "📭 No source meetings were retrieved."
                            )

                        # ------------------------------------
                        # RETRIEVED CONTEXT
                        # ------------------------------------

                        if sources:

                            with st.expander(
                                "🔍 View Retrieved Context"
                            ):

                                for index, source in enumerate(
                                    sources,
                                    start=1
                                ):

                                    st.markdown(
                                        f"**Source {index} — "
                                        f"Meeting "
                                        f"{source.get('meeting_id', 'Unknown')}**"
                                    )

                                    st.write(
                                        source.get(
                                            "content",
                                            "No context available."
                                        )

                                    )

                                    st.divider()

                except requests.exceptions.Timeout:

                    st.error(
                        "⏱️ The AI request timed out. "
                        "Please try again."
                    )

                except requests.exceptions.ConnectionError:

                    st.error(
                        "🔌 Could not connect to the AI backend."
                    )

                except requests.exceptions.RequestException as error:

                    st.error(
                        f"❌ AI request failed: {error}"
                    )

                except Exception as error:

                    st.error(
                        f"❌ Unexpected error: {error}"
                    )

# ============================================================
# 10. ZOOM INTEGRATION
# ============================================================
elif selected_page == "🎥 Zoom Integration":

    st.header("🎥 Zoom Integration")
    st.write("Select a local meeting recording and generate its transcript.")

    # Find recordings already saved in the uploads folder
    if not os.path.isdir(UPLOAD_FOLDER):
        st.error("Uploads folder was not found.")
    else:
        recording_files = sorted([
            filename
            for filename in os.listdir(UPLOAD_FOLDER)
            if os.path.isfile(os.path.join(UPLOAD_FOLDER, filename))
            and filename.lower().endswith(
                (".mp3", ".wav", ".m4a", ".aac", ".flac",
                 ".mp4", ".mov", ".avi", ".mkv")
            )
        ])

        if not recording_files:
            st.warning("No local recordings found in the uploads folder.")
            st.info("Upload a recording first in Generate Transcript.")
        else:
            selected_recording = st.selectbox(
                "Choose a meeting recording",
                recording_files,
                key="zoom_local_recording"
            )

            file_path = os.path.join(UPLOAD_FOLDER, selected_recording)

            if st.button(
                "🎙️ Generate Transcript from Recording",
                type="primary",
                key="zoom_local_transcribe"
            ):
                try:
                    with st.spinner("Loading Whisper model..."):
                        model = load_whisper_model()

                    with st.spinner("Transcribing meeting recording..."):
                        result = model.transcribe(file_path, fp16=False)

                    transcript = result["text"].strip()

                    if not transcript:
                        st.warning("No speech was detected in this recording.")
                    else:
                        st.session_state["transcript"] = transcript
                        st.session_state["transcript_filename"] = selected_recording
                        st.session_state["meeting_data"] = {}
                        st.session_state["meeting_id"] = None
                        st.session_state["analysis_done"] = False
                        st.session_state["accuracy_result"] = None

                        
                    # Run AI meeting analysis
                    with st.spinner("Analyzing meeting with AI..."):
                        meeting_result = process_transcript(transcript)

                    # Convert result to a dictionary
                    if hasattr(meeting_result, "model_dump"):
                        meeting_result = meeting_result.model_dump()
                    elif hasattr(meeting_result, "dict"):
                        meeting_result = meeting_result.dict()

                    # Save meeting to database
                    with st.spinner("Saving meeting to database..."):
                        meeting_id = save_meeting(
                            intelligence=meeting_result,
                            transcript=transcript,
                            filename=selected_recording
                        )

                    st.session_state["transcript"] = transcript
                    st.session_state["transcript_filename"] = selected_recording
                    st.session_state["meeting_data"] = meeting_result
                    st.session_state["meeting_id"] = meeting_id
                    st.session_state["analysis_done"] = True
                    st.session_state["accuracy_result"] = None

                    st.success("Transcript and meeting analysis generated successfully!")
                    st.success(f"Meeting saved to database. Meeting ID: {meeting_id}")

                    st.subheader("Meeting Transcript")
                    st.text_area(
                        "Transcript",
                        value=transcript,
                        height=350,
                        key="zoom_generated_transcript"
                    )

                    st.subheader("Meeting Intelligence")
                    st.json(meeting_result)

                    st.download_button(
                        "Download Transcript",
                        data=transcript,
                        file_name=f"{os.path.splitext(selected_recording)[0]}_transcript.txt",
                        mime="text/plain"
                    )
                except Exception as error:
                    st.error(f"Could not transcribe recording: {error}")