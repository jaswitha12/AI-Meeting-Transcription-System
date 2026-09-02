from transformers import pipeline


# Load summarization model
def load_summarizer():
    summarizer = pipeline(
        "summarization",
        model="facebook/bart-large-cnn"
    )
    return summarizer


def generate_summary(transcript):
    """
    Generate an overall summary from the complete transcript.
    """

    if not transcript or not transcript.strip():
        return ""

    # Clean transcript
    transcript = transcript.strip()

    # Load model
    summarizer = load_summarizer()

    # BART has a limited input size.
    # Split long transcripts into chunks.
    words = transcript.split()

    chunk_size = 400

    chunks = []

    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)

    summaries = []

    # Summarize each chunk
    for chunk in chunks:

        if len(chunk.split()) < 30:
            summaries.append(chunk)
            continue

        result = summarizer(
            chunk,
            max_length=120,
            min_length=40,
            do_sample=False
        )

        summaries.append(
            result[0]["summary_text"]
        )

    # If there are multiple chunk summaries,
    # combine them and summarize again.
    combined_summary = " ".join(summaries)

    if len(summaries) > 1:

        final_result = summarizer(
            combined_summary,
            max_length=150,
            min_length=60,
            do_sample=False
        )

        final_summary = final_result[0]["summary_text"]

    else:
        final_summary = combined_summary

    return final_summary