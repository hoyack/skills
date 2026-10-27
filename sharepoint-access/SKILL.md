---
name: sharepoint-access
version: 1.0.0
author: Spartacus
license: MIT
platforms: [linux, macos, windows]
prerequisites:
  env_vars:
    - SHAREPOINT_CLIENT_ID
    - SHAREPOINT_CLIENT_SECRET
    - SHAREPOINT_TENANT_ID
    - SHAREPOINT_HOSTNAME
    - SHAREPOINT_ALLOWED_DRIVE_IDS
    - SHAREPOINT_ALLOWED_DRIVE_NAMES
metadata:
  hermes:
    tags: [SharePoint, Microsoft, Graph, Files, AccessControl]
    homepage: https://github.com/hoyack/skills
---

# SharePoint Access Control

Controlled SharePoint access for the Hermes FT production bot (Rachel).
**RESTRICTED** to only the Clients and Reference Library drives.

## Access Policy

- **Allowed drives:** Clients, Reference Library
- **Blocked drives:** All others (IT, Accounting, Indulge, etc.)
- **Enforcement:** Code-level validation via drive ID whitelist

## Usage

All SharePoint operations MUST use the `sharepoint_request` helper:

```python
from sharepoint_access import sharepoint_request

# This will fail if drive_id is not in the whitelist
result = sharepoint_request("GET", f"/drives/{drive_id}/root/children")
```

## Direct API Access (for terminal tool)

Get token:
```bash
python /opt/hermes/skills/productivity/sharepoint-access/scripts/sharepoint_access.py --token
```

List allowed drives:
```bash
python /opt/hermes/skills/productivity/sharepoint-access/scripts/sharepoint_access.py --list-drives
```

Query allowed drive (replace DRIVE_ID with actual ID):
```bash
python /opt/hermes/skills/productivity/sharepoint-access/scripts/sharepoint_access.py --query "drives/DRIVE_ID/root/children"
```

## Allowed Drive IDs

| Name | ID |
|------|-----|
| Clients | b!7eSO3vWOJUy9k6SRlTFyRPKrGEYd7ZZHqggrqWBQTrGOFlrZqhzQT5l0l3PAHJ80 |
| Reference Library | b!7eSO3vWOJUy9k6SRlTFyRPKrGEYd7ZZHqggrqWBQTrHn5hZMvZwDQIHrY1PhybSF |
