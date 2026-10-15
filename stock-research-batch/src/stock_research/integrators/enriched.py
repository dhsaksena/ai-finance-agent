from stock_research.gemini.client import GeminiClient
from stock_research.integrators.base import ResearchIntegrator
from stock_research.integrators.nse_mcp import NSEMCPIntegrator
from stock_research.research.prompts import STOCK_RESEARCH_PROMPT

_ENRICHED_PROMPT = """
{base_prompt}

--- LIVE NSE MARKET DATA (use this as your primary source for price/volume/market data) ---

{nse_data}

--- END OF NSE MARKET DATA ---
"""


class EnrichedResearchIntegrator(ResearchIntegrator):
    """Fetches live NSE market data, then uses Gemini to produce a full research report grounded in that data."""

    def __init__(
        self,
        nse_url: str = None,
        gemini_model: str = None,
        gemini_temperature: float = None,
    ):
        self.nse = NSEMCPIntegrator(url=nse_url) if nse_url else NSEMCPIntegrator()
        self.gemini = GeminiClient(model=gemini_model, temperature=gemini_temperature)

    def research(self, ticker: str) -> str:
        nse_data = self.nse.research(ticker)
        print(f"[NSE data fetched for {ticker}]\n{nse_data}\n{'='*60}")

        base_prompt = STOCK_RESEARCH_PROMPT.format(ticker=ticker)
        prompt = _ENRICHED_PROMPT.format(base_prompt=base_prompt, nse_data=nse_data)

        # use_search=False: NSE data is already in the prompt; enabling Google
        # Search (AFC) doubles API calls and triggers rate limits on free tier.
        return self.gemini.research(prompt, use_search=False)
