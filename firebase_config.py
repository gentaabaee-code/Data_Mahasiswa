"""
firebase_config.py
──────────────────────────────────────────────────────────────────────────────
Firebase Admin SDK initialization.

Project credentials are taken from firebase.js:
  projectId      : data-mahasiswa-132d3
  storageBucket  : data-mahasiswa-132d3.firebasestorage.app

The Admin SDK requires a Service Account Key (JSON) which you can download
from the Firebase console:
  Firebase Console → Project Settings → Service Accounts → Generate new private key

Save the downloaded file as an untracked local file such as
serviceAccountKey.json in the project root, OR set the environment variable
GOOGLE_APPLICATION_CREDENTIALS to its path.
──────────────────────────────────────────────────────────────────────────────
"""

import os
import firebase_admin
from firebase_admin import credentials, firestore

# ── Project details (from firebase.js) ────────────────────────────────────
FIREBASE_PROJECT_ID     = "data-mahasiswa-132d3"
FIREBASE_STORAGE_BUCKET = "data-mahasiswa-132d3.firebasestorage.app"

_PROJECT_ROOT = os.path.dirname(__file__)
_LOCAL_SERVICE_ACCOUNT_CANDIDATES = (
    os.path.join(_PROJECT_ROOT, "serviceAccountKey.json"),
    os.path.join(_PROJECT_ROOT, "serviceAccountKey.local.json"),
    os.path.join(
        _PROJECT_ROOT,
        "data-mahasiswa-132d3-firebase-adminsdk-fbsvc-4737f597ed.json",
    ),
)


def _resolve_service_account_path() -> str | None:
    explicit_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "").strip()
    if explicit_path:
        return explicit_path

    for candidate in _LOCAL_SERVICE_ACCOUNT_CANDIDATES:
        if os.path.exists(candidate):
            return candidate

    return None


def get_firestore_client():
    """
    Initialize the Firebase Admin SDK (only once) and return a Firestore client.

    Initialization order:
      1. serviceAccountKey.json in project root  (local development)
      2. GOOGLE_APPLICATION_CREDENTIALS env var  (any explicit path)
      3. Application Default Credentials          (GCP / Cloud Run deployment)
    """
    if not firebase_admin._apps:
        service_account_path = _resolve_service_account_path()

        if service_account_path and os.path.exists(service_account_path):
            cred = credentials.Certificate(service_account_path)
            firebase_admin.initialize_app(cred, {
                "projectId":     FIREBASE_PROJECT_ID,
                "storageBucket": FIREBASE_STORAGE_BUCKET,
            })
        else:
            # Fallback: Application Default Credentials (gcloud auth / GCP env)
            firebase_admin.initialize_app(options={
                "projectId":     FIREBASE_PROJECT_ID,
                "storageBucket": FIREBASE_STORAGE_BUCKET,
            })

    return firestore.client()


# Singleton client – import this wherever Firestore access is needed
db = get_firestore_client()
