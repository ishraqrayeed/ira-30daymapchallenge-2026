"""Small, explicit HTTP and atomic-cache helpers."""

import hashlib
import json
from pathlib import Path
import tempfile

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def http_session() -> requests.Session:
    """Retry transient read failures without retrying arbitrary client errors."""
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    session.mount("https://", HTTPAdapter(max_retries=retry))
    session.headers["User-Agent"] = "30DayMapChallenge2026/0.1 (public-data research)"
    return session


def get_json(session: requests.Session, url: str, **params) -> dict:
    response = session.get(url, params=params, timeout=(10, 90))
    return _response_json(response, url)


def post_json(session: requests.Session, url: str, **params) -> dict:
    """Send read-only query parameters as form data, avoiding URL length limits."""
    response = session.post(url, data=params, timeout=(10, 90))
    return _response_json(response, url)


def _response_json(response: requests.Response, url: str) -> dict:
    response.raise_for_status()
    result = response.json()
    if not isinstance(result, dict) or "error" in result:
        raise ValueError(f"Invalid API response from {url}: {result}")
    return result


def write_json(path: Path, value: dict) -> str:
    """Atomically save JSON and return its SHA-256 for provenance manifests."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = (json.dumps(value, indent=2, allow_nan=False) + "\n").encode()
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as handle:
        temporary = Path(handle.name)
        handle.write(payload)
    temporary.replace(path)
    return hashlib.sha256(payload).hexdigest()
