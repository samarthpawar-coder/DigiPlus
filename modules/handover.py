
import streamlit as st
import uuid

from datetime import datetime, timezone

from database.firebase_db import (
    get_collection,
    create_document,
    update_document
)

from utils.logger import log_event, new_request_id
from utils.validation import validate_required
from modules.action_tracker import record_task_history


def generate_handover_brief(source_meeting, target_meeting, tasks):
    """Generate a structured handover brief from saved information."""

    lines = [
        "DIGIPLUS - SMART HANDOVER BRIEF",
        "",
        f"Previous Meeting: {source_meeting.get('title', 'Unknown')}",
        f"Next Meeting: {target_meeting.get('title', 'Unknown')}",
        "",
        "PREVIOUS MEETING SUMMARY:",
        source_meeting.get("summary") or "No AI summary available.",
        "",
        "PREVIOUS MEETING NOTES:",
        source_meeting.get("notes") or "No notes available.",
        "",
        "OPEN ACTION ITEMS:"
    ]

    for index, task in enumerate(tasks, start=1):

        lines.extend([
            f"{index}. {task.get('title', 'Untitled task')}",
            f"   Owner: {task.get('owner') or 'Unassigned'}",
            f"   Due date: {task.get('due_date') or 'Not specified'}",
            f"   Status: {task.get('status', 'Pending')}",
            f"   Outcome: {task.get('outcome') or 'Not recorded'}",
            ""
        ])

    lines.extend([
        "NEXT STEPS:",
        "Review the carried-forward tasks, confirm responsibilities,",
        "and update their progress in DigiPlus."
    ])

    return "\n".join(lines)


def execute_handover(
    source_meeting,
    target_meeting,
    selected_tasks,
    new_owner=None
):
    """Transfer open tasks and preserve their history."""

    if source_meeting == target_meeting:
        raise ValueError("Source and receiving meetings must be different.")

    request_id = new_request_id()

    meetings = get_collection("meetings")
    tasks = get_collection("action_items")

    source = next(
        (
            meeting for meeting in meetings
            if meeting.get("meeting_id", meeting["id"]) == source_meeting
        ),
        None
    )

    target = next(
        (
            meeting for meeting in meetings
            if meeting.get("meeting_id", meeting["id"]) == target_meeting
        ),
        None
    )

    if not source or not target:
        raise ValueError("Source or receiving meeting was not found.")

    if not selected_tasks:
        raise ValueError("Select at least one task to transfer.")

    task_lookup = {
        task.get("task_id", task["id"]): task
        for task in tasks
    }

    selected_records = []

    for task_id in selected_tasks:

        task = task_lookup.get(task_id)

        if not task:
            raise ValueError(f"Task not found: {task_id}")

        if task.get("meeting_id") != source_meeting:
            raise ValueError(
                f"Task {task_id} does not belong to the source meeting."
            )

        if task.get("status") == "Completed":
            raise ValueError("Completed tasks cannot be carried forward.")

        selected_records.append((task_id, task))

    handover_id = str(uuid.uuid4())

    # Generate the brief using existing saved information.
    brief = generate_handover_brief(
        source,
        target,
        [task for _, task in selected_records]
    )

    transferred_tasks = []

    # Update each existing task without creating duplicates.
    for task_id, task in selected_records:

        previous_owner = task.get("owner")

        updates = {
            "meeting_id": target_meeting,
            "last_handover_id": handover_id,
            "last_handover_at": datetime.now(timezone.utc).isoformat()
        }

        if new_owner and new_owner.strip():
            updates["owner"] = new_owner.strip()

        update_document(
            "action_items",
            task_id,
            updates
        )

        details = (
            f"Carried forward from meeting {source_meeting} "
            f"to meeting {target_meeting}."
        )

        if new_owner and new_owner.strip():
            details += (
                f" Reassigned from {previous_owner} "
                f"to {new_owner.strip()}."
            )

        record_task_history(
            task_id,
            "Carried Forward",
            details,
            request_id
        )

        transferred_tasks.append({
            "task_id": task_id,
            "title": task.get("title"),
            "previous_owner": previous_owner,
            "new_owner": (
                new_owner.strip()
                if new_owner and new_owner.strip()
                else previous_owner
            ),
            "previous_status": task.get("status"),
            "due_date": task.get("due_date")
        })

    # Store the handover record.
    handover_data = {
        "handover_id": handover_id,
        "source_meeting_id": source_meeting,
        "target_meeting_id": target_meeting,
        "transferred_tasks": transferred_tasks,
        "brief": brief,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "request_id": request_id
    }

    create_document(
        "handover_briefs",
        handover_id,
        handover_data
    )

    log_event(
        f"Handover completed: {handover_id}",
        request_id=request_id
    )

    return handover_id, brief


