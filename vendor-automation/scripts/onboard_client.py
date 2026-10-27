#!/usr/bin/env python3
"""
Client Onboarding for Hermes FT Production Bot

New clients are created under Active/clients/ or Builders/clients/.

Usage (via Hermes bot):
    onboard_client.py "Acme Corp" --group Active
    onboard_client.py "Smith Construction" --group Builders
"""

import argparse
import json
import os
import sys

import requests

# Configuration
CLIENTS_DRIVE_ID = os.environ.get(
    'SHAREPOINT_CLIENTS_DRIVE_ID',
    'b!7eSO3vWOJUy9k6SRlTFyRPKrGEYd7ZZHqggrqWBQTrGOFlrZqhzQT5l0l3PAHJ80'
)
TENANT_ID = os.environ.get('SHAREPOINT_TENANT_ID')
CLIENT_ID = os.environ.get('SHAREPOINT_CLIENT_ID')
CLIENT_SECRET = os.environ.get('SHAREPOINT_CLIENT_SECRET')

FOLDER_STRUCTURES = {
    "active": [
        "Proposal",
        "Accounting",
        "Contract with FT",
        "PC",
    ],
    "builders": [
        "Accounting",
        "Bids",
        "Documents",
        "Plan",
        "Specs",
        "Change Orders",
        "Chief",
        "Cabinet Drawings",
        "Contract with FT",
        "Electrical walk notes",
        "Inspection",
        "Notes",
        "Emails",
        "Photos",
        "MOF",
        "WOF",
        "Purchase Status",
        "Selection Sheet",
        "PC",
    ],
}


def get_token() -> str:
    url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
    data = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope": "https://graph.microsoft.com/.default",
    }
    resp = requests.post(url, data=data)
    resp.raise_for_status()
    return resp.json()["access_token"]


def get_folder_id(drive_id: str, folder_path: str, token: str) -> str | None:
    path = folder_path.strip('/')
    encoded_path = requests.utils.quote(path, safe='')
    url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root:/{encoded_path}"
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(url, headers=headers)
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    return resp.json()["id"]


def create_folder(drive_id: str, parent_id: str, folder_name: str, token: str) -> dict:
    url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/items/{parent_id}/children"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    data = {
        "name": folder_name,
        "folder": {},
        "@microsoft.graph.conflictBehavior": "rename",
    }
    resp = requests.post(url, headers=headers, json=data)
    resp.raise_for_status()
    return resp.json()


def ensure_folder(drive_id: str, parent_id: str, folder_path: str, token: str) -> str:
    """Return folder ID, creating parent folders as needed along the path."""
    existing_id = get_folder_id(drive_id, folder_path, token)
    if existing_id:
        print(f"Found existing folder: {folder_path}")
        return existing_id
    folder_name = folder_path.split('/')[-1]
    result = create_folder(drive_id, parent_id, folder_name, token)
    print(f"Created folder: {folder_path}")
    return result["id"]


def onboard_client(client_name: str, group: str) -> dict:
    if not all([TENANT_ID, CLIENT_ID, CLIENT_SECRET]):
        raise ValueError("Missing SharePoint credentials. Check environment variables.")

    client_type = group.lower()
    if client_type not in FOLDER_STRUCTURES:
        raise ValueError(f"Invalid group: {group}. Must be 'Active' or 'Builders'")

    group_folder = group.capitalize()
    if client_type == "builders":
        clients_folder = f"{group_folder}/~~Builders"
    else:
        clients_folder = f"{group_folder}/clients"
    client_path = f"{clients_folder}/{client_name}"

    folders = FOLDER_STRUCTURES[client_type]
    token = get_token()

    # Ensure Active/clients or Builders/~~Builders exists
    group_id = ensure_folder(CLIENTS_DRIVE_ID, "root", group_folder, token)
    clients_id = ensure_folder(CLIENTS_DRIVE_ID, group_id, clients_folder, token)

    try:
        client_folder = create_folder(CLIENTS_DRIVE_ID, clients_id, client_name, token)
        client_folder_id = client_folder["id"]
        print(f"Created client folder: {client_name}")
    except requests.HTTPError as e:
        if e.response.status_code == 409:
            client_folder_id = get_folder_id(CLIENTS_DRIVE_ID, client_path, token)
            print(f"Client folder already exists: {client_name}")
        else:
            raise

    created = []
    errors = []
    for folder_name in folders:
        try:
            create_folder(CLIENTS_DRIVE_ID, client_folder_id, folder_name, token)
            created.append(folder_name)
            print(f"  ✓ {folder_name}")
        except Exception as e:
            errors.append({"folder": folder_name, "error": str(e)})
            print(f"  ✗ {folder_name}: {e}")

    return {
        "client_name": client_name,
        "group": group_folder,
        "client_path": client_path,
        "client_type": client_type,
        "created_folders": created,
        "errors": errors,
        "status": "success" if not errors else "partial",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Client Onboarding for Hermes FT")
    parser.add_argument("client_name", help="Name of the new client")
    parser.add_argument("--group", choices=["Active", "Builders"],
                        help="Client group (Active or Builders). If omitted, you will be asked.")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    args = parser.parse_args()

    group = args.group
    if group is None:
        prompt = "Which directory for '" + args.client_name + "'? [1] Active  [2] Builders: "
        while True:
            try:
                answer = input(prompt).strip()
            except EOFError:
                print("No directory given; aborting.")
                sys.exit(1)
            if answer in ("1", "Active", "active"):
                group = "Active"
                break
            if answer in ("2", "Builders", "builders"):
                group = "Builders"
                break
            print("Please choose 1 (Active) or 2 (Builders).")

    try:
        result = onboard_client(args.client_name, group)
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            icon = "✅" if not result["errors"] else "⚠️"
            print(f"\n{icon} Onboarding: {result['status']}")
            print(f"Created {len(result['created_folders'])} folders under {result['client_path']}")
            if result["errors"]:
                print(f"Errors: {len(result['errors'])}")
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
