import os
import json
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

APP_NAME = "DigiPlus"

LOG_DIR = BASE_DIR / "logs"
LOG_FILE = LOG_DIR / "app.log"

FIREBASE_CREDENTIALS = BASE_DIR / "serviceAccountKey.json"


def get_secret(key):
    """Read secrets from environment or Streamlit secrets."""

    value = os.getenv(key)

    if value:
        return value

    # Local Streamlit secrets
    try:
        import streamlit as st
        value = st.secrets.get(key)
        if value:
            return value
    except Exception:
        pass

    return None

GEMINI_API_KEY = get_secret("GEMINI_API_KEY")


def get_firebase_credentials():
    """Load Firebase service account credentials."""

    if FIREBASE_CREDENTIALS.exists():
        with open(FIREBASE_CREDENTIALS, "r", encoding="utf-8") as file:
            return json.load(file)

    # Deployment credentials will be configured later.
    raw_credentials = get_secret("FIREBASE_SERVICE_ACCOUNT")

    if raw_credentials:
        return json.loads(raw_credentials)

    raise FileNotFoundError(
        "Firebase credentials not found. "
        "Place serviceAccountKey.json in the project root."
    )