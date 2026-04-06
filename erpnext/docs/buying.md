# Buying Module

## Supplier

Vendor/supplier records for procurement.

### Key Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | Data | Supplier ID |
| `supplier_name` | Data | Display name |
| `supplier_group` | Link | Supplier group classification |
| `supplier_type` | Select | `Company`, `Individual` |
| `country` | Link | Supplier country |
| `default_currency` | Link | Default currency |
| `tax_id` | Data | Tax identification |
| `disabled` | Check | Active/inactive |

### Examples

```bash
# List suppliers
curl -s "$BASE/api/resource/Supplier?fields=[\"name\",\"supplier_name\",\"supplier_group\",\"country\"]" \
  -H "$AUTH"

# Create supplier
curl -X POST "$BASE/api/resource/Supplier" \
  -H "$AUTH" -H "Content-Type: application/json" \
  -d '{"supplier_name":"Global Parts Inc.","supplier_type":"Company","supplier_group":"Raw Material"}'

# Get supplier detail
curl -s "$BASE/api/resource/Supplier/Summit%20Traders%20Ltd." -H "$AUTH"
```

---

## Purchase Order

An order placed with a supplier for goods or services.

### Key Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | Data | Auto-ID (e.g., `PUR-ORD-2026-00001`) |
| `supplier` | Link | Supplier reference |
| `transaction_date` | Date | Order date |
| `schedule_date` | Date | Expected delivery date |
| `company` | Link | Buying company |
| `items` | Table (Purchase Order Item) | Line items |
| `grand_total` | Currency | Total amount |
| `status` | Select | Draft, To Receive and Bill, To Bill, To Receive, Completed, Cancelled |
| `docstatus` | Int | 0=Draft, 1=Submitted, 2=Cancelled |

### Purchase Order Item (child table)

| Field | Type | Description |
|-------|------|-------------|
| `item_code` | Link (Item) | Item reference |
| `qty` | Float | Quantity |
| `rate` | Currency | Unit price |
| `amount` | Currency | Line total |
| `schedule_date` | Date | Expected receipt date |
| `warehouse` | Link | Target warehouse |

### Examples

```bash
# List purchase orders
curl -s "$BASE/api/resource/Purchase%20Order?fields=[\"name\",\"supplier\",\"transaction_date\",\"grand_total\",\"status\"]&limit_page_length=20" \
  -H "$AUTH"

# Get purchase order detail
curl -s "$BASE/api/resource/Purchase%20Order/PUR-ORD-2026-00008" -H "$AUTH"

# Create purchase order
curl -X POST "$BASE/api/resource/Purchase%20Order" \
  -H "$AUTH" -H "Content-Type: application/json" \
  -d '{
    "supplier": "Summit Traders Ltd.",
    "company": "Hoyack (Demo)",
    "schedule_date": "2026-05-15",
    "items": [
      {"item_code": "SKU003", "qty": 50, "rate": 500, "schedule_date": "2026-05-15", "warehouse": "Stores - HOKD"}
    ]
  }'

# Filter: POs over $5000
curl -s "$BASE/api/resource/Purchase%20Order?filters=[[\"grand_total\",\">\",5000],[\"docstatus\",\"=\",1]]&fields=[\"name\",\"supplier\",\"grand_total\"]" \
  -H "$AUTH"
```

---

## Material Request

Internal request for materials (purchase, transfer, manufacture).

### Key Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | Data | Auto-ID |
| `material_request_type` | Select | `Purchase`, `Material Transfer`, `Material Issue`, `Manufacture`, `Customer Provided` |
| `transaction_date` | Date | Request date |
| `schedule_date` | Date | Required by date |
| `items` | Table | Requested items |
| `status` | Select | Draft, Submitted, Stopped, Cancelled, Pending, Partially Ordered, Ordered, Issued, Transferred, Received |

### Examples

```bash
# List material requests
curl -s "$BASE/api/resource/Material%20Request?fields=[\"name\",\"material_request_type\",\"status\",\"schedule_date\"]" \
  -H "$AUTH"

# Create material request
curl -X POST "$BASE/api/resource/Material%20Request" \
  -H "$AUTH" -H "Content-Type: application/json" \
  -d '{
    "material_request_type": "Purchase",
    "company": "Hoyack (Demo)",
    "schedule_date": "2026-05-01",
    "items": [
      {"item_code": "SKU005", "qty": 100, "schedule_date": "2026-05-01", "warehouse": "Stores - HOKD"}
    ]
  }'
```
