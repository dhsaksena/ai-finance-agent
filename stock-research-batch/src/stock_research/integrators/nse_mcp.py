import asyncio
import json
from datetime import date, timedelta
from typing import Optional

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from stock_research.integrators.base import ResearchIntegrator

_BHAVCOPY_URL = "https://mcp.nseindia.in/bhavcopy/cm/mcp"


def _today() -> str:
    return date.today().strftime("%Y-%m-%d")


def _days_ago(n: int) -> str:
    return (date.today() - timedelta(days=n)).strftime("%Y-%m-%d")


# Each entry: (tool_name, args_dict)
# These are the stock-specific tools from the nse-bhavcopy server.
def _stock_tools(ticker: str) -> list:
    return [
        ("get_bulk_quote",        {"symbols": [ticker]}),
        ("get_52_week_high_low",  {"symbol": ticker}),
        ("get_ltp_by_date",       {"symbol": ticker, "date": _today()}),
        ("get_stock_history",     {"symbol": ticker, "from_date": _days_ago(90), "to_date": _today()}),
        ("get_corporate_actions", {"symbol": ticker}),
        ("moving_average",        {"symbol": ticker, "period": 50}),
        ("get_volume_analysis",   {"symbol": ticker, "days": 30}),
        ("get_stock_vs_index",    {"symbol": ticker, "index": "NIFTY 50"}),
    ]


class NSEMCPIntegrator(ResearchIntegrator):
    """Fetches NSE price/volume data via the bhavcopy MCP server."""

    def __init__(self, url: str = _BHAVCOPY_URL):
        self.url = url

    def research(self, ticker: str) -> str:
        return asyncio.run(self._research_async(ticker))

    async def _research_async(self, ticker: str) -> str:
        sections = []
        for tool_name, args in _stock_tools(ticker):
            content = await self._call_tool(tool_name, args)
            if content:
                sections.append(f"### {tool_name}\n\n{content}")

        if not sections:
            return f"No data retrieved from NSE for {ticker}."

        return f"# NSE Market Data: {ticker}\n\n" + "\n\n".join(sections)

    async def _call_tool(self, tool_name: str, args: dict) -> str:
        # Each tool gets its own isolated connection so a background-stream
        # failure on one call does not corrupt subsequent calls.
        try:
            async with streamable_http_client(self.url, terminate_on_close=False) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    result = await session.call_tool(tool_name, args)
                    return self._extract_content(result)
        except Exception:
            return ""

    @staticmethod
    def _extract_content(call_result) -> str:
        parts = []
        for item in call_result.content:
            if hasattr(item, "text") and item.text:
                parts.append(item.text)
            elif hasattr(item, "data"):
                parts.append(json.dumps(item.data, indent=2))
        return "\n".join(parts)
