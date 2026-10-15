from abc import ABC, abstractmethod


class ResearchIntegrator(ABC):
    """Abstract base for research data providers."""

    @abstractmethod
    def research(self, ticker: str) -> str:
        """Return markdown research content for the given ticker."""
