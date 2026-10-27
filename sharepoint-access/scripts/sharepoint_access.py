#!/usr/bin/env python3
"""
SharePoint Access Control Module

Enforces drive-level restrictions for the Hermes FT production bot.
Only allows access to drives listed in SHAREPOINT_ALLOWED_DRIVE_IDS.
"""

import os
import sys
import requests
from typing import Optional, List, Dict, Any


class SharePointAccessError(Exception):
    """Raised when a SharePoint access policy is violated."""
    pass


class SharePointClient:
    """SharePoint client with drive-level access control."""
    
    def __init__(self):
        self.client_id = os.environ.get('SHAREPOINT_CLIENT_ID')
        self.client_secret = os.environ.get('SHAREPOINT_CLIENT_SECRET')
        self.tenant_id = os.environ.get('SHAREPOINT_TENANT_ID')
        self.hostname = os.environ.get('SHAREPOINT_HOSTNAME', 'finishingtouches.sharepoint.com')
        
        # Parse allowed drive IDs from comma-separated env var
        allowed_ids_str = os.environ.get('SHAREPOINT_ALLOWED_DRIVE_IDS', '')
        self.allowed_drive_ids = {id.strip() for id in allowed_ids_str.split(',') if id.strip()}
        
        allowed_names_str = os.environ.get('SHAREPOINT_ALLOWED_DRIVE_NAMES', '')
        self.allowed_drive_names = {name.strip() for name in allowed_names_str.split(',') if name.strip()}
        
        self._token: Optional[str] = None
        
    def _get_token(self) -> str:
        """Get Microsoft Graph access token."""
        if self._token:
            return self._token
            
        if not all([self.client_id, self.client_secret, self.tenant_id]):
            raise SharePointAccessError(
                "Missing credentials. Ensure SHAREPOINT_CLIENT_ID, "
                "SHAREPOINT_CLIENT_SECRET, and SHAREPOINT_TENANT_ID are set."
            )
        
        url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": "https://graph.microsoft.com/.default"
        }
        
        resp = requests.post(url, data=data)
        if resp.status_code != 200:
            raise SharePointAccessError(f"Token acquisition failed: {resp.status_code} - {resp.text}")
        
        self._token = resp.json()["access_token"]
        return self._token
    
    def _validate_drive_id(self, drive_id: str) -> None:
        """Validate that a drive ID is in the allowed list."""
        if not self.allowed_drive_ids:
            raise SharePointAccessError(
                "No allowed drive IDs configured. "
                "Set SHAREPOINT_ALLOWED_DRIVE_IDS environment variable."
            )
        
        if drive_id not in self.allowed_drive_ids:
            raise SharePointAccessError(
                f"Access DENIED to drive ID: {drive_id}. "
                f"Allowed drives: {', '.join(sorted(self.allowed_drive_ids))}"
            )
    
    def _extract_drive_id_from_path(self, path: str) -> Optional[str]:
        """Extract drive ID from API path if present."""
        # Patterns like: /drives/{drive_id}/... or /drives/{drive_id}
        import re
        match = re.search(r'/drives/([^/]+)', path)
        if match:
            return match.group(1)
        return None
    
    def request(self, method: str, path: str, **kwargs) -> Dict[str, Any]:
        """
        Make a validated SharePoint/Graph API request.
        """
        # Ensure full path before extracting drive ID
        if not path.startswith('https://'):
            full_path = f"https://graph.microsoft.com/v1.0/{path.lstrip('/')}"
        else:
            full_path = path
        
        # Validate drive ID if present in path
        drive_id = self._extract_drive_id_from_path(full_path)
        if drive_id:
            self._validate_drive_id(drive_id)
        
        token = self._get_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        resp = requests.request(method, full_path, headers=headers, **kwargs)
        
        if resp.status_code >= 400:
            raise SharePointAccessError(
                f"SharePoint API error: {resp.status_code} - {resp.text}"
            )
        
        return resp.json()
    
    def list_allowed_drives(self, site_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all drives that are accessible (allowed ones)."""
        if not site_id:
            # Try to get site by hostname
            site_resp = self.request(
                "GET", 
                f"sites/{self.hostname}:/sites/CompanyFiles"
            )
            site_id = site_resp["id"]
        
        drives_resp = self.request("GET", f"sites/{site_id}/drives")
        all_drives = drives_resp.get("value", [])
        
        # Filter to only allowed drives
        allowed = [
            drive for drive in all_drives
            if drive.get("id") in self.allowed_drive_ids
        ]
        
        return allowed
    
    def get_drive_items(self, drive_id: str, path: str = "root/children") -> Dict[str, Any]:
        """Get items from a specific drive."""
        self._validate_drive_id(drive_id)
        return self.request("GET", f"drives/{drive_id}/{path}")
    
    def search_drive(self, drive_id: str, query: str) -> Dict[str, Any]:
        """Search within a specific drive."""
        self._validate_drive_id(drive_id)
        return self.request(
            "GET", 
            f"drives/{drive_id}/search(q='{query}')"
        )


# Global client instance
_client: Optional[SharePointClient] = None


def get_client() -> SharePointClient:
    """Get or create the global SharePoint client."""
    global _client
    if _client is None:
        _client = SharePointClient()
    return _client


def sharepoint_request(method: str, path: str, **kwargs) -> Dict[str, Any]:
    """Convenience function for making validated SharePoint requests."""
    return get_client().request(method, path, **kwargs)


def main():
    """CLI interface for SharePoint access control."""
    import argparse
    
    parser = argparse.ArgumentParser(description="SharePoint Access Control")
    parser.add_argument("--token", action="store_true", help="Get access token")
    parser.add_argument("--list-drives", action="store_true", help="List allowed drives")
    parser.add_argument("--query", help="Query path (e.g., 'drives/ID/root/children')")
    parser.add_argument("--drive-id", help="Specific drive ID to query")
    parser.add_argument("--method", default="GET", help="HTTP method")
    
    args = parser.parse_args()
    
    try:
        client = get_client()
        
        if args.token:
            token = client._get_token()
            print(f"Token acquired: {token[:50]}...")
            print(f"Token length: {len(token)}")
            
        elif args.list_drives:
            print("Fetching allowed drives...")
            drives = client.list_allowed_drives()
            print(f"\nAllowed drives ({len(drives)}):")
            for drive in drives:
                print(f"  📁 {drive['name']}")
                print(f"     ID: {drive['id']}")
                print(f"     URL: {drive.get('webUrl', 'N/A')}")
                print()
                
        elif args.query:
            result = client.request(args.method, args.query)
            import json
            print(json.dumps(result, indent=2))
            
        elif args.drive_id:
            result = client.get_drive_items(args.drive_id)
            import json
            print(json.dumps(result, indent=2))
            
        else:
            print("SharePoint Access Control Module")
            print(f"Allowed drives: {', '.join(sorted(client.allowed_drive_names))}")
            print(f"Allowed drive IDs: {len(client.allowed_drive_ids)} configured")
            
    except SharePointAccessError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
