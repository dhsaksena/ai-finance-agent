from datetime import datetime
from pathlib import Path


class MarkdownStorage:
    """Handles saving research reports to markdown files."""

    def __init__(self, base_dir: Path):
        """
        Initialize storage with base directory.

        Args:
            base_dir: Base directory where ticker folders will be created
        """
        self.base_dir = Path(base_dir)

    def save(self, ticker: str, content: str, date: datetime = None) -> Path:
        """
        Save research report to markdown file.

        Args:
            ticker: Stock ticker symbol
            content: Research report content
            date: Optional date for the report (defaults to today)

        Returns:
            Path to the saved file
        """
        if date is None:
            date = datetime.now()

        ticker_dir = self.base_dir / ticker
        ticker_dir.mkdir(parents=True, exist_ok=True)

        date_str = date.strftime("%Y-%m-%d")
        output_file = ticker_dir / f"{date_str}.md"

        output_file.write_text(content, encoding="utf-8")
        return output_file
