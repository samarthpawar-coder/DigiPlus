
import streamlit as st
import uuid

from datetime import date, datetime, timezone

from database.firebase_db import (
    create_document,
    get_collection,
    update_document
)

from utils.validation import validate_required, validate_status
from utils.logger import log_event, new_request_id


STATUSES = [
    "Pending",
    "In Progress",
    "Completed",
    "Blocked"
]


def record_task_history(task_id, event, details, request_id):
    """Save every important task change."""

    history_id = str(uuid.uuid4())

    history_data = {
        "history_id": history_id,
        "task_id": task_id,
        "event": event,
        "details": details,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "request_id": request_id
    }

    create_document(
        "task_history",
        history_id,
        history_data
    )


def create_action_item(
    title,
    owner,
    due_date,
    meeting_id=None
):
    """Create and persist an action item."""

    title = validate_required(title, "Task title")

    if not owner.strip():
        raise ValueError("Task owner is required.")

    task_id = str(uuid.uuid4())
    request_id = new_request_id()

    task_data = {
        "task_id": task_id,
        "title": title,
        "owner": owner.strip(),
        "due_date": due_date.isoformat() if due_date else None,
        "meeting_id": meeting_id,
        "original_meeting_id": meeting_id,
        "status": "Pending",
        "outcome": "",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }

    create_document(
        "action_items",
        task_id,
        task_data
    )

    record_task_history(
        task_id,
        "Created",
        f"Task created and assigned to {owner.strip()}",
        request_id
    )

    log_event(
        f"Action item created: {task_id}",
        request_id=request_id
    )

    return task_id


def update_action_item(task_id, updates):
    """Update a task and record its changes."""

    request_id = new_request_id()

    existing_tasks = get_collection("action_items")

    existing = next(
        (
            task for task in existing_tasks
            if task.get("task_id", task["id"]) == task_id
        ),
        None
    )

    if not existing:
        raise ValueError("Action item not found.")

    if "status" in updates:
        validate_status(updates["status"])

    changes = []

    for field, new_value in updates.items():

        old_value = existing.get(field)

        if old_value != new_value:
            changes.append(
                f"{field}: {old_value} -> {new_value}"
            )

    if not changes:
        return False

    updates["updated_at"] = datetime.now(timezone.utc).isoformat()

    update_document(
        "action_items",
        task_id,
        updates
    )

    record_task_history(
        task_id,
        "Updated",
        "; ".join(changes),
        request_id
    )

    log_event(
        f"Action item updated: {task_id}",
        request_id=request_id
    )

    if updates.get("status") == "Completed":
        log_event(
            f"Action item closed: {task_id}",
            request_id=request_id
        )

    return True


