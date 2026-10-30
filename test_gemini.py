from config import GEMINI_API_KEY
from modules.ai_engine import generate_response

print("Checking Gemini configuration...")

if not GEMINI_API_KEY:
    print("ERROR: API key not detected.")
else:
    print("API key detected successfully.")

    try:
        response = generate_response(
            "Reply with exactly: DigiPlus AI Connected"
        )

        print("\nGemini response:")
        print(response)

        print("\nSUCCESS: Gemini is working!")

    except Exception as e:
        print("\nGEMINI ERROR:", str(e))