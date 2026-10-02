"""Configuration management for stock research."""
import os
from pathlib import Path


class Config:
    """Configuration for the stock research system."""

    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

    OUTPUT_DIR = Path(
        os.getenv(
            "OUTPUT_DIR",
            "/mnt/c/Users/dhsak/Documents/Study/AI/ai-finance-agent/stock-research-batch/output"
        )
    )

    RESEARCH_TEMPERATURE = float(os.getenv("RESEARCH_TEMPERATURE", "0.2"))

    @classmethod
    def validate(cls):
        """Validate required configuration."""
        if not cls.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        if not cls.OUTPUT_DIR.exists():
            cls.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
