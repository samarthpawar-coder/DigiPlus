
import streamlit as st
import uuid

from datetime import date, datetime, timezone

from database.firebase_db import (
    create_document,
    get_collection,
    delete_document
)

from utils.validation import validate_required
from utils.logger import log_event, new_request_id


def create_meeting(
    title,
    meeting_date,
    participants,
    agenda,
    notes
):
    """Create and save a meeting in Firestore."""

    title = validate_required(title, "Meeting title")

    if not participants:
        raise ValueError("Add at least one participant.")

    if not agenda.strip():
        raise ValueError("Meeting agenda is required.")

    meeting_id = str(uuid.uuid4())
    request_id = new_request_id()

    meeting_data = {
        "meeting_id": meeting_id,
        "title": title,
        "date": meeting_date.isoformat(),
        "participants": participants,
        "agenda": agenda.strip(),
        "notes": notes.strip(),
        "summary": "",
        "decisions": [],
        "status": "Scheduled",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }

    create_document(
        "meetings",
        meeting_id,
        meeting_data
    )

    log_event(
        f"Meeting created: {meeting_id}",
        level="INFO",
        request_id=request_id
    )

    return meeting_id


def show_meetings():

    st.title("📅 Meeting Management")

    st.caption(
        "Create meetings, manage participants and preserve "
        "important discussions."
    )

    tab1, tab2 = st.tabs([
        "➕ Create Meeting",
        "📋 All Meetings"
    ])

    # ---------------------------------
    # TAB 1: CREATE MEETING
    # ---------------------------------

    with tab1:

        st.subheader("Create a New Meeting")

        with st.form("create_meeting_form"):

            title = st.text_input(
                "Meeting Title",
                placeholder="Example: DigiPlus Project Review"
            )

            meeting_date = st.date_input(
                "Meeting Date",
                value=date.today()
            )

            participants_input = st.text_input(
                "Participants",
                placeholder="Rahul, Priya, Samarth"
            )

            agenda = st.text_area(
                "Meeting Agenda",
                height=120,
                placeholder="1. Project progress\n2. Pending work\n3. Deployment plan"
            )

            notes = st.text_area(
                "Meeting Notes",
                height=180,
                placeholder="Record the discussions and important points..."
            )

            submitted = st.form_submit_button(
                "Save Meeting",
                use_container_width=True
            )

            if submitted:

                try:

                    participants = [
                        person.strip()
                        for person in participants_input.split(",")
                        if person.strip()
                    ]

                    meeting_id = create_meeting(
                        title=title,
                        meeting_date=meeting_date,
                        participants=participants,
                        agenda=agenda,
                        notes=notes
                    )

                    st.success("Meeting saved successfully!")

                    st.write(f"Meeting ID: `{meeting_id}`")

                    st.rerun()

                except Exception as e:

                    st.error(f"Unable to create meeting: {e}")

    # ---------------------------------
    # TAB 2: VIEW MEETINGS
    # ---------------------------------

    with tab2:

        st.subheader("Meeting History")

        try:

            meetings = get_collection("meetings")

            if not meetings:

                st.info("No meetings available. Create your first meeting!")

            else:

                meetings.sort(
                    key=lambda m: m.get("date", ""),
                    reverse=True
                )

                for meeting in meetings:

                    meeting_id = meeting.get("meeting_id", meeting["id"])

                    with st.expander(
                        f"📌 {meeting.get('title', 'Untitled')} "
                        f"— {meeting.get('date', 'No date')}"
                    ):

                        st.write("**Meeting ID:**", meeting_id)

                        st.write("**Date:**", meeting.get("date"))

                        st.write(
                            "**Participants:**",
                            ", ".join(meeting.get("participants", []))
                        )

                        st.write("**Agenda:**")

                        st.write(meeting.get("agenda", "No agenda"))

                        st.write("**Meeting Notes:**")

                        st.write(meeting.get("notes") or "No notes available.")

                        st.write(
                            "**Status:**",
                            meeting.get("status", "Scheduled")
                        )

                        st.divider()

                        if st.button(
                            "Delete Meeting",
                            key=f"delete_{meeting_id}"
                        ):

                            try:

                                delete_document(
                                    "meetings",
                                    meeting_id
                                )

                                log_event(
                                    f"Meeting deleted: {meeting_id}",
                                    level="WARNING",
                                    request_id=new_request_id()
                                )

                                st.success("Meeting deleted.")

                                st.rerun()

                            except Exception as e:

                                st.error(
                                    f"Unable to delete meeting: {e}"
                                )

        except Exception as e:

            st.error(f"Unable to load meetings: {e}")
