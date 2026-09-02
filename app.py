import os
import re

import streamlit as st
import whisper
import jiwer

from transformers import AutoTokenizer, AutoModelForSeq2SeqLM


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Meeting Transcription System",
    page_icon="🎙️",
    layout="wide"
)


# ============================================================
# FOLDER CONFIGURATION
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

UPLOAD_FOLDER = os.path.join(
    BASE_DIR,
    "uploads"
)

TRANSCRIPT_FOLDER = os.path.join(
    BASE_DIR,
    "transcripts"
)

SUMMARY_FOLDER = os.path.join(
    BASE_DIR,
    "summaries"
)


# Create folders automatically
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(TRANSCRIPT_FOLDER, exist_ok=True)
os.makedirs(SUMMARY_FOLDER, exist_ok=True)


# ============================================================
# SUPPORTED FILES
# ============================================================

SUPPORTED_FILES = [
    "mp3",
    "wav",
    "m4a",
    "aac",
    "flac",
    "mp4",
    "mov",
    "avi",
    "mkv"
]

MAX_FILE_SIZE_MB = 200


# ============================================================
# SESSION STATE INITIALIZATION
# ============================================================

if "transcript" not in st.session_state:
    st.session_state["transcript"] = ""

if "base_name" not in st.session_state:
    st.session_state["base_name"] = ""

if "summary" not in st.session_state:
    st.session_state["summary"] = ""

if "summary_bullets" not in st.session_state:
    st.session_state["summary_bullets"] = []

if "uploaded_file_name" not in st.session_state:
    st.session_state["uploaded_file_name"] = ""

