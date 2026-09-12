import logging
import os
import json
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from cli import ask_advisor, ask_advisor_stream
from ingest import load_notes
from cli import build_context

from logging.handlers import RotatingFileHandler


# In-memory session storage: {session_id: {"history": [...], "context": "..."}}
sessions = {}


class ChatRequest(BaseModel):
    query: str
    session_id: str = None


class ChatResponse(BaseModel):
    response: str
    session_id: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Finance Agent Server starting...")
    yield
    logger.info("Finance Agent Server shutting down...")


app = FastAPI(title="Finance Agent API", lifespan=lifespan)

logger = logging.getLogger("finance-agent")
logger.setLevel(logging.INFO)

handler = RotatingFileHandler(
    "app.log",
    maxBytes=10 * 1024 * 1024,
    backupCount=5
)


formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)

handler.setFormatter(formatter)
logger.addHandler(handler)

# Enable CORS for the frontend (allow all localhost ports for development)
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/chat")
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Accept a user query and return the agent's response.
    Maintains conversation history per session_id.
    """
    try:
        # Create or retrieve session
        session_id = request.session_id or str(uuid4())

        if session_id not in sessions:
            # Initialize new session with fresh history and context
            notes = load_notes()
            context = build_context(notes)
            sessions[session_id] = {
                "history": [],
                "context": context
            }

        session = sessions[session_id]

        # Add user query to history
        session["history"].append({"role": "user", "content": request.query})

        # Get agent response (ask_advisor handles tool loop internally)
        response_text = ask_advisor(session["history"], session["context"])

        logger.info(f"Session {session_id}: Query processed successfully")

        return ChatResponse(
            response=response_text,
            session_id=session_id
        )
    except Exception as e:
        logger.exception(f"Chat endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat/stream")
async def chatStream(request: ChatRequest) -> StreamingResponse:
    session_id = request.session_id or str(uuid4())

    if session_id not in sessions:
        # Initialize new session with fresh history and context
        notes = load_notes()
        context = build_context(notes)
        sessions[session_id] = {
            "history": [],
            "context": context
        }

    session = sessions[session_id]

    session["history"].append({
        "role": "user",
        "content": request.query
    })

    async def event_generator():
        try:
            async for event in ask_advisor_stream(
                session["history"],
                session["context"]
            ):
                yield f"data: {json.dumps(event)}\n\n"

        except Exception as e:
            logger.exception(
                f"Session {session_id}: Streaming failed"
            )
            yield f"data: {json.dumps({
                'type': 'error',
                'message': str(e)
            })}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@app.post("/sessions/{session_id}/clear")
async def clear_session(session_id: str):
    """Clear the conversation history for a session."""
    if session_id in sessions:
        notes = load_notes()
        context = build_context(notes)
        sessions[session_id] = {
            "history": [],
            "context": context
        }
        logger.info(f"Session {session_id} cleared")
        return {"status": "cleared"}
    else:
        raise HTTPException(status_code=404, detail="Session not found")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("FINANCE_AGENT_PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
