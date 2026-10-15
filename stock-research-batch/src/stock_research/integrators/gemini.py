from stock_research.gemini.client import GeminiClient
from stock_research.integrators.base import ResearchIntegrator
from stock_research.research.prompts import STOCK_RESEARCH_PROMPT


class GeminiIntegrator(ResearchIntegrator):
    """Research integrator backed by Google Gemini."""

    def __init__(self, model: str = None, temperature: float = None, use_search: bool = True):
        self.client = GeminiClient(model=model, temperature=temperature)
        self.use_search = use_search

    def research(self, ticker: str) -> str:
        prompt = STOCK_RESEARCH_PROMPT.format(ticker=ticker)
        return self.client.research(prompt, use_search=self.use_search)
