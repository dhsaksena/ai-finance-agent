import logging
from pathlib import Path
from config import NOTES_DIR

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_notes() -> list[dict[str, str]]:
    """Load all markdown notes from the notes directory."""
    notes = []

    try:
        for file in NOTES_DIR.glob("*.md"):
            try:
                content = file.read_text(encoding="utf-8")
                notes.append({
                    "filename": file.name,
                    "content": content
                })
            except IOError as e:
                logger.error(f"Failed to read {file.name}: {e}")
                continue
    except Exception as e:
        logger.error(f"Failed to scan notes directory: {e}")

    return notes