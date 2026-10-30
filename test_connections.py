from datetime import datetime, timezone

from database.firebase_db import (
    get_db,
    create_document,
    get_document,
    delete_document
)

from modules.ai_engine import generate_response


print("\n========== DIGIPLUS CONNECTION TEST ==========\n")


# TEST 1: FIREBASE

try:
    print("[1] Connecting to Firebase...")

    db = get_db()

    test_id = "connection_test"

    test_data = {
        "application": "DigiPlus",
        "status": "Connected",
        "tested_at": datetime.now(timezone.utc).isoformat()
    }

    create_document(
        "system_tests",
        test_id,
        test_data
    )

    retrieved = get_document(
        "system_tests",
        test_id
    )

    if retrieved and retrieved["status"] == "Connected":
        print("SUCCESS: Firebase write/read working!")

    else:
        raise Exception("Firebase read verification failed.")

    delete_document("system_tests", test_id)

    print("SUCCESS: Test document cleaned up!")

except Exception as e:
    print("FIREBASE ERROR:", str(e))


# TEST 2: GEMINI

try:
    print("\n[2] Connecting to Gemini AI...")

    response = generate_response(
        "Reply with exactly this text: DigiPlus AI Connected"
    )

    print("Gemini response:", response)

    print("SUCCESS: Gemini API working!")

except Exception as e:
    print("GEMINI ERROR:", str(e))


print("\n========== TEST COMPLETED ==========\n")