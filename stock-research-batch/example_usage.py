#!/usr/bin/env python3
"""
Example script demonstrating how to use the stock research system standalone.

Usage:
    python example_usage.py AAPL
    python example_usage.py MSFT
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from stock_research.config import Config
from stock_research.research.researcher import StockResearcher
from stock_research.storage.markdown import MarkdownStorage


def main(ticker: str):
    """Generate research report for a stock ticker."""
    print(f"Initializing stock research for {ticker}...")

    try:
        Config.validate()
    except ValueError as e:
        print(f"Configuration error: {e}")
        print("Please set GEMINI_API_KEY environment variable")
        sys.exit(1)

    researcher = StockResearcher()
    storage = MarkdownStorage(Config.OUTPUT_DIR)

    print(f"Starting research for {ticker}...")
    print("This may take a few minutes as Gemini searches for current information...")

    try:
        report = researcher.research(ticker)
        output_file = storage.save(ticker, report)
        print(f"\n✓ Research complete!")
        print(f"✓ Report saved to: {output_file}")
        print(f"\nReport preview (first 500 characters):")
        print("-" * 80)
        print(report[:500] + "...")

    except Exception as e:
        print(f"\n✗ Error during research: {e}")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python example_usage.py <TICKER>")
        print("Example: python example_usage.py AAPL")
        sys.exit(1)

    ticker = sys.argv[1].upper()
    main(ticker)
