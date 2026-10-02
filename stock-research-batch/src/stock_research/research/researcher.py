from stock_research.gemini.client import GeminiClient
from stock_research.research.prompts import STOCK_RESEARCH_PROMPT


class StockResearcher:
    """Orchestrates stock research using Gemini AI."""

    def __init__(self, model: str = "gemini-3.5-flash-lite"):
        self.client = GeminiClient(model=model)

    def research(self, ticker: str) -> str:
        """
        Generate a comprehensive research report for a given stock ticker.

        Args:
            ticker: Stock ticker symbol (e.g., 'AAPL')

        Returns:
            Markdown-formatted research report
        """
        prompt = STOCK_RESEARCH_PROMPT.format(ticker=ticker)
        report = self.client.research(prompt)
        return report
