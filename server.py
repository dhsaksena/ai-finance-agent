import logging
import os
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from cli import ask_advisor
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
        logger.error(f"Error processing chat request: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process request: {str(e)}"
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
