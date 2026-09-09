import os
import requests
import streamlit as st
import whisper
from backend.database import get_meeting_history, get_full_meeting


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
        "🎙️ Generate Transcript",
        "🧠 Meeting Intelligence",
        "✅ Decisions",
        "👥 Participants & Responsibilities",
        "📅 Deadlines",
        "🔥 Priorities",
        "🎯 Transcription Accuracy Testing",
         "📚 Meeting History"
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
# 1. GENERATE TRANSCRIPT
# ============================================================

if selected_page == "🎙️ Generate Transcript":

    st.header(
        "1. Generate Transcript"
    )

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

        extension = (
            uploaded_file.name
            .split(".")[-1]
            .lower()
        )

        size_mb = (
            uploaded_file.size
            / (1024 * 1024)
        )

        if size_mb > MAX_FILE_SIZE_MB:

            st.error(
                f"❌ File is too large. "
                f"Maximum allowed size is "
                f"{MAX_FILE_SIZE_MB} MB."
            )

            st.stop()

        # New recording clears previous meeting results.
        if (
            st.session_state["transcript_filename"]
            and
            st.session_state["transcript_filename"]
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

            st.write(
                "**File:**",
                uploaded_file.name
            )

        with col2:

            st.write(
                "**Size:**",
                f"{size_mb:.2f} MB"
            )

        with col3:

            st.write(
                "**Type:**",
                extension.upper()
            )

        file_path = os.path.join(
            UPLOAD_FOLDER,
            uploaded_file.name
        )

        with open(
            file_path,
            "wb"
        ) as file:

            file.write(
                uploaded_file.getbuffer()
            )

        st.success(
            "📁 File uploaded successfully!"
        )

        if st.button(
            "🎙️ Generate Transcript",
            type="primary",
            use_container_width=True
        ):

            try:

                with st.spinner(
                    "🔄 Loading Whisper model..."
                ):

                    model = load_whisper_model()

                with st.spinner(
                    "🎧 Processing recording and generating transcript..."
                ):

                    result = model.transcribe(
                        file_path,
                        fp16=False
                    )

                transcript = (
                    result["text"]
                    .strip()
                )

                if not transcript:

                    st.error(
                        "❌ Transcript is empty."
                    )

                    st.stop()

                st.session_state[
                    "transcript"
                ] = transcript

                st.session_state[
                    "transcript_filename"
                ] = uploaded_file.name

                st.session_state[
                    "meeting_data"
                ] = {}

                st.session_state[
                    "meeting_id"
                ] = None

                st.session_state[
                    "analysis_done"
                ] = False

                st.session_state[
                    "accuracy_result"
                ] = None

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

                    file.write(
                        transcript
                    )

                st.success(
                    "✅ Transcript generated successfully!"
                )

            except Exception as error:

                st.error(
                    f"❌ Transcription failed: {error}"
                )


    # Show generated transcript only on this page.
    if st.session_state["transcript"]:

        st.divider()

        st.subheader(
            "📄 Generated Text"
        )

        st.text_area(
            "Whisper Generated Transcript",
            st.session_state["transcript"],
            height=300
        )

        base_name = os.path.splitext(
            st.session_state[
                "transcript_filename"
            ]
        )[0]

        st.download_button(
            "📥 Download Transcript",
            st.session_state["transcript"],
            file_name=(
                f"{base_name}_transcript.txt"
            ),
            mime="text/plain",
            use_container_width=True
        )


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

                name = participant.get(
                    "name",
                    "Unknown"
                )

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
