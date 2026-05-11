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

import base64
import binascii
import json
import os
import firebase_admin
from firebase_admin import credentials, firestore
from google.auth.exceptions import DefaultCredentialsError

# ── Project details (from firebase.js) ────────────────────────────────────
FIREBASE_PROJECT_ID     = "data-mahasiswa-132d3"
FIREBASE_STORAGE_BUCKET = "data-mahasiswa-132d3.firebasestorage.app"

_PROJECT_ROOT = os.path.dirname(__file__)
_SERVICE_ACCOUNT_JSON_BASE64_ENV_VARS = (
    "FIREBASE_SERVICE_ACCOUNT_JSON_BASE64",
    "FIREBASE_SERVICE_ACCOUNT_BASE64",
)
_SERVICE_ACCOUNT_JSON_ENV_VARS = (
    "FIREBASE_SERVICE_ACCOUNT_JSON",
    "FIREBASE_SERVICE_ACCOUNT_KEY",
)
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


def _normalize_service_account_info(service_account_info: dict) -> dict:
    private_key = service_account_info.get("private_key")
    if private_key:
        service_account_info = dict(service_account_info)
        service_account_info["private_key"] = private_key.replace("\\n", "\n")

    return service_account_info


def _decode_base64_service_account_json(raw_value: str) -> str:
    normalized_value = "".join(raw_value.split())
    padded_value = normalized_value + ("=" * (-len(normalized_value) % 4))
    decoded_bytes = base64.b64decode(padded_value, altchars=b"-_", validate=True)
    return decoded_bytes.decode("utf-8")


def _load_service_account_info(raw_value: str, env_name: str) -> dict:
    try:
        return _normalize_service_account_info(json.loads(raw_value))
    except json.JSONDecodeError:
        try:
            decoded_json = _decode_base64_service_account_json(raw_value)
            return _normalize_service_account_info(json.loads(decoded_json))
        except (binascii.Error, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise RuntimeError(
                f"Environment variable '{env_name}' must contain valid Firebase service account JSON, either as raw JSON or base64-encoded JSON."
            ) from exc


def _resolve_service_account_certificate():
    last_env_error = None

    for env_name in _SERVICE_ACCOUNT_JSON_BASE64_ENV_VARS + _SERVICE_ACCOUNT_JSON_ENV_VARS:
        raw_json = os.environ.get(env_name, "").strip()
        if not raw_json:
            continue

        try:
            service_account_info = _load_service_account_info(raw_json, env_name)
        except RuntimeError as exc:
            last_env_error = exc
            continue

        return credentials.Certificate(service_account_info)

    service_account_path = _resolve_service_account_path()
    if service_account_path and os.path.exists(service_account_path):
        return credentials.Certificate(service_account_path)

    if last_env_error is not None:
        raise last_env_error

    return None


def get_firestore_client():
    """
    Initialize the Firebase Admin SDK (only once) and return a Firestore client.

    Initialization order:
            1. FIREBASE_SERVICE_ACCOUNT_JSON_BASE64 / FIREBASE_SERVICE_ACCOUNT_BASE64 env vars
            2. FIREBASE_SERVICE_ACCOUNT_JSON / FIREBASE_SERVICE_ACCOUNT_KEY env vars
            3. serviceAccountKey.json in project root  (local development)
            4. GOOGLE_APPLICATION_CREDENTIALS env var  (any explicit path)
            5. Application Default Credentials          (GCP / Cloud Run deployment)
    """
    if not firebase_admin._apps:
        service_account_credential = _resolve_service_account_certificate()

        if service_account_credential is not None:
            firebase_admin.initialize_app(service_account_credential, {
                "projectId":     FIREBASE_PROJECT_ID,
                "storageBucket": FIREBASE_STORAGE_BUCKET,
            })
        else:
            try:
                # Fallback: Application Default Credentials (gcloud auth / GCP env)
                firebase_admin.initialize_app(options={
                    "projectId":     FIREBASE_PROJECT_ID,
                    "storageBucket": FIREBASE_STORAGE_BUCKET,
                })
            except DefaultCredentialsError as exc:
                raise RuntimeError(
                    "Firebase Admin credentials were not found. "
                    "Set FIREBASE_SERVICE_ACCOUNT_JSON_BASE64, FIREBASE_SERVICE_ACCOUNT_JSON, or GOOGLE_APPLICATION_CREDENTIALS in the deployment environment."
                ) from exc

    try:
        return firestore.client()
    except DefaultCredentialsError as exc:
        raise RuntimeError(
            "Firebase Admin credentials were not found. "
            "Set FIREBASE_SERVICE_ACCOUNT_JSON_BASE64, FIREBASE_SERVICE_ACCOUNT_JSON, or GOOGLE_APPLICATION_CREDENTIALS in the deployment environment."
        ) from exc


# Singleton client – import this wherever Firestore access is needed
db = get_firestore_client()
