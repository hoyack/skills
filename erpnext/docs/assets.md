# Assets Module

## Asset

Track fixed assets — computers, vehicles, machinery, furniture, etc.

### Key Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | Data | Asset ID (e.g., `ACC-ASS-2026-00001`) |
| `asset_name` | Data | Display name |
| `item_code` | Link | Item reference (must be fixed asset item) |
| `company` | Link | Owning company |
| `location` | Link | Physical location |
| `custodian` | Link (Employee) | Responsible employee |
| `department` | Link | Department |
| `purchase_date` | Date | Acquisition date |
| `gross_purchase_amount` | Currency | Purchase price |
| `asset_value` | Currency | Current book value |
| `status` | Select | `Draft`, `Submitted`, `Partially Depreciated`, `Fully Depreciated`, `Sold`, `Scrapped`, `In Maintenance`, `Out of Order` |
| `depreciation_method` | Select | `Straight Line`, `Double Declining Balance`, `Written Down Value`, `Manual` |
| `total_number_of_depreciations` | Int | Total depreciation periods |
| `frequency_of_depreciation` | Int | Months between depreciation entries |
| `expected_value_after_useful_life` | Currency | Salvage value |
| `docstatus` | Int | 0=Draft, 1=Submitted |

### Examples

```bash
# List assets
curl -s "$BASE/api/resource/Asset?fields=[\"name\",\"asset_name\",\"status\",\"gross_purchase_amount\",\"asset_value\",\"location\"]" \
  -H "$AUTH"

# Create asset
curl -X POST "$BASE/api/resource/Asset" \
  -H "$AUTH" -H "Content-Type: application/json" \
  -d '{
    "asset_name": "MacBook Pro 16",
    "item_code": "LAPTOP-001",
    "company": "Hoyack",
    "purchase_date": "2026-04-01",
    "gross_purchase_amount": 3500,
    "depreciation_method": "Straight Line",
    "total_number_of_depreciations": 36,
    "frequency_of_depreciation": 1,
    "expected_value_after_useful_life": 500
  }'

# Active assets by location
curl -s "$BASE/api/resource/Asset?filters=[[\"status\",\"not in\",[\"Sold\",\"Scrapped\"]]]&fields=[\"name\",\"asset_name\",\"location\",\"asset_value\"]" \
  -H "$AUTH"
```

---

## Asset Movement

Track transfers of assets between locations, employees, or departments.

### Key Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | Data | Auto-ID |
| `purpose` | Select | `Transfer`, `Receipt`, `Issue` |
| `transaction_date` | Date | Movement date |
| `assets` | Table (Asset Movement Item) | Assets being moved |

### Asset Movement Item (child table)

| Field | Type | Description |
|-------|------|-------------|
| `asset` | Link | Asset reference |
| `source_location` | Link | From location |
| `target_location` | Link | To location |
| `from_employee` | Link | From custodian |
| `to_employee` | Link | To custodian |

### Examples

```bash
# Transfer asset to new location
curl -X POST "$BASE/api/resource/Asset%20Movement" \
  -H "$AUTH" -H "Content-Type: application/json" \
  -d '{
    "purpose": "Transfer",
    "transaction_date": "2026-04-05",
    "assets": [
      {
        "asset": "ACC-ASS-2026-00001",
        "source_location": "Office A",
        "target_location": "Office B"
      }
    ]
  }'
```

---

## Asset Maintenance

Schedule and track preventive maintenance for assets.

### Key Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | Data | Auto-ID |
| `asset_name` | Link | Asset reference |
| `maintenance_team` | Link | Assigned team |
| `maintenance_tasks` | Table | Scheduled tasks |

### Examples

```bash
# List asset maintenance records
curl -s "$BASE/api/resource/Asset%20Maintenance?fields=[\"name\",\"asset_name\",\"maintenance_team\"]" \
  -H "$AUTH"
```

---

## Asset Depreciation Reports

```bash
# Fixed Asset Register
curl -s "$BASE/api/method/frappe.desk.query_report.run" \
  -H "$AUTH" -H "Content-Type: application/json" \
  -d '{"report_name":"Fixed Asset Register","filters":{"company":"Hoyack"}}'
```
