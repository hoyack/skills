#!/usr/bin/env python3
"""Verify SearXNG connectivity and basic search functionality."""

import argparse
import json
import sys
import urllib.parse
import urllib.request
import urllib.error


def check_health(base_url: str) -> bool:
    """Check SearXNG health endpoint."""
    health_urls = [
        f"{base_url.rstrip('/')}/healthz",
        f"{base_url.rstrip('/')}/",
    ]
    for url in health_urls:
        try:
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=10) as resp:
                print(f"  Health check: {url} -> HTTP {resp.status}")
                return True
        except urllib.error.HTTPError as e:
            if e.code in (200, 301, 302):
                print(f"  Health check: {url} -> HTTP {e.code}")
                return True
            print(f"  Health check failed: {url} -> HTTP {e.code}")
        except Exception as e:
            print(f"  Health check failed: {url} -> {e}")
    return False


def test_search(base_url: str, query: str = "openclaw") -> bool:
    """Perform a test search query."""
    search_url = f"{base_url.rstrip('/')}/search?q={urllib.parse.quote(query)}&format=json"
    try:
        req = urllib.request.Request(
            search_url,
            headers={"Accept": "application/json"},
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            results = data.get("results", [])
            print(f"  Search test: '{query}' -> {len(results)} results")
            if results:
                print(f"  Top result: {results[0].get('title', 'N/A')}")
            return len(results) > 0
    except Exception as e:
        print(f"  Search test failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Verify SearXNG connectivity")
    parser.add_argument("--url", required=True, help="SearXNG base URL")
    parser.add_argument("--query", default="openclaw", help="Test search query")
    args = parser.parse_args()

    print(f"Verifying SearXNG at: {args.url}")

    health_ok = check_health(args.url)
    if not health_ok:
        print("ERROR: SearXNG health check failed.")
        sys.exit(1)

    search_ok = test_search(args.url, args.query)
    if not search_ok:
        print("WARNING: Search returned no results (may be normal for some queries).")

    print("SearXNG verification complete.")
    sys.exit(0 if health_ok else 1)


if __name__ == "__main__":
    main()
