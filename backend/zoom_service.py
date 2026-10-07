import os
from pathlib import Path

import requests
from dotenv import load_dotenv


# Project root folder
BASE_DIR = Path(__file__).resolve().parent.parent

# Load the .env file from the project root
ENV_FILE = BASE_DIR / ".env"
load_dotenv(ENV_FILE)


def get_zoom_access_token():
    """Get an access token using Zoom Server-to-Server OAuth."""

    account_id = os.getenv("ZOOM_ACCOUNT_ID")
    client_id = os.getenv("ZOOM_CLIENT_ID")
    client_secret = os.getenv("ZOOM_CLIENT_SECRET")

    if not account_id:
        raise ValueError("ZOOM_ACCOUNT_ID is missing from .env")

    if not client_id:
        raise ValueError("ZOOM_CLIENT_ID is missing from .env")

    if not client_secret:
        raise ValueError("ZOOM_CLIENT_SECRET is missing from .env")

    response = requests.post(
        "https://zoom.us/oauth/token",
        params={
            "grant_type": "account_credentials",
            "account_id": account_id,
        },
        auth=(client_id, client_secret),
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    return data["access_token"]
def get_zoom_meetings():
    """Get meetings from the Zoom account."""

    access_token = get_zoom_access_token()

    response = requests.get(
        "https://api.zoom.us/v2/users/me/meetings",
        headers={
            "Authorization": f"Bearer {access_token}"
        },
        params={
            "type": "scheduled",
            "page_size": 30,
        },
        timeout=30,
    )

    response.raise_for_status()

    return response.json()

def get_zoom_transcript(meeting_id: str):
    """Get recording metadata for a specific Zoom meeting."""
    access_token = get_zoom_access_token()

    response = requests.get(
        f"https://api.zoom.us/v2/meetings/{meeting_id}/recordings",
        headers={
            "Authorization": f"Bearer {access_token}"
        },
        timeout=30,
    )

    response.raise_for_status()
    data = response.json()

    # Return only transcript-related recording files.
    transcript_files = [
        recording
        for recording in data.get("recording_files", [])
        if recording.get("file_type") == "TRANSCRIPT"
        or recording.get("file_extension", "").upper() == "VTT"
    ]

    return {
        "meeting_id": meeting_id,
        "transcript_files": transcript_files,
    }
def get_zoom_recordings():
    access_token = get_zoom_access_token()

    response = requests.get(
        "https://api.zoom.us/v2/users/me/recordings",
        headers={
            "Authorization": f"Bearer {access_token}"
        },
        timeout=30,
    )

    response.raise_for_status()

    return response.json()
def download_zoom_recording(download_url: str, output_path: str):
    access_token = get_zoom_access_token()

    response = requests.get(
        download_url,
        headers={
            "Authorization": f"Bearer {access_token}"
        },
        stream=True,
        timeout=60,
    )

    response.raise_for_status()

    with open(output_path, "wb") as file:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                file.write(chunk)

    return output_path