if "accuracy_results" not in st.session_state:
    st.session_state["accuracy_results"] = None


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    .main-title {
        text-align: center;
        font-size: 42px;
        font-weight: 700;
        margin-bottom: 10px;
    }

    .subtitle {
        text-align: center;
        font-size: 18px;
        margin-bottom: 30px;
    }

    .summary-box {
        padding: 20px;
        border-radius: 10px;
        background-color: #f4f6fa;
        margin-bottom: 15px;
    }

    .metric-title {
        font-size: 18px;
        font-weight: 600;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# TITLE
# ============================================================

st.markdown(
    '<div class="main-title">🎙️ Meeting Transcription System</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'Upload an audio or video meeting recording to generate a transcript, '
    'overall meeting summary, and transcription accuracy.'
    '</div>',
    unsafe_allow_html=True
)


# ============================================================
# PROJECT INFORMATION
# ============================================================

st.info(
    "🎵 **Audio:** MP3, WAV, M4A, AAC, FLAC\n\n"
    "🎬 **Video:** MP4, MOV, AVI, MKV\n\n"
    "📦 **Maximum file size:** 200 MB"
)


# ============================================================
# LOAD WHISPER MODEL
# ============================================================

@st.cache_resource
def load_whisper_model():

    model = whisper.load_model("base")

    return model


# ============================================================
# LOAD SUMMARY MODEL
# ============================================================

@st.cache_resource
def load_summary_model():

    model_name = "facebook/bart-large-cnn"

    tokenizer = AutoTokenizer.from_pretrained(
        model_name
    )

    model = AutoModelForSeq2SeqLM.from_pretrained(
        model_name
    )

    return tokenizer, model


# ============================================================
# CLEAN TEXT
# ============================================================

def clean_text(text):

    if not text:
        return ""

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# ============================================================
# SPLIT TEXT INTO CHUNKS
# ============================================================

def split_into_chunks(text, chunk_size=400):

    words = text.split()

    chunks = []

    for i in range(
        0,
        len(words),
        chunk_size
    ):

        chunk = " ".join(
            words[i:i + chunk_size]
        )

        if chunk.strip():

            chunks.append(
                chunk.strip()
            )

    return chunks


# ============================================================
# SUMMARIZE ONE CHUNK
# ============================================================

def summarize_chunk(
    text,
    tokenizer,
    model
):

    inputs = tokenizer(
        text,
        return_tensors="pt",
        max_length=1024,
        truncation=True
    )

    summary_ids = model.generate(
        inputs["input_ids"],
        attention_mask=inputs["attention_mask"],
        max_length=100,
        min_length=20,
        num_beams=4,
        length_penalty=1.2,
        early_stopping=True
    )

    summary = tokenizer.decode(
        summary_ids[0],
        skip_special_tokens=True
    )

    return summary.strip()


# ============================================================
# OVERALL SUMMARY FUNCTION
# ============================================================

def summarize_text(text):

    if not text or not text.strip():

        return None

    text = clean_text(text)

    tokenizer, model = load_summary_model()

    # --------------------------------------------------------
    # Split transcript
    # --------------------------------------------------------

    chunks = split_into_chunks(
        text,
        chunk_size=400
    )

    if not chunks:

        return None

    # --------------------------------------------------------
    # Generate summaries for chunks
    # --------------------------------------------------------

    partial_summaries = []

    for chunk in chunks:

        summary = summarize_chunk(
            chunk,
            tokenizer,
            model
        )

        if summary:

            partial_summaries.append(
                summary
            )

    if not partial_summaries:

        return None

    # --------------------------------------------------------
    # If transcript is short
    # --------------------------------------------------------

    if len(partial_summaries) == 1:

        final_summary = partial_summaries[0]

    else:

        # Combine chunk summaries
        combined = " ".join(
            partial_summaries
        )

        # Generate final overall summary
        inputs = tokenizer(
            combined,
            return_tensors="pt",
            max_length=1024,
            truncation=True
        )

        summary_ids = model.generate(
            inputs["input_ids"],
            attention_mask=inputs["attention_mask"],
            max_length=130,
            min_length=35,
            num_beams=4,
            length_penalty=1.2,
            early_stopping=True
        )

        final_summary = tokenizer.decode(
            summary_ids[0],
            skip_special_tokens=True
        )

    return final_summary.strip()


# ============================================================
# CONVERT SUMMARY INTO BULLET POINTS
# ============================================================

def make_bullets(summary):

    if not summary:

        return []

    summary = clean_text(
        summary
    )

    # Split into sentences
    sentences = re.split(
        r"(?<=[.!?])\s+",
        summary
    )

    sentences = [
        sentence.strip()
        for sentence in sentences
        if sentence.strip()
    ]

    # Maximum 3 overall points
    bullets = sentences[:3]

    return bullets


# ============================================================
# NORMALIZE TEXT FOR ACCURACY TESTING
# ============================================================

def normalize_for_accuracy(text):

    text = text.lower()

    text = re.sub(
        r"[^\w\s]",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# ============================================================
# APPLICATION TABS
# ============================================================

tab_upload, tab_transcript, tab_summary, tab_accuracy = st.tabs(
    [
        "📂 Upload",
        "📝 Transcript",
        "📋 Overall Summary",
        "📊 Accuracy Testing"
    ]
)


# ============================================================
# TAB 1 - UPLOAD
# ============================================================

with tab_upload:

    st.header(
        "📂 Upload Meeting Recording"
    )

    uploaded_file = st.file_uploader(
        "Choose an audio or video file",
        type=SUPPORTED_FILES
    )

    if uploaded_file is not None:

        file_extension = (
            uploaded_file.name
            .split(".")[-1]
            .lower()
        )

        file_size_mb = (
            uploaded_file.size /
            (1024 * 1024)
        )

        # ----------------------------------------------------
        # Validate file
        # ----------------------------------------------------

        if file_extension not in SUPPORTED_FILES:

            st.error(
                "❌ Unsupported file format."
            )

            st.stop()

        if file_size_mb > MAX_FILE_SIZE_MB:

            st.error(
                f"❌ File is too large. "
                f"Maximum size is {MAX_FILE_SIZE_MB} MB."
            )

            st.stop()

        # ----------------------------------------------------
        # Display file information
        # ----------------------------------------------------

        st.success(
            "📁 File uploaded successfully!"
        )

        st.write(
            "**File name:**",
            uploaded_file.name
        )

        st.write(
            "**File size:**",
            f"{file_size_mb:.2f} MB"
        )

        st.write(
            "**File format:**",
            file_extension.upper()
        )

        # ----------------------------------------------------
        # Save uploaded file
        # ----------------------------------------------------

        safe_filename = os.path.basename(
            uploaded_file.name
        )

        file_path = os.path.join(
            UPLOAD_FOLDER,
            safe_filename
        )

        with open(
            file_path,
            "wb"
        ) as f:

            f.write(
                uploaded_file.getbuffer()
            )

        st.session_state[
            "uploaded_file_name"
        ] = uploaded_file.name

        st.session_state[
            "base_name"
        ] = os.path.splitext(
            uploaded_file.name
        )[0]

        # ----------------------------------------------------
        # Transcribe button
        # ----------------------------------------------------

        if st.button(
            "🎙️ Transcribe Recording",
            type="primary"
        ):

            try:

                # --------------------------------------------
                # Load Whisper
                # --------------------------------------------

                with st.spinner(
                    "🔄 Loading Whisper speech recognition model..."
                ):

                    whisper_model = (
                        load_whisper_model()
                    )

                # --------------------------------------------
                # Transcription
                # --------------------------------------------

                with st.spinner(
                    "🎧 Processing recording and generating transcript..."
                ):

                    result = whisper_model.transcribe(
                        file_path,
                        fp16=False
                    )

                transcript = clean_text(
                    result.get(
                        "text",
                        ""
                    )
                )

                # --------------------------------------------
                # Validate transcript
                # --------------------------------------------

                if not transcript:

                    st.error(
                        "❌ Transcript is empty. "
                        "Please check the recording."
                    )

                else:

                    # ----------------------------------------
                    # Save transcript in session state
                    # ----------------------------------------

                    st.session_state[
                        "transcript"
                    ] = transcript

                    st.session_state[
                        "summary"
                    ] = ""

                    st.session_state[
                        "summary_bullets"
                    ] = []

                    st.session_state[
                        "accuracy_results"
                    ] = None

                    # ----------------------------------------
                    # Save transcript to file
                    # ----------------------------------------

                    base_name = st.session_state[
                        "base_name"
                    ]

                    transcript_path = os.path.join(
                        TRANSCRIPT_FOLDER,
                        base_name +
                        "_transcript.txt"
                    )

                    with open(
                        transcript_path,
                        "w",
                        encoding="utf-8"
                    ) as f:

                        f.write(
                            transcript
                        )

                    st.success(
                        "✅ Transcription completed successfully!"
                    )

                    st.info(
                        "📝 Your transcript is available in the "
                        "'Transcript' tab."
                    )

            except Exception as e:

                st.error(
                    f"❌ Transcription failed: {e}"
                )


# ============================================================
# TAB 2 - TRANSCRIPT
# ============================================================

with tab_transcript:

    st.header(
        "📝 Generated Transcript"
    )

    transcript = st.session_state.get(
        "transcript",
        ""
    )

    if transcript:

        st.success(
            "✅ Transcript generated successfully!"
        )

        st.text_area(
            "Full Transcript",
            transcript,
            height=400
        )

        # ----------------------------------------------------
        # Download transcript
        # ----------------------------------------------------

        base_name = st.session_state.get(
            "base_name",
            "meeting"
        )

        st.download_button(
            label="📥 Download Transcript",
            data=transcript,
            file_name=(
                base_name +
                "_transcript.txt"
            ),
            mime="text/plain"
        )

    else:

        st.info(
            "📂 Please upload and transcribe a recording "
            "from the Upload tab first."
        )


# ============================================================
# TAB 3 - OVERALL MEETING SUMMARY
# ============================================================

with tab_summary:

    st.header(
        "📋 Overall Meeting Summary"
    )

    transcript = st.session_state.get(
        "transcript",
        ""
    )

    if not transcript:

        st.info(
            "📝 Please generate a transcript first."
        )

    else:

        st.write(
            "The system analyzes the complete generated transcript "
            "and produces an overall summary containing the main "
            "discussion points."
        )

        if st.button(
            "🧠 Generate Overall Summary",
            type="primary"
        ):

            try:

                with st.spinner(
                    "🧠 Analyzing the complete meeting transcript..."
                ):

                    summary = summarize_text(
                        transcript
                    )

                if not summary:

                    st.error(
                        "❌ Could not generate the overall summary."
                    )

                else:

                    bullets = make_bullets(
                        summary
                    )

                    st.session_state[
                        "summary"
                    ] = summary

                    st.session_state[
                        "summary_bullets"
                    ] = bullets

                    # ----------------------------------------
                    # Save summary
                    # ----------------------------------------

                    base_name = st.session_state.get(
                        "base_name",
                        "meeting"
                    )

                    summary_path = os.path.join(
                        SUMMARY_FOLDER,
                        base_name +
                        "_summary.txt"
                    )

                    summary_text = (
                        "Overall Meeting Summary\n\n"
                        +
                        "\n".join(
                            "- " + bullet
                            for bullet in bullets
                        )
                    )

                    with open(
                        summary_path,
                        "w",
                        encoding="utf-8"
                    ) as f:

                        f.write(
                            summary_text
                        )

                    st.success(
                        "✅ Overall meeting summary generated!"
                    )

            except Exception as e:

                st.error(
                    f"❌ Summary generation failed: {e}"
                )

        # ----------------------------------------------------
        # Display saved summary
        # ----------------------------------------------------

        bullets = st.session_state.get(
            "summary_bullets",
            []
        )

        if bullets:

            st.markdown(
                "### 📋 Overall Meeting Summary"
            )

            for bullet in bullets:

                st.markdown(
                    f"- {bullet}"
                )

            # ------------------------------------------------
            # Download summary
            # ------------------------------------------------

            base_name = st.session_state.get(
                "base_name",
                "meeting"
            )

            summary_text = (
                "Overall Meeting Summary\n\n"
                +
                "\n".join(
                    "- " + bullet
                    for bullet in bullets
                )
            )

            st.download_button(
                label="📥 Download Summary",
                data=summary_text,
                file_name=(
                    base_name +
                    "_summary.txt"
                ),
                mime="text/plain"
            )


# ============================================================
# TAB 4 - ACCURACY TESTING
# ============================================================

with tab_accuracy:

    st.header(
        "📊 Accuracy Testing"
    )

    st.write(
        "Compare the generated Whisper transcript with a correct "
        "reference transcript to evaluate transcription performance."
    )

    generated_text = st.session_state.get(
        "transcript",
        ""
    )

    # --------------------------------------------------------
    # Reference transcript
    # --------------------------------------------------------

    reference_text = st.text_area(
        "📝 Enter the Correct / Reference Transcript",
        height=220,
        placeholder=(
            "Paste the correct transcript here..."
        ),
        key="reference_transcript"
    )

    # --------------------------------------------------------
    # Calculate accuracy
    # --------------------------------------------------------

    if st.button(
        "📊 Calculate Accuracy",
        type="primary"
    ):

        if not generated_text.strip():

            st.warning(
                "⚠️ Please generate the transcript first."
            )

        elif not reference_text.strip():

            st.warning(
                "⚠️ Please enter the correct/reference transcript."
            )

        else:

            try:

                # --------------------------------------------
                # Normalize both transcripts
                # --------------------------------------------

                reference = normalize_for_accuracy(
                    reference_text
                )

                hypothesis = normalize_for_accuracy(
                    generated_text
                )

                # --------------------------------------------
                # Calculate WER
                # --------------------------------------------

                wer_score = jiwer.wer(
                    reference,
                    hypothesis
                )

                # --------------------------------------------
                # Calculate CER
                # --------------------------------------------

                cer_score = jiwer.cer(
                    reference,
                    hypothesis
                )

                # --------------------------------------------
                # Word Accuracy
                # --------------------------------------------

                word_accuracy = max(
                    0,
                    (1 - wer_score) * 100
                )

                # --------------------------------------------
                # Save results in session
                # --------------------------------------------

                st.session_state[
                    "accuracy_results"
                ] = {
                    "word_accuracy": word_accuracy,
                    "wer": wer_score * 100,
                    "cer": cer_score * 100,
                    "reference": reference_text.strip(),
                    "generated": generated_text.strip()
                }

            except Exception as e:

                st.error(
                    f"❌ Accuracy calculation failed: {e}"
                )


    # ========================================================
    # DISPLAY ACCURACY RESULTS
    # ========================================================

    results = st.session_state.get(
        "accuracy_results"
    )

    if results:

        st.divider()

        st.subheader(
            "📊 Accuracy Test Results"
        )

        # ----------------------------------------------------
        # Metrics
        # ----------------------------------------------------

        col1, col2, col3 = st.columns(3)

        with col1:

            st.metric(
                "Word Accuracy",
                f"{results['word_accuracy']:.2f}%"
            )

        with col2:

            st.metric(
                "Word Error Rate",
                f"{results['wer']:.2f}%"
            )

        with col3:

            st.metric(
                "Character Error Rate",
                f"{results['cer']:.2f}%"
            )

        # ----------------------------------------------------
        # Accuracy interpretation
        # ----------------------------------------------------

        if results["word_accuracy"] >= 90:

            st.success(
                "✅ Excellent transcription accuracy."
            )

        elif results["word_accuracy"] >= 75:

            st.info(
                "ℹ️ Good transcription accuracy, "
                "but some errors are present."
            )

        else:

            st.warning(
                "⚠️ Transcription accuracy is below 75%. "
                "Consider improving the recording quality "
                "or using a larger Whisper model."
            )

        # ====================================================
        # TRANSCRIPT COMPARISON
        # ====================================================

        st.divider()

        st.subheader(
            "🔍 Transcript Comparison"
        )

        comparison_col1, comparison_col2 = st.columns(2)

        with comparison_col1:

            st.markdown(
                "### 📘 Reference Transcript"
            )

            st.text_area(
                "Correct / Reference",
                results["reference"],
                height=350,
                key="reference_comparison"
            )

        with comparison_col2:

            st.markdown(
                "### 🎙️ Generated Transcript"
            )

            st.text_area(
                "Whisper Generated",
                results["generated"],
                height=350,
                key="generated_comparison"
            )

        # ----------------------------------------------------
        # Explain metrics
        # ----------------------------------------------------

        st.divider()

        st.markdown(
            "### 📖 What do these values mean?"
        )

        st.write(
            "**Word Accuracy:** Percentage of words correctly "
            "recognized based on the Word Error Rate."
        )

        st.write(
            "**Word Error Rate (WER):** Measures word-level "
            "errors such as substitutions, deletions, and insertions. "
            "Lower WER is better."
        )

        st.write(
            "**Character Error Rate (CER):** Measures errors "
            "at the character level. Lower CER is better."
        )

else_message = None