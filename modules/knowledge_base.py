
import streamlit as st
import uuid

from datetime import datetime, timezone

from database.firebase_db import (
    create_document,
    get_collection,
    delete_document
)

from utils.validation import validate_required
from utils.logger import log_event, new_request_id


CATEGORIES = [
    "Project Documentation",
    "Meeting Notes",
    "Technical Documentation",
    "Research",
    "Policies",
    "Other"
]


def create_knowledge_document(
    title,
    category,
    content,
    description="",
    linked_meetings=None
):
    """Save a knowledge document to Firestore."""

    title = validate_required(title, "Document title")
    content = validate_required(content, "Document content")

    if len(content) > 500000:
        raise ValueError("Document content exceeds the 500,000 character limit.")

    document_id = str(uuid.uuid4())
    request_id = new_request_id()

    document_data = {
        "document_id": document_id,
        "title": title,
        "category": category,
        "description": description.strip(),
        "content": content,
        "linked_meetings": linked_meetings or [],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }

    create_document(
        "knowledge_base",
        document_id,
        document_data
    )

    log_event(
        f"Knowledge document created: {document_id}",
        request_id=request_id
    )

    return document_id


def search_knowledge_documents(documents, query):
    """Search document titles, categories and content."""

    query = query.strip().lower()

    if not query:
        return documents

    results = []

    for document in documents:

        searchable_text = " ".join([
            str(document.get("title", "")),
            str(document.get("category", "")),
            str(document.get("description", "")),
            str(document.get("content", ""))
        ]).lower()

        if query in searchable_text:
            results.append(document)

    return results


def show_knowledge_base():

    st.title("📚 Knowledge Base")

    st.caption(
        "Centralized storage for project documents, "
        "technical information and meeting knowledge."
    )

    tab1, tab2 = st.tabs([
        "Add Document",
        "Browse Documents"
    ])

    # ==================================
    # TAB 1: ADD DOCUMENT
    # ==================================

    with tab1:

        st.subheader("Add Knowledge Document")

        try:
            meetings = get_collection("meetings")

        except Exception as e:
            meetings = []
            st.error(f"Unable to load meetings: {e}")

        meeting_options = {}

        for meeting in meetings:

            meeting_id = meeting.get(
                "meeting_id",
                meeting["id"]
            )

            meeting_options[
                f"{meeting.get('title', 'Untitled')} ({meeting.get('date', '')})"
            ] = meeting_id

        with st.form("knowledge_document_form"):

            title = st.text_input(
                "Document Title",
                placeholder="Example: DigiPlus System Architecture"
            )

            category = st.selectbox(
                "Category",
                CATEGORIES
            )

            description = st.text_input(
                "Short Description",
                placeholder="Briefly describe this document"
            )

            uploaded_file = st.file_uploader(
                "Upload a text or Markdown file (optional)",
                type=["txt", "md"]
            )

            content_input = st.text_area(
                "Document Content",
                height=220,
                placeholder="Paste your document content here..."
            )

            selected_meetings = st.multiselect(
                "Link to Previous Meetings",
                list(meeting_options.keys())
            )

            submitted = st.form_submit_button(
                "Save Document",
                use_container_width=True
            )

            if submitted:

                try:

                    content = content_input

                    if uploaded_file is not None:

                        content = uploaded_file.getvalue().decode(
                            "utf-8-sig"
                        )

                    linked_meetings = [
                        meeting_options[name]
                        for name in selected_meetings
                    ]

                    document_id = create_knowledge_document(
                        title=title,
                        category=category,
                        content=content,
                        description=description,
                        linked_meetings=linked_meetings
                    )

                    st.success("Knowledge document saved successfully!")

                    st.write(f"Document ID: `{document_id}`")

                    st.rerun()

                except UnicodeDecodeError:

                    st.error(
                        "Unable to read this file. "
                        "Please upload a UTF-8 encoded TXT or Markdown file."
                    )

                except Exception as e:

                    st.error(f"Unable to save document: {e}")

    # ==================================
    # TAB 2: BROWSE DOCUMENTS
    # ==================================

    with tab2:

        st.subheader("Browse Knowledge Documents")

        try:

            documents = get_collection("knowledge_base")

            search_query = st.text_input(
                "Search Documents",
                placeholder="Search by title, category or content..."
            )

            filtered_documents = search_knowledge_documents(
                documents,
                search_query
            )

            st.caption(
                f"Showing {len(filtered_documents)} of "
                f"{len(documents)} documents"
            )

            if not filtered_documents:

                st.info("No matching knowledge documents found.")

            else:

                filtered_documents.sort(
                    key=lambda doc: doc.get("created_at", ""),
                    reverse=True
                )

                for document in filtered_documents:

                    document_id = document.get(
                        "document_id",
                        document["id"]
                    )

                    with st.expander(
                        f"📄 {document.get('title', 'Untitled')}"
                    ):

                        st.write(
                            "**Category:**",
                            document.get("category", "Other")
                        )

                        st.write(
                            "**Description:**",
                            document.get("description") or "No description"
                        )

                        st.write(
                            "**Created:**",
                            document.get("created_at", "")
                        )

                        st.write("**Document Content:**")

                        st.text_area(
                            "Content",
                            value=document.get("content", ""),
                            height=180,
                            disabled=True,
                            key=f"content_{document_id}"
                        )

                        linked_meetings = document.get(
                            "linked_meetings",
                            []
                        )

                        st.write(
                            "**Linked Meeting IDs:**",
                            ", ".join(linked_meetings)
                            if linked_meetings
                            else "No linked meetings"
                        )

                        if st.button(
                            "Delete Document",
                            key=f"delete_doc_{document_id}"
                        ):

                            try:

                                delete_document(
                                    "knowledge_base",
                                    document_id
                                )

                                log_event(
                                    f"Knowledge document deleted: {document_id}",
                                    level="WARNING",
                                    request_id=new_request_id()
                                )

                                st.success("Document deleted.")

                                st.rerun()

                            except Exception as e:

                                st.error(
                                    f"Unable to delete document: {e}"
                                )

        except Exception as e:

            st.error(f"Unable to load knowledge base: {e}")