def show_action_tracker():

    st.title("✅ Action Item Management")

    st.caption(
        "Assign, monitor and close tasks while preserving "
        "their complete history."
    )

    tab1, tab2, tab3 = st.tabs([
        "Create Task",
        "All Tasks",
        "Task History"
    ])

    # ==================================
    # TAB 1: CREATE TASK
    # ==================================

    with tab1:

        st.subheader("Create New Action Item")

        try:
            meetings = get_collection("meetings")

        except Exception as e:
            meetings = []
            st.error(f"Unable to load meetings: {e}")

        meeting_options = {
            "No linked meeting": None
        }

        for meeting in meetings:
            meeting_id = meeting.get(
                "meeting_id",
                meeting["id"]
            )

            meeting_options[
                f"{meeting.get('title', 'Untitled')} ({meeting.get('date', '')})"
            ] = meeting_id

        with st.form("create_action_item_form"):

            title = st.text_input(
                "Task Title",
                placeholder="Complete backend API development"
            )

            owner = st.text_input(
                "Assigned To",
                placeholder="Rahul"
            )

            selected_meeting = st.selectbox(
                "Related Meeting",
                list(meeting_options.keys())
            )

            has_due_date = st.checkbox(
                "Set a due date",
                value=True
            )

            due_date = None

            if has_due_date:
                due_date = st.date_input(
                    "Due Date",
                    value=date.today()
                )

            submitted = st.form_submit_button(
                "Create Action Item",
                use_container_width=True
            )

            if submitted:

                try:

                    task_id = create_action_item(
                        title=title,
                        owner=owner,
                        due_date=due_date,
                        meeting_id=meeting_options[selected_meeting]
                    )

                    st.success("Action item created successfully!")

                    st.write(f"Task ID: `{task_id}`")

                    st.rerun()

                except Exception as e:

                    st.error(f"Unable to create task: {e}")

    # ==================================
    # TAB 2: ALL TASKS
    # ==================================

    with tab2:

        st.subheader("Action Item Tracker")

        try:

            tasks = get_collection("action_items")

            filter_status = st.selectbox(
                "Filter by status",
                ["All", *STATUSES]
            )

            if filter_status != "All":
                visible_tasks = [
                    task for task in tasks
                    if task.get("status") == filter_status
                ]
            else:
                visible_tasks = tasks

            if not visible_tasks:

                st.info("No action items found.")

            for task in visible_tasks:

                task_id = task.get("task_id", task["id"])

                with st.expander(
                    f"{task.get('title', 'Untitled')} "
                    f"— {task.get('status', 'Pending')}"
                ):

                    st.write("**Assigned to:**", task.get("owner", "Unassigned"))

                    st.write("**Due date:**", task.get("due_date") or "Not set")

                    st.write("**Meeting ID:**", task.get("meeting_id") or "Standalone task")

                    st.write("**Current outcome:**", task.get("outcome") or "Not recorded")

                    st.divider()

                    with st.form(f"update_task_{task_id}"):

                        new_owner = st.text_input(
                            "Update Owner",
                            value=task.get("owner", "")
                        )

                        current_status = task.get("status", "Pending")

                        if current_status not in STATUSES:
                            current_status = "Pending"

                        new_status = st.selectbox(
                            "Update Status",
                            STATUSES,
                            index=STATUSES.index(current_status)
                        )

                        new_outcome = st.text_area(
                            "Record Outcome",
                            value=task.get("outcome", ""),
                            placeholder="Describe the result or completion details..."
                        )

                        new_due_date_text = st.text_input(
                            "Due Date (YYYY-MM-DD; leave empty if not applicable)",
                            value=task.get("due_date") or ""
                        )

                        save_changes = st.form_submit_button(
                            "Save Changes"
                        )

                        if save_changes:

                            try:

                                if not new_owner.strip():
                                    raise ValueError("Task owner cannot be empty.")

                                parsed_due_date = None

                                if new_due_date_text.strip():
                                    parsed_due_date = date.fromisoformat(
                                        new_due_date_text.strip()
                                    ).isoformat()

                                updates = {
                                    "owner": new_owner.strip(),
                                    "status": validate_status(new_status),
                                    "outcome": new_outcome.strip(),
                                    "due_date": parsed_due_date
                                }

                                changed = update_action_item(
                                    task_id,
                                    updates
                                )

                                if changed:
                                    st.success("Task updated successfully!")
                                else:
                                    st.info("No changes detected.")

                                st.rerun()

                            except ValueError as e:

                                st.error(str(e))

                            except Exception as e:

                                st.error(f"Unable to update task: {e}")

        except Exception as e:

            st.error(f"Unable to load action items: {e}")

    # ==================================
    # TAB 3: TASK HISTORY
    # ==================================

    with tab3:

        st.subheader("Task Activity History")

        try:

            history = get_collection("task_history")

            history.sort(
                key=lambda item: item.get("timestamp", ""),
                reverse=True
            )

            if not history:

                st.info("No task history available.")

            else:

                for event in history[:100]:

                    with st.container(border=True):

                        st.write(
                            f"**{event.get('event', 'Activity')}**"
                        )

                        st.caption(
                            f"Task ID: {event.get('task_id')}"
                        )

                        st.write(
                            event.get("details", "")
                        )

                        st.caption(
                            f"Time: {event.get('timestamp', '')}"
                        )

        except Exception as e:

            st.error(f"Unable to load task history: {e}")
