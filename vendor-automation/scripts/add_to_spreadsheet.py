#!/usr/bin/env python3
"""
Add a product/item to a client's pencil-copy spreadsheet in SharePoint.
"""

import argparse
import json
import os
import sys
import requests

TENANT_ID = os.environ.get('SHAREPOINT_TENANT_ID')
CLIENT_ID = os.environ.get('SHAREPOINT_CLIENT_ID')
CLIENT_SECRET = os.environ.get('SHAREPOINT_CLIENT_SECRET')


def get_token() -> str:
    url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
    data = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope": "https://graph.microsoft.com/.default"
    }
    resp = requests.post(url, data=data)
    resp.raise_for_status()
    return resp.json()["access_token"]


def find_or_create_spreadsheet(drive_id: str, client_path: str, token: str) -> str:
    """Find existing 'Pencil Copy.xlsx' or return None to signal manual creation needed."""
    encoded_path = requests.utils.quote(f"{client_path}/Pencil Copy.xlsx", safe='')
    url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root:/{encoded_path}"
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        return resp.json()["id"]
    return None


def main():
    parser = argparse.ArgumentParser(description="Add item to client pencil copy spreadsheet")
    parser.add_argument("--client", required=True, help="Client name")
    parser.add_argument("--vendor", required=True, help="Vendor name")
    parser.add_argument("--item", required=True, help="Item/product name")
    parser.add_argument("--description", default="", help="Item description")
    parser.add_argument("--quantity", default="1", help="Quantity")
    parser.add_argument("--price", default="", help="Price")
    parser.add_argument("--image-url", default="", help="Product image URL")
    parser.add_argument("--group", default="Active", choices=["Active", "Builders"])
    args = parser.parse_args()

    if not all([TENANT_ID, CLIENT_ID, CLIENT_SECRET]):
        raise ValueError("Missing SharePoint credentials")

    token = get_token()
    print(f"Adding item for client {args.client} ({args.group})")
    print(f"  Vendor: {args.vendor}")
    print(f"  Item: {args.item}")
    print(f"  Description: {args.description}")
    print(f"  Quantity: {args.quantity}")
    print(f"  Price: {args.price}")
    print(f"  Image URL: {args.image_url or '(none)'}")

    # Placeholder: full spreadsheet row append requires Excel Graph workbook-session logic.
    # For now, report what would be added so the operator can confirm.
    print("\nNote: Automated spreadsheet append is not yet implemented. "
          "Please add the above details to the client's Pencil Copy.xlsx manually.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
