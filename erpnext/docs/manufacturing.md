# Manufacturing Module

## BOM (Bill of Materials)

Defines the raw materials and operations needed to manufacture a finished product.

### Key Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | Data | Auto-ID (e.g., `BOM-SKU001-001`) |
| `item` | Link | Finished item |
| `quantity` | Float | Quantity produced per BOM |
| `is_active` | Check | Active BOM |
| `is_default` | Check | Default BOM for this item |
| `items` | Table (BOM Item) | Raw material list |
| `operations` | Table (BOM Operation) | Manufacturing operations |
| `total_cost` | Currency | Total material + operation cost |
| `docstatus` | Int | 0=Draft, 1=Submitted |

### BOM Item (child table)

| Field | Type | Description |
|-------|------|-------------|
| `item_code` | Link | Raw material item |
| `qty` | Float | Quantity required |
| `rate` | Currency | Unit cost |
| `amount` | Currency | Line total |
| `source_warehouse` | Link | Source warehouse |

### Examples

```bash
# List BOMs
curl -s "$BASE/api/resource/BOM?fields=[\"name\",\"item\",\"quantity\",\"total_cost\",\"is_active\",\"is_default\"]" \
  -H "$AUTH"

# Get BOM with materials
curl -s "$BASE/api/resource/BOM/BOM-SKU001-001" -H "$AUTH"

# Create BOM
curl -X POST "$BASE/api/resource/BOM" \
  -H "$AUTH" -H "Content-Type: application/json" \
  -d '{
    "item": "SKU001",
    "company": "Hoyack (Demo)",
    "quantity": 1,
    "items": [
      {"item_code": "RAW-001", "qty": 2, "rate": 50},
      {"item_code": "RAW-002", "qty": 1, "rate": 100}
    ]
  }'
```

---

## Work Order

Production order to manufacture items based on a BOM.

### Key Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | Data | Auto-ID |
| `production_item` | Link | Item to manufacture |
| `bom_no` | Link | BOM reference |
| `qty` | Float | Quantity to produce |
| `company` | Link | Manufacturing company |
| `planned_start_date` | Datetime | Planned start |
| `actual_start_date` | Datetime | Actual start |
| `actual_end_date` | Datetime | Actual completion |
| `produced_qty` | Float | Quantity produced so far |
| `status` | Select | Draft, Not Started, In Process, Completed, Stopped, Cancelled |
| `wip_warehouse` | Link | Work in progress warehouse |
| `fg_warehouse` | Link | Finished goods warehouse |

### Examples

```bash
# List work orders
curl -s "$BASE/api/resource/Work%20Order?fields=[\"name\",\"production_item\",\"qty\",\"produced_qty\",\"status\"]" \
  -H "$AUTH"

# Create work order
curl -X POST "$BASE/api/resource/Work%20Order" \
  -H "$AUTH" -H "Content-Type: application/json" \
  -d '{
    "production_item": "SKU001",
    "bom_no": "BOM-SKU001-001",
    "qty": 100,
    "company": "Hoyack (Demo)",
    "wip_warehouse": "Work In Progress - HOKD",
    "fg_warehouse": "Finished Goods - HOKD"
  }'
```

---

## Job Card

Tracks individual operations within a Work Order at workstation level.

### Key Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | Data | Auto-ID |
| `work_order` | Link | Parent work order |
| `operation` | Link | Operation name |
| `workstation` | Link | Workstation |
| `for_quantity` | Float | Quantity for this job |
| `time_logs` | Table | Start/end time records |
| `status` | Select | Open, Work In Progress, Completed, On Hold, Material Transferred |

### Examples

```bash
# List job cards for a work order
curl -s "$BASE/api/resource/Job%20Card?filters=[[\"work_order\",\"=\",\"MFG-WO-2026-00001\"]]&fields=[\"name\",\"operation\",\"status\",\"for_quantity\"]" \
  -H "$AUTH"
```
