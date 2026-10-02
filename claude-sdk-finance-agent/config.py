from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent
NOTES_DIR = BASE_DIR / "notes"
RESEARCH_DIR = BASE_DIR / "research"