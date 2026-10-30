
import streamlit as st
from pathlib import Path

from config import APP_NAME

from modules.dashboard import show_dashboard
from modules.meetings import show_meetings
from modules.action_tracker import show_action_tracker
from modules.knowledge_base import show_knowledge_base
from modules.handover import show_handover


# =====================================
# PAGE CONFIGURATION
# =====================================

st.set_page_config(
    page_title="DigiPlus | Workspace",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =====================================
# LOAD GLOBAL CSS
# =====================================

def load_css():

    css_path = Path(__file__).parent / "style.css"

    if css_path.exists():

        with open(css_path, "r", encoding="utf-8") as file:

            st.markdown(
                f"<style>{file.read()}</style>",
                unsafe_allow_html=True
            )


load_css()


# =====================================
# SIDEBAR
# =====================================

with st.sidebar:

    st.markdown(
        """
        <div style="padding: 12px 0 22px 0;">
            <div style="
                font-size: 27px;
                font-weight: 800;
                letter-spacing: -1px;
                color: #FFFFFF;
            ">
                🧠 DigiPlus
            </div>
            <div style="
                font-size: 11px;
                color: #98A2B3;
                margin-top: 5px;
            ">
                KNOWLEDGE & TASK WORKSPACE
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.divider()

    st.markdown(
        """
        <div style="
            color: #98A2B3;
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 1px;
            margin: 12px 0 8px 4px;
        ">
            WORKSPACE
        </div>
        """,
        unsafe_allow_html=True
    )

    navigation = {
        "Dashboard": "🏠",
        "Meetings": "📅",
        "Action Items": "✓",
        "Knowledge Base": "📚",
        "Handover": "🔄"
    }

    page = st.radio(
        "Navigation",
        list(navigation.keys()),
        format_func=lambda item: (
            f"{navigation[item]}   {item}"
        ),
        label_visibility="collapsed"
    )

    st.divider()

    st.markdown(
        """
        <div style="
            padding: 12px;
            background: #1D2939;
            border-radius: 10px;
            margin-top: 12px;
        ">
            <div style="font-size: 12px; font-weight: 600;">
                DigiPlus Workspace
            </div>
            <div style="
                color: #98A2B3;
                font-size: 10px;
                margin-top: 5px;
            ">
                Version 1.0.0
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


# =====================================
# PAGE ROUTING
# =====================================

if page == "Dashboard":

    show_dashboard()

elif page == "Meetings":

    show_meetings()

elif page == "Action Items":

    show_action_tracker()

elif page == "Knowledge Base":

    show_knowledge_base()

elif page == "Handover":

    show_handover()
