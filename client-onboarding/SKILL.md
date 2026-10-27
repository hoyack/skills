---
name: client-onboarding
version: 1.0.0
author: Spartacus
license: MIT
platforms: [linux]
prerequisites:
  env_vars:
    - SHAREPOINT_TENANT_ID
    - SHAREPOINT_CLIENT_ID
    - SHAREPOINT_CLIENT_SECRET
    - SHAREPOINT_CLIENTS_DRIVE_ID
metadata:
  hermes:
    tags: [SharePoint, Client, Onboarding, Folders]
    homepage: https://github.com/hoyack/skills
---

# Client Onboarding for Hermes FT

Automated folder creation for new clients in the SharePoint 'Clients' drive.

## Folder Structures

### Active Clients
```
Active/
  └── [Client Name]/
      ├── Proposal
      ├── Accounting
      ├── Contract with FT
      └── PC
```

### Builders Clients
```
Builders/
  └── [Client Name]/
      ├── Accounting
      ├── Bids
      ├── Documents
      ├── Plan
      ├── Specs
      ├── Change Orders
      ├── Chief
      ├── Cabinet Drawings
      ├── Contract with FT
      ├── Electrical walk notes
      ├── Inspection
      ├── Notes
      ├── Emails
      ├── Photos
      ├── MOF
      ├── WOF
      ├── Purchase Status
      ├── Selection Sheet
      └── PC
```

## Usage

### Command Line
```bash
python scripts/onboard_client.py "Acme Corp" active --parent-folder "Active"
python scripts/onboard_client.py "Smith Construction" builders --parent-folder "Builders"
```

### From Hermes Bot
The bot can invoke this skill when users request:
- "Onboard a new active client called 'Acme Corp'"
- "Create a builders folder for 'Smith Construction'"
- "Set up a new client 'XYZ Corp' in Active"

## Environment Variables

| Variable | Description |
|----------|-------------|
| SHAREPOINT_TENANT_ID | Azure AD tenant ID |
| SHAREPOINT_CLIENT_ID | App registration client ID |
| SHAREPOINT_CLIENT_SECRET | App registration client secret |
| SHAREPOINT_CLIENTS_DRIVE_ID | SharePoint drive ID for Clients |

## SharePoint Permissions Required

- `Files.ReadWrite.All` (Application permission)
- `Sites.Read.All` (Application permission)

## Notes

- Folders are created using Microsoft Graph API
- If a folder already exists, it will be skipped (no overwrite)
- The script requires the SharePoint access control skill to be configured
