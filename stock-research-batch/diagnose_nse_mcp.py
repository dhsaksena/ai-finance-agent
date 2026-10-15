#!/usr/bin/env python3
"""Diagnose NSE MCP server tools and test calls."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

SERVERS = {
    "nse-bhavcopy": "https://mcp.nseindia.in/bhavcopy/cm/mcp",
    "cm-market": "https://mcp.nseindia.in/cmmkt/mcp",
}


async def diagnose_server(server_name: str, url: str, ticker: str):
    print(f"\n{'='*60}")
    print(f"Server: {server_name}  ({url})")
    print(f"{'='*60}")

    # Collect tool info into plain dicts immediately — before the background
    # GET-stream task can crash the TaskGroup and interrupt the loop.
    tools_info = []
    try:
        async with streamable_http_client(url, terminate_on_close=False) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools_result = await session.list_tools()
                tools_info = [
                    {
                        "name": t.name,
                        "description": t.description or "",
                        "params": list((t.inputSchema or {}).get("properties", {}).keys()),
                        "required": (t.inputSchema or {}).get("required", []),
                        "schema": (t.inputSchema or {}).get("properties", {}),
                    }
                    for t in tools_result.tools
                ]
    except Exception:
        pass  # Connection cleanup may raise — we already have the data

    print(f"\nTools found: {len(tools_info)}\n")
    for t in tools_info:
        print(f"  Tool      : {t['name']}")
        print(f"  Description: {t['description'][:140]}")
        print(f"  Parameters : {t['params']}  (required: {t['required']})")
        print()


async def main():
    ticker = sys.argv[1].upper() if len(sys.argv) > 1 else "RELIANCE"
    print(f"Diagnosing NSE MCP servers for ticker: {ticker}")

    for name, url in SERVERS.items():
        try:
            await diagnose_server(name, url, ticker)
        except Exception as e:
            print(f"\nFailed to connect to {name}: {e}")
            if hasattr(e, "exceptions"):
                for sub in e.exceptions:
                    print(f"  Sub-exception: {sub}")


if __name__ == "__main__":
    asyncio.run(main())
