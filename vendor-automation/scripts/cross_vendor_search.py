#!/usr/bin/env python3
"""
Cross-vendor product search for Hermes FT Production Bot.

Searches configured vendor websites for a product/item description.
"""

import argparse
import json
import os
import sys
import requests
from urllib.parse import quote_plus

CREDENTIALS_PATH = os.environ.get(
    "VENDOR_CREDENTIALS_PATH",
    "/opt/data/vendor-credentials/credentials.json"
)


def load_vendors():
    with open(CREDENTIALS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("vendors", [])


def main():
    parser = argparse.ArgumentParser(description="Search across vendor catalogs")
    parser.add_argument("query", help="Product or item to search for")
    parser.add_argument("--vendors", help="Comma-separated vendor names (default: all)")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    args = parser.parse_args()

    vendors = load_vendors()

    if args.vendors:
        wanted = {v.strip().lower() for v in args.vendors.split(",")}
        vendors = [v for v in vendors if (v.get("name") or "").lower() in wanted]

    results = []
    for v in vendors:
        name = v.get("name", "Unknown")
        website = v.get("website", "")
        results.append({
            "vendor": name,
            "website": website,
            "query": args.query,
            "note": "Automated website extraction is not yet implemented. "
                    "Please visit the vendor website and search manually."
        })

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print(f"Cross-vendor search: '{args.query}'")
        for r in results:
            print(f"\n- {r['vendor']}: {r['website'] or 'no website configured'}")
            print(f"  {r['note']}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
