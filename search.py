import json
import logging
import functools

import yfinance as yf

from config import BASE_DIR, RESEARCH_DIR

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TICKERS_FILE = BASE_DIR / "tickers.json"


@functools.lru_cache(maxsize=1)
def load_known_tickers() -> dict:
    """Load and cache the tickers file."""
    if not TICKERS_FILE.exists():
        logger.warning(f"Tickers file not found at {TICKERS_FILE}")
        return {}
    try:
        with open(TICKERS_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Failed to load tickers file: {e}")
        return {}


def search_ticker(company_name: str) -> dict:
    """Look up a company's ticker symbol from the local tickers.json file.

    This is the ONLY source of truth for tickers right now — it does not
    call out to the internet. If nothing matches, the caller (Claude)
    should ask the user for the ticker rather than guessing one.
    """
    known = load_known_tickers()
    company_lower = company_name.lower()

    for name, ticker in known.items():
        if company_lower in name.lower() or name.lower() in company_lower:
            return {"company": name, "ticker": ticker, "source": "local_file"}

    return {
        "company": company_name,
        "ticker": None,
        "source": "not_found",
        "note": (
            "Not found in tickers.json. Do not guess a ticker — "
            "ask the user for the exact ticker symbol."
        ),
    }


def get_stock_fundamentals(ticker: str) -> dict:
    """Fetch price, valuation, profitability, and growth stats for a stock.

    Call search_ticker first if you are not already certain of the
    exact ticker symbol. Some fields may be missing depending on the
    company and data available from the source — treat missing fields
    as "unknown," not zero, and say so if it affects your confidence.
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
    except Exception as e:
        logger.error(f"Failed to fetch data for ticker {ticker}: {e}")
        return {
            "ticker": ticker,
            "error": f"Failed to fetch fundamentals: {str(e)}",
        }

    return {
        "ticker": ticker,
        "price": {
            "current_price": info.get("currentPrice") or info.get("regularMarketPrice"),
            "previous_close": info.get("previousClose"),
            "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
            "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
        },
        "valuation": {
            "trailing_pe": info.get("trailingPE"),
            "forward_pe": info.get("forwardPE"),
            "price_to_book": info.get("priceToBook"),
            "market_cap": info.get("marketCap"),
        },
        "profitability": {
            "profit_margins": info.get("profitMargins"),
            "return_on_equity": info.get("returnOnEquity"),
            "debt_to_equity": info.get("debtToEquity"),
        },
        "growth": {
            "revenue_growth": info.get("revenueGrowth"),
            "earnings_growth": info.get("earningsGrowth"),
        },
        "other": {
            "dividend_yield": info.get("dividendYield"),
            "beta": info.get("beta"),
        },
    }


def get_company_research(ticker: str) -> dict:
    """Fetch manually-saved human research notes for a ticker, if any exist.

    Looks for a file at research/<BASE_TICKER>.md, where BASE_TICKER strips
    any exchange suffix (e.g. "ZFCVINDIA.NS" -> "ZFCVINDIA"), since research
    files are saved per-company, not per-exchange-listing.
    """
    try:
        base_ticker = ticker.split(".")[0].upper()
        filename = f"{base_ticker}.md"
        filepath = RESEARCH_DIR / filename

        if not filepath.exists():
            return {
                "ticker": ticker,
                "found": False,
                "note": (
                    "No research file found for this ticker. If fundamentals "
                    "alone leave real gaps, ask the user directly rather than "
                    "guessing."
                ),
            }

        with open(filepath, encoding="utf-8") as f:
            content = f.read()

        return {"ticker": ticker, "found": True, "content": content}
    except IOError as e:
        logger.error(f"Failed to read research file for {ticker}: {e}")
        return {
            "ticker": ticker,
            "found": False,
            "error": f"Failed to read research: {str(e)}",
        }


TOOLS = [
    {
        "name": "search_ticker",
        "description": (
            "Look up the stock ticker symbol for a company name, using the "
            "user's local tickers file. Always call this BEFORE "
            "get_stock_fundamentals if you are not already 100% certain of "
            "the exact ticker — never guess a ticker symbol."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "company_name": {
                    "type": "string",
                    "description": "The company name as the user referred to it.",
                }
            },
            "required": ["company_name"],
        },
    },
    {
        "name": "get_stock_fundamentals",
        "description": (
            "Get price, valuation (P/E, price-to-book), profitability "
            "(margins, ROE, debt-to-equity), and growth stats for a stock, "
            "given its confirmed ticker symbol. Use this as your primary "
            "basis for any buy/hold/sell judgment."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": (
                        "The confirmed stock ticker symbol, e.g. 'AAPL' or "
                        "'RELIANCE.NS' for NSE-listed stocks."
                    ),
                }
            },
            "required": ["ticker"],
        },
    },
    {
        "name": "get_company_research",
        "description": (
            "Fetch manually saved human research notes for a stock (balance "
            "sheet detail, earnings context, why a ratio looks distorted, "
            "analyst commentary) from a local research file, keyed by "
            "ticker. Call this when get_stock_fundamentals alone leaves a "
            "real gap in your confidence, BEFORE asking the user directly."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "The confirmed stock ticker symbol.",
                }
            },
            "required": ["ticker"],
        },
    },
]