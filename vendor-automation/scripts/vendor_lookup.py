#!/usr/bin/env python3
"""
Vendor lookup for Hermes FT Production Bot.

Reads the vendor credentials file and returns the list of configured vendors.
"""

import json
import os
import sys
from pathlib import Path

CREDENTIALS_PATH = os.environ.get(
    "VENDOR_CREDENTIALS_PATH",
    "/opt/data/vendor-credentials/credentials.json"
)


def load_vendors():
    if not os.path.exists(CREDENTIALS_PATH):
        raise FileNotFoundError(f"Vendor credentials file not found: {CREDENTIALS_PATH}")

    with open(CREDENTIALS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    vendors = data.get("vendors", [])
    if not isinstance(vendors, list):
        raise ValueError("Invalid credentials format: 'vendors' must be a list")

    return vendors


def format_vendor(v):
    name = v.get("name") or v.get("vendor_name") or v.get("company") or "Unknown"
    website = v.get("website", "")
    category = v.get("category", "")
    parts = [name]
    if category:
        parts.append(f"[{category}]")
    if website:
        parts.append(f"- {website}")
    return " ".join(parts)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="List configured vendors")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--category", help="Filter by category")
    args = parser.parse_args()

    vendors = load_vendors()

    if args.category:
        vendors = [v for v in vendors if args.category.lower() in (v.get("category", "")).lower()]

    if args.json:
        print(json.dumps(vendors, indent=2))
        return

    if not vendors:
        print("No vendors found.")
        return

    print(f"Found {len(vendors)} vendors:\n")
    for v in vendors:
        print(format_vendor(v))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
