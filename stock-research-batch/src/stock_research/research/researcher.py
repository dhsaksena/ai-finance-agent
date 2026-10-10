from typing import List, Optional

from stock_research.integrators.base import ResearchIntegrator
from stock_research.integrators.enriched import EnrichedResearchIntegrator


class StockResearcher:
    """Orchestrates stock research via one or more integrators."""

    def __init__(self, integrators: Optional[List[ResearchIntegrator]] = None):
        self.integrators = integrators if integrators is not None else [EnrichedResearchIntegrator()]

    def research(self, ticker: str) -> str:
        """
        Generate a research report for a given stock ticker.

        Collects results from all configured integrators and combines them.

        Args:
            ticker: Stock ticker symbol (e.g., 'RELIANCE')

        Returns:
            Markdown-formatted research report
        """
        reports = [integrator.research(ticker) for integrator in self.integrators]

        if len(reports) == 1:
            return reports[0]

        return "\n\n---\n\n".join(reports)
