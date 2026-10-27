# vendor-automation

Vendor lookup and client onboarding automation for Rachel FT (Hermes FT production bot).

## Description

This skill provides command-line scripts that Rachel FT uses to look up vendors, search across
vendor records, and onboard new active/builder clients into SharePoint.

## Scripts

- `vendor_lookup.py` — Look up a vendor by name or category.
- `cross_vendor_search.py` — Search across multiple vendor fields.
- `create_client_directory.py` — Create the standard SharePoint folder structure for a client.
- `add_to_spreadsheet.py` — Add/update vendor or client data in spreadsheets.
- `onboard_client.py` — Full onboarding flow for a new client (Active or Builders).

## Usage (via Hermes FT)

```
onboard_client.py "Client Name" --group Active
onboard_client.py "Client Name" --group Builders
vendor_lookup.py --help
cross_vendor_search.py --help
```

## Environment

Scripts expect the following environment variables to be available in the Hermes FT pod:

- `SHAREPOINT_TENANT_ID`
- `SHAREPOINT_CLIENT_ID`
- `SHAREPOINT_CLIENT_SECRET`
- `SHAREPOINT_CLIENTS_DRIVE_ID`

Vendor credentials are read from the `vendor-credentials` Secret mounted in the pod.
