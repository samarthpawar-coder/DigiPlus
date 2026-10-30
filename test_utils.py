from utils.logger import log_event, new_request_id
from utils.validation import (
    validate_required,
    validate_status,
    validate_participants
)

print("\n===== DIGIPLUS UTILITY TEST =====")

# Test logging
request_id = new_request_id()

log_event(
    "DigiPlus utility test started",
    request_id=request_id
)

print("SUCCESS: Request ID generated:", request_id)

# Test required field
print(
    "SUCCESS:",
    validate_required("Project Meeting", "Title")
)

# Test status
print(
    "SUCCESS:",
    validate_status("Pending")
)

# Test participants
print(
    "SUCCESS:",
    validate_participants(["Rahul", "Priya"])
)

print("\n===== TEST COMPLETED =====")