def show_handover():

    st.title("🔄 Smart Handover")

    st.caption(
        "Transfer responsibilities, carry forward open tasks "
        "and preserve meeting context."
    )

    tab1, tab2 = st.tabs([
        "Create Handover",
        "Handover History"
    ])

    # ==================================
    # TAB 1: CREATE HANDOVER
    # ==================================

    with tab1:

        try:

            meetings = get_collection("meetings")
            tasks = get_collection("action_items")

            if len(meetings) < 2:

                st.warning(
                    "Create at least two meetings before performing a handover."
                )

            else:

                meeting_lookup = {
                    meeting.get("meeting_id", meeting["id"]): meeting
                    for meeting in meetings
                }

                meeting_options = {
                    (
                        f"{meeting.get('title', 'Untitled')} "
                        f"({meeting.get('date', '')})"
                    ): meeting.get("meeting_id", meeting["id"])
                    for meeting in meetings
                }

                st.subheader("Select Meetings")

                source_label = st.selectbox(
                    "Previous Meeting",
                    list(meeting_options.keys()),
                    key="handover_source"
                )

                source_id = meeting_options[source_label]

                target_options = {
                    label: meeting_id
                    for label, meeting_id in meeting_options.items()
                    if meeting_id != source_id
                }

                target_label = st.selectbox(
                    "Receiving Meeting",
                    list(target_options.keys()),
                    key="handover_target"
                )

                target_id = target_options[target_label]

                # Only open tasks belonging to the source meeting.
                open_tasks = [
                    task for task in tasks
                    if task.get("meeting_id") == source_id
                    and task.get("status") != "Completed"
                ]

                st.divider()

                st.subheader("Select Open Action Items")

                if not open_tasks:

                    st.info(
                        "No open action items are linked to this meeting."
                    )

                else:

                    task_options = {}

                    for task in open_tasks:

                        task_id = task.get(
                            "task_id",
                            task["id"]
                        )

                        label = (
                            f"{task.get('title', 'Untitled')} | "
                            f"{task.get('owner', 'Unassigned')} | "
                            f"{task.get('status', 'Pending')}"
                        )

                        task_options[label] = task_id

                    selected_labels = st.multiselect(
                        "Choose tasks to carry forward",
                        list(task_options.keys())
                    )

                    st.divider()

                    st.subheader("Responsibility Transfer")

                    new_owner = st.text_input(
                        "Reassign all selected tasks to (optional)",
                        placeholder="Leave blank to retain existing owners"
                    )

                    if new_owner.strip():

                        st.info(
                            f"Selected tasks will be reassigned to {new_owner.strip()}."
                        )

                    else:

                        st.caption(
                            "Existing task owners will be retained."
                        )

                    st.warning(
                        "Completed tasks cannot be transferred. "
                        "Transferred tasks will retain their original meeting ID."
                    )

                    confirm = st.checkbox(
                        "I confirm that these tasks should be transferred."
                    )

                    if st.button(
                        "Execute Smart Handover",
                        use_container_width=True,
                        type="primary"
                    ):

                        if not selected_labels:
                            st.error("Select at least one task.")

                        elif not confirm:
                            st.error("Please confirm the handover.")

                        else:

                            try:

                                selected_ids = [
                                    task_options[label]
                                    for label in selected_labels
                                ]

                                handover_id, brief = execute_handover(
                                    source_meeting=source_id,
                                    target_meeting=target_id,
                                    selected_tasks=selected_ids,
                                    new_owner=new_owner
                                )

                                st.success(
                                    "Smart Handover completed successfully!"
                                )

                                st.write(
                                    f"**Handover ID:** `{handover_id}`"
                                )

                                st.subheader("Generated Handover Brief")

                                st.text_area(
                                    "Handover Brief",
                                    value=brief,
                                    height=350
                                )

                            except Exception as e:

                                st.error(
                                    f"Unable to execute handover: {e}"
                                )

        except Exception as e:

            st.error(f"Unable to load handover information: {e}")

    # ==================================
    # TAB 2: HANDOVER HISTORY
    # ==================================

    with tab2:

        st.subheader("Previous Handover Records")

        try:

            handovers = get_collection("handover_briefs")

            handovers.sort(
                key=lambda item: item.get("created_at", ""),
                reverse=True
            )

            if not handovers:

                st.info("No handover records available yet.")

            else:

                for handover in handovers:

                    with st.expander(
                        f"Handover - {handover.get('created_at', '')}"
                    ):

                        st.write(
                            "**Source Meeting:**",
                            handover.get("source_meeting_id")
                        )

                        st.write(
                            "**Receiving Meeting:**",
                            handover.get("target_meeting_id")
                        )

                        st.write(
                            "**Transferred Tasks:**",
                            len(handover.get("transferred_tasks", []))
                        )

                        for task in handover.get("transferred_tasks", []):

                            st.write(
                                f"- {task.get('title')} "
                                f"({task.get('previous_owner')} → "
                                f"{task.get('new_owner')})"
                            )

                        st.text_area(
                            "Saved Handover Brief",
                            value=handover.get("brief", ""),
                            height=250,
                            key=f"brief_{handover.get('handover_id')}"
                        )

        except Exception as e:

            st.error(f"Unable to load handover history: {e}")
