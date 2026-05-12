"""Dynamic model discovery for all supported providers."""

import os
import requests
from typing import List


def fetch_ollama_models(base_url: str) -> List[str]:
    try:
        resp = requests.get(f"{base_url.rstrip('/')}/api/tags", timeout=3)
        if resp.status_code == 200:
            return [m["name"] for m in resp.json().get("models", [])]
    except Exception:
        pass
    return []


def fetch_openai_compatible_models(api_key: str, base_url: str) -> List[str]:
    try:
        headers = {"Authorization": f"Bearer {api_key}"}
        base = base_url.rstrip("/")
        if base.endswith("/v1"):
            endpoint = f"{base}/models"
        else:
            endpoint = f"{base}/v1/models"
        
        resp = requests.get(endpoint, headers=headers, timeout=5)
        if resp.status_code == 200:
            return [m.get("id", "") for m in resp.json().get("data", []) if m.get("id")]
    except Exception:
        pass
    return []


def fetch_google_models() -> List[str]:
    # Google doesn't expose a public unauthenticated model list endpoint.
    # Return known stable models + allow custom input.
    return [
        "gemini-2.0-flash",
        "gemini-2.0-pro",
        "gemini-1.5-flash",
        "gemini-1.5-pro",
        "gemini-2.5-flash",
        "gemini-2.5-pro",
    ]


def get_available_models(provider: str) -> List[str]:
    """Fetch models dynamically based on selected provider."""
    env = dict(os.environ)

    if provider == "ollama":
        return fetch_ollama_models(env.get("OLLAMA_BASE_URL", "http://localhost:11434"))
    elif provider in ["openai", "byok"]:
        key = env.get("OPENAI_API_KEY") or env.get("BYOK_API_KEY")
        url = env.get("OPENAI_BASE_URL") or env.get("BYOK_BASE_URL") or "https://api.openai.com/v1"
        return fetch_openai_compatible_models(key, url) if key else []
    elif provider == "google":
        return fetch_google_models()
    elif provider == "ollama_cloud":
        key = env.get("OLLAMA_CLOUD_API_KEY")
        url = env.get("OLLAMA_CLOUD_BASE_URL", "https://api.ollama.com/v1")
        return fetch_openai_compatible_models(key, url) if key else []
    return []
