import requests
from django.conf import settings


class BackendError(Exception):
    def __init__(self, message: str, status_code: int | None = None):
        self.status_code = status_code
        super().__init__(message)


def _base_url() -> str:
    return settings.BACKEND_API_URL.rstrip("/")


def get_facility(ccn: str) -> dict:
    try:
        response = requests.get(f"{_base_url()}/facilities/{ccn}", timeout=15)
    except requests.RequestException as exc:
        raise BackendError(f"Could not reach the backend service: {exc}") from exc

    if response.status_code == 404:
        raise BackendError(f"CCN {ccn} was not found in the CMS Provider Information dataset.", 404)
    if response.status_code == 422:
        raise BackendError("CCN must be 6 alphanumeric characters.", 422)
    if response.status_code != 200:
        raise BackendError("CMS data is temporarily unavailable. Please try again shortly.", response.status_code)

    return response.json()


def get_insights(facility: dict, manual: dict) -> dict:
    try:
        response = requests.post(
            f"{_base_url()}/insights",
            json={"facility": facility, "manual": manual},
            timeout=30,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise BackendError(f"Could not generate AI insights: {exc}") from exc
    return response.json()


def post_chat(facilities: list[dict], question: str) -> dict:
    try:
        response = requests.post(
            f"{_base_url()}/chat",
            json={"facilities": facilities, "question": question},
            timeout=30,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise BackendError(f"Could not reach Sanavox: {exc}") from exc
    return response.json()


def export_file(facility: dict, manual: dict, ai_summary: str | None, file_format: str) -> tuple[bytes, str]:
    """Returns (content_bytes, content_type)."""
    try:
        response = requests.post(
            f"{_base_url()}/reports/{file_format}",
            json={"facility": facility, "manual": manual, "ai_summary": ai_summary},
            timeout=30,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise BackendError(f"Could not generate the {file_format} export: {exc}") from exc
    return response.content, response.headers.get("content-type", "application/octet-stream")
