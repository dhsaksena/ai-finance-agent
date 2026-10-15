
import csv
import io
import logging
import time

import requests


logger = logging.getLogger(__name__)


class NSEDataProvider:

    NSE_EQUITY_LIST_URLS = [
        "https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv",
        "https://archives.nseindia.com/content/equities/EQUITY_L.csv",
    ]

    NSE_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0 Safari/537.36"
        ),
        "Accept": "text/csv,*/*;q=0.8",
        "Referer": "https://www.nseindia.com/",
    }

    def fetch_nse_names(
        self, retries_per_url: int = 2, timeout: int = 30
    ) -> dict[str, str]:
        """Return {SYMBOL: company name} from NSE's equity master CSV."""
        last_error = None

        for url in self.NSE_EQUITY_LIST_URLS:
            for attempt in range(retries_per_url):
                try:
                    response = requests.get(
                        url,
                        headers=self.NSE_HEADERS,
                        timeout=timeout,
                    )
                    response.raise_for_status()

                    reader = csv.DictReader(io.StringIO(response.text))

                    # Normalize CSV column headers.
                    reader.fieldnames = [
                        field.strip()
                        for field in (reader.fieldnames or [])
                    ]

                    return {
                        row["SYMBOL"].strip().upper():
                            row["NAME OF COMPANY"].strip()
                        for row in reader
                        if row.get("SYMBOL")
                        and row.get("NAME OF COMPANY")
                    }

                except (requests.RequestException, KeyError) as exc:
                    last_error = exc
                    logger.warning(
                        "NSE fetch failed (%s, attempt %d): %s",
                        url,
                        attempt + 1,
                        exc,
                    )
                    time.sleep(1 + attempt)

        raise RuntimeError(
            f"Could not fetch NSE equity master list: {last_error}"
        )

    def resolve_nse_symbol(
        self, symbol: str, master: dict[str, str]
    ) -> str | None:
        """
        Exact match first, then try removing the final hyphenated suffix.
        Returns the matching master key or None.
        """
        symbol = symbol.strip().upper()

        if symbol in master:
            return symbol

        if "-" in symbol:
            base = symbol.rsplit("-", 1)[0]
            if base in master:
                return base

        return None
