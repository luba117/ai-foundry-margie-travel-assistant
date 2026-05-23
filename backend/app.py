"""
backend/app.py
--------------
FastAPI server for Margie's Travel Assistant — React UI interface.

Start with:
    uvicorn backend.app:app --reload --port 8000
(from the project root)
"""

import sys
import uuid
from pathlib import Path

# Allow imports from the project root (where core.py lives)
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from core import (
    DEPLOYMENT,
    SYSTEM_PROMPT,
    VECTOR_STORE_ID,
    build_tools,
    get_async_client,
)

# ---------------------------------------------------------------------------
# OpenAI async client (shared across requests)
# ---------------------------------------------------------------------------
client = get_async_client()


# ---------------------------------------------------------------------------
# In-memory session store  { session_id -> previous_response_id }
# ---------------------------------------------------------------------------
_sessions: dict[str, str] = {}

# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(title="Margie's Travel Assistant API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:4173",  # Vite preview
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class ChatRequest(BaseModel):
    message: str
    session_id: str = ""


class ChatResponse(BaseModel):
    reply: str
    session_id: str


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    session_id = req.session_id.strip() or str(uuid.uuid4())
    previous_response_id = _sessions.get(session_id)

    params: dict = {
        "model": DEPLOYMENT,
        "instructions": SYSTEM_PROMPT,
        "input": req.message,
        "tools": build_tools(),
    }
    if previous_response_id:
        params["previous_response_id"] = previous_response_id

    try:
        response = await client.responses.create(**params)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    _sessions[session_id] = response.id
    return ChatResponse(reply=response.output_text or "", session_id=session_id)


@app.delete("/api/chat/{session_id}")
async def clear_session(session_id: str) -> dict:
    _sessions.pop(session_id, None)
    return {"ok": True}


@app.get("/api/health")
async def health() -> dict:
    return {
        "status": "ok",
        "deployment": DEPLOYMENT,
        "vector_store": VECTOR_STORE_ID or "not configured",
    }
