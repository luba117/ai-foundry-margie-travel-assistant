"""
core.py
-------
Shared configuration and helpers for Margie's Travel Assistant.

Used by both:
  - travel_assistant.py  (CLI interface)
  - backend/app.py       (FastAPI / React interface)
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from openai import AsyncAzureOpenAI, AzureOpenAI

# Load .env from the project root regardless of where the script is run from
load_dotenv(dotenv_path=Path(__file__).parent / ".env")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
API_VERSION = "2025-04-01-preview"

SYSTEM_PROMPT = (Path(__file__).parent / "prompts" / "system_prompt.txt").read_text(encoding="utf-8").strip()


# ---------------------------------------------------------------------------
# Configuration helpers
# ---------------------------------------------------------------------------
def _normalize_endpoint(endpoint: str) -> str:
    """Strip /openai/v1 suffix added by some Foundry endpoint URLs."""
    for suffix in ("/openai/v1/", "/openai/v1"):
        if endpoint.endswith(suffix):
            return endpoint[: -len(suffix)]
    return endpoint.rstrip("/")


def _load_config() -> tuple[str, str, str, str]:
    """Return (endpoint, api_key, deployment, vector_store_id) from environment."""
    endpoint = _normalize_endpoint(os.environ.get("AZURE_OPENAI_ENDPOINT", "").strip())
    api_key = os.environ.get("AZURE_OPENAI_API_KEY", "").strip()
    deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1").strip()
    vector_store_id = os.environ.get("VECTOR_STORE_ID", "").strip()

    if not endpoint or not api_key:
        raise RuntimeError(
            "AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY must be set in .env"
        )

    return endpoint, api_key, deployment, vector_store_id


ENDPOINT, API_KEY, DEPLOYMENT, VECTOR_STORE_ID = _load_config()


# ---------------------------------------------------------------------------
# Client factories
# ---------------------------------------------------------------------------
def get_sync_client() -> AzureOpenAI:
    """Synchronous client — used by the CLI (travel_assistant.py)."""
    return AzureOpenAI(
        azure_endpoint=ENDPOINT,
        api_key=API_KEY,
        api_version=API_VERSION,
    )


def get_async_client() -> AsyncAzureOpenAI:
    """Async client — used by the FastAPI backend (backend/app.py)."""
    return AsyncAzureOpenAI(
        azure_endpoint=ENDPOINT,
        api_key=API_KEY,
        api_version=API_VERSION,
    )


# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------
def build_tools() -> list[dict]:
    """Return the list of Responses API tools to attach to every request."""
    tools: list[dict] = [{"type": "web_search_preview"}]

    if VECTOR_STORE_ID:
        tools.append(
            {"type": "file_search", "vector_store_ids": [VECTOR_STORE_ID]}
        )

    return tools
