
import firebase_admin
from firebase_admin import credentials, firestore

from config import get_firebase_credentials

_db = None


def initialize_firebase():
    """Initialize Firebase and return Firestore client."""

    global _db

    if _db is not None:
        return _db

    try:
        app = firebase_admin.get_app()

    except ValueError:
        credentials_data = get_firebase_credentials()
        cred = credentials.Certificate(credentials_data)

        app = firebase_admin.initialize_app(cred)

    _db = firestore.client(app=app)

    return _db


def get_db():
    """Get Firestore database."""

    return initialize_firebase()


def create_document(collection, document_id, data):
    """Create or update a document."""

    db = get_db()

    db.collection(collection).document(document_id).set(data)

    return True


def get_document(collection, document_id):
    """Retrieve a document."""

    db = get_db()

    doc = db.collection(collection).document(document_id).get()

    if doc.exists:
        return doc.to_dict()

    return None


def update_document(collection, document_id, data):
    """Update an existing document."""

    db = get_db()

    db.collection(collection).document(document_id).update(data)

    return True


def delete_document(collection, document_id):
    """Delete a document."""

    db = get_db()

    db.collection(collection).document(document_id).delete()

    return True


def get_collection(collection):
    """Retrieve all documents from a collection."""

    db = get_db()

    documents = db.collection(collection).stream()

    return [
        {
            "id": doc.id,
            **(doc.to_dict() or {})
        }
        for doc in documents
    ]
