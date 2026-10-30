
import streamlit as st
import pandas as pd

from datetime import date

from database.firebase_db import get_collection


def load_dashboard_data():
    """Fetch dashboard information from Firestore."""

    meetings = get_collection("meetings")
    tasks = get_collection("action_items")

    pending = [
        task for task in tasks
        if task.get("status") == "Pending"
    ]

    in_progress = [
        task for task in tasks
        if task.get("status") == "In Progress"
    ]

    completed = [
        task for task in tasks
        if task.get("status") == "Completed"
    ]

    overdue = []

    for task in tasks:
        due_date = task.get("due_date")

        if not due_date:
            continue

        try:
            due = date.fromisoformat(str(due_date)[:10])

            if due < date.today() and task.get("status") != "Completed":
                overdue.append(task)

        except (ValueError, TypeError):
            continue

    return {
        "meetings": meetings,
        "tasks": tasks,
        "pending": pending,
        "in_progress": in_progress,
        "completed": completed,
        "overdue": overdue
    }


def show_dashboard():

    st.markdown(
    """
    <div style="margin-bottom: 25px;">
        <div style="
            color: #667085;
            font-size: 12px;
            font-weight: 600;
            letter-spacing: 1px;
        ">
            OVERVIEW
        </div>
        <h1 style="
            font-size: 30px;
            font-weight: 800;
            margin: 5px 0;
            color: #182230;
        ">
            Welcome to DigiPlus 👋
        </h1>
        <p style="color: #667085; font-size: 14px;">
            Manage meetings, track responsibilities and keep
            your team's knowledge connected.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

    st.caption(
        "Your centralized workspace for meetings, "
        "knowledge and action management."
    )

    try:
        data = load_dashboard_data()

    except Exception as e:
        st.error(f"Unable to load dashboard data: {e}")
        return

    # Metric cards
    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Total Meetings",
        len(data["meetings"])
    )

    col2.metric(
        "Total Action Items",
        len(data["tasks"])
    )

    col3.metric(
        "Pending Tasks",
        len(data["pending"]) + len(data["in_progress"])
    )

    col4.metric(
        "Overdue Tasks",
        len(data["overdue"])
    )

    st.divider()

    # Task overview
    st.markdown(
    "<h3>📊 Action Item Overview</h3>",
    unsafe_allow_html=True
)

    task_col1, task_col2, task_col3 = st.columns(3)

    task_col1.metric(
        "Pending",
        len(data["pending"])
    )

    task_col2.metric(
        "In Progress",
        len(data["in_progress"])
    )

    task_col3.metric(
        "Completed",
        len(data["completed"])
    )

    if data["tasks"]:
        status_counts = {
            "Pending": len(data["pending"]),
            "In Progress": len(data["in_progress"]),
            "Completed": len(data["completed"])
        }

        chart_data = pd.DataFrame(
            list(status_counts.items()),
            columns=["Status", "Count"]
        )

        st.bar_chart(
            chart_data,
            x="Status",
            y="Count"
        )
    else:
        st.info("No action items have been created yet.")

    st.divider()

    # Recent meetings
    st.markdown(
    "<h3>📅 Recent Meetings</h3>",
    unsafe_allow_html=True
)

    if data["meetings"]:

        recent_meetings = sorted(
            data["meetings"],
            key=lambda meeting: str(meeting.get("date", "")),
            reverse=True
        )[:5]

        for meeting in recent_meetings:

            with st.container(border=True):

                st.write(
                    f"**{meeting.get('title', 'Untitled Meeting')}**"
                )

                st.caption(
                    f"Date: {meeting.get('date', 'Not specified')}"
                )

                st.write(
                    f"Participants: "
                    f"{', '.join(meeting.get('participants', []))}"
                )

    else:
        st.info("No meetings have been created yet.")

    st.divider()

    # Upcoming and overdue tasks
    st.markdown(
    "<h3>⚡ Tasks Requiring Attention</h3>",
    unsafe_allow_html=True
)

    attention_tasks = data["overdue"][:5]

    if attention_tasks:

        for task in attention_tasks:

            with st.container(border=True):

                st.write(
                    f"**{task.get('title', 'Untitled Task')}**"
                )

                st.write(
                    f"Owner: {task.get('owner') or 'Unassigned'}"
                )

                st.write(
                    f"Due date: {task.get('due_date', 'Not specified')}"
                )

                st.error("Overdue")

    else:
        st.success("No overdue tasks. Great work!")
