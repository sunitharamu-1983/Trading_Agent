"""
main.py
───────
Entry point for the Trading Agent.

Run:
    python main.py                     # analyse default watch list
    python main.py --tickers AAPL TSLA # analyse specific tickers
    python main.py --search "Fed rate cut impact on tech stocks"  # ad-hoc search
"""

from __future__ import annotations

import argparse
import logging
import sys

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level  = logging.INFO,
    format = "%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


def cmd_analyse(tickers: list[str]) -> None:
    from agent.agent import run_analysis
    results = run_analysis(tickers)
    for ticker, analysis in results.items():
        print(f"\n{'='*60}")
        print(f"  {ticker}")
        print('='*60)
        print(analysis)


def cmd_search(query: str) -> None:
    """Ad-hoc Tavily search — useful for quick lookups during dev."""
    from agent.tavily_search import TavilySearchClient, search_topic
    client   = TavilySearchClient()
    response = search_topic(client, query)
    print(f"\nQuery : {response.query}")
    if response.answer:
        print(f"Answer: {response.answer}\n")
    for i, r in enumerate(response.results, 1):
        print(f"[{i}] {r.title}  (score={r.score:.2f})")
        print(f"    {r.url}")
        print(f"    {r.content[:200]}…\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="AI Trading Agent")
    sub    = parser.add_subparsers(dest="command")

    # analyse sub-command
    p_analyse = sub.add_parser("analyse", help="Run market analysis")
    p_analyse.add_argument(
        "--tickers", nargs="+", metavar="TICKER",
        help="Tickers to analyse (default: watch list in config/settings.py)"
    )

    # search sub-command
    p_search = sub.add_parser("search", help="Ad-hoc Tavily search")
    p_search.add_argument("query", help="Search query string")

    args = parser.parse_args()

    if args.command == "search":
        cmd_search(args.query)
    elif args.command == "analyse":
        cmd_analyse(args.tickers or [])
    else:
        # Default: run full analysis on watch list
        cmd_analyse([])


if __name__ == "__main__":
    main()
