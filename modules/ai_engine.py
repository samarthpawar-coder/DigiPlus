import json
from google import genai

from config import GEMINI_API_KEY , GEMINI_MODEL


MODEL_NAME = "gemini-2.5-flash"


def get_ai_client():
    """Create Gemini client."""

    if not GEMINI_API_KEY:
        raise ValueError(
            "Gemini API key is missing. Check .streamlit/secrets.toml"
        )

    return genai.Client(api_key=GEMINI_API_KEY)


def generate_response(prompt):
    """Generate a response using Gemini."""

    client = get_ai_client()

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt
    )

    if not response.text:
        raise ValueError("Gemini returned an empty response.")

    return response.text


def generate_meeting_recap(notes):
    """Convert raw meeting notes into structured information."""

    prompt = f"""
You are an intelligent meeting assistant.

Analyze the following meeting notes.

Return ONLY valid JSON with this structure:

{{
    "summary": "Short meeting summary",
    "decisions": [
        "Decision 1"
    ],
    "action_items": [
        {{
            "title": "Task description",
            "owner": null,
            "due_date": null,
            "status": "Pending"
        }}
    ]
}}

Rules:
- Do not invent missing owners.
- Do not invent deadlines.
- Use YYYY-MM-DD for explicit dates.
- Keep unassigned owners as null.
- Extract only actual decisions and action items.
- If no action items exist, return an empty array.

Meeting notes:

{notes}
"""

    result = generate_response(prompt)

    # Extract JSON safely
    try:
        return json.loads(result)

    except json.JSONDecodeError:
        # Handle models that wrap JSON in Markdown.
        cleaned = result.strip()

        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1]
            cleaned = cleaned.rsplit("```", 1)[0]

        return json.loads(cleaned)


def generate_catchup_brief(meeting_context):
    """Generate an AI-powered meeting catch-up brief."""

    prompt = f"""
You are an intelligent team handover assistant.

Create a concise catch-up brief for someone who missed a meeting.

Include:
1. What happened?
2. Important decisions.
3. Pending tasks.
4. Task owners and deadlines.
5. What the recipient should do next.

Use clear and professional language.

Meeting context:

{meeting_context}
"""

    return generate_response(prompt)