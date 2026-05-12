"""Dynamic model resolver with explicit provider routing & validation."""

import os
import requests
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from src.utils.errors import ModelResolutionError


def resolve_model(provider_type: str, model_name: str):
    model_name = model_name.strip()
    if not model_name:
        raise ModelResolutionError("Error! Unable to search Model Name.")

    if provider_type == "ollama":
        ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        try:
            resp = requests.get(f"{ollama_url}/api/tags", timeout=3)
            if resp.status_code == 200:
                available = [m["name"] for m in resp.json().get("models", [])]
                match = next((m for m in available if model_name.lower() in m.lower()), None)
                if match:
                    return ChatOllama(
                        model=match, 
                        base_url=ollama_url, 
                        temperature=0.3,
                        timeout=1200  # 20 minutes
                    )
            raise ModelResolutionError("Error! Unable to search Model Name.")
        except requests.exceptions.ConnectionError:
            raise ModelResolutionError("Error! Ollama is not running. Start 'ollama serve'.")
        except Exception as e:
            if "Unable to search" in str(e):
                raise
            raise ModelResolutionError(f"Error! Unable to connect to Ollama: {e}")

    elif provider_type == "google":
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ModelResolutionError("Error! GOOGLE_API_KEY not set in .env")
        return ChatGoogleGenerativeAI(
            model=model_name, 
            google_api_key=api_key, 
            temperature=0.3, 
            timeout=1200
        )

    elif provider_type == "ollama_cloud":
        api_key = os.getenv("OLLAMA_CLOUD_API_KEY")
        base_url = os.getenv("OLLAMA_CLOUD_BASE_URL", "https://api.ollama.com/v1")
        if not api_key:
            raise ModelResolutionError("Error! OLLAMA_CLOUD_API_KEY not set in .env")
        return ChatOpenAI(
            model=model_name, 
            api_key=api_key, 
            base_url=base_url, 
            temperature=0.3,
            timeout=1200
        )

    elif provider_type in ["openai", "byok"]:
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("BYOK_API_KEY")
        base_url = (
            os.getenv("OPENAI_BASE_URL")
            or os.getenv("BYOK_BASE_URL")
            or "https://api.openai.com/v1"
        )
        if not api_key:
            raise ModelResolutionError("Error! Set OPENAI_API_KEY or BYOK_API_KEY in .env")
        try:
            resp = requests.get(
                f"{base_url.rstrip('/')}/models",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=5,
            )
            if resp.status_code == 200:
                ids = [m.get("id", "") for m in resp.json().get("data", [])]
                if not any(model_name.lower() in mid.lower() for mid in ids):
                    raise ModelResolutionError("Error! Unable to search Model Name.")
        except ModelResolutionError:
            raise
        except Exception:
            pass
        return ChatOpenAI(
            model=model_name, 
            api_key=api_key, 
            base_url=base_url, 
            temperature=0.3,
            timeout=1200
        )

    raise ModelResolutionError("Error! Invalid provider type.")
