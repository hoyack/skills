# Stock (Inventory) Module

## Item

Master record for products, raw materials, and services.

### Key Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | Data | Item code (e.g., `SKU001`) |
| `item_code` | Data | Same as name |
| `item_name` | Data | Display name |
| `item_group` | Link | Item group classification |
| `stock_uom` | Link | Default unit of measure |
| `is_stock_item` | Check | Maintained in inventory |
| `is_sales_item` | Check | Available for sale |
| `is_purchase_item` | Check | Available for purchase |
| `standard_rate` | Currency | Standard selling rate |
| `valuation_rate` | Currency | Current valuation rate |
| `opening_stock` | Float | Opening stock qty |
| `image` | Attach Image | Item image |
| `description` | Text Editor | Item description |
| `has_variants` | Check | Template with variants |
| `has_serial_no` | Check | Serial number tracking |
| `has_batch_no` | Check | Batch tracking |
| `disabled` | Check | Active/inactive |
| `end_of_life` | Date | End of life date |

### Examples

```bash
# List items with key fields
curl -s "$BASE/api/method/frappe.client.get_list" \
  -H "$AUTH" -H "Content-Type: application/json" \
  -d '{"doctype":"Item","fields":["name","item_name","item_group","stock_uom","valuation_rate","is_stock_item"],"limit_page_length":20}'

# Get item detail
curl -s "$BASE/api/resource/Item/SKU001" -H "$AUTH"

# Create item
curl -X POST "$BASE/api/resource/Item" \
  -H "$AUTH" -H "Content-Type: application/json" \
  -d '{
    "item_code": "WIDGET-001",
    "item_name": "Steel Widget",
    "item_group": "Raw Material",
    "stock_uom": "Nos",
    "is_stock_item": 1,
    "is_purchase_item": 1,
    "is_sales_item": 1,
    "standard_rate": 150
  }'

# Search items
curl -s "$BASE/api/method/frappe.desk.search.search_link?doctype=Item&txt=Laptop" -H "$AUTH"

# Item count
curl -s "$BASE/api/method/frappe.client.get_count" \
  -H "$AUTH" -H "Content-Type: application/json" \
  -d '{"doctype":"Item"}'
```

---

## Warehouse

Physical or logical storage locations.

### Key Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | Data | Warehouse name with abbreviation (e.g., `Stores - HOK`) |
| `warehouse_name` | Data | Display name |
| `company` | Link | Owning company |
| `parent_warehouse` | Link | Parent in hierarchy |
| `is_group` | Check | Group warehouse flag |
| `disabled` | Check | Active/inactive |

### Examples

```bash
# List warehouses
curl -s "$BASE/api/resource/Warehouse?fields=[\"name\",\"warehouse_name\",\"company\",\"is_group\"]" \
  -H "$AUTH"
```

---

## Stock Entry

Movement of stock between warehouses, production, etc.

### Key Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | Data | Auto-ID |
| `stock_entry_type` | Select | `Material Receipt`, `Material Issue`, `Material Transfer`, `Manufacture`, `Repack`, `Send to Subcontractor` |
| `posting_date` | Date | Entry date |
| `from_warehouse` | Link | Source warehouse |
| `to_warehouse` | Link | Target warehouse |
| `items` | Table (Stock Entry Detail) | Line items |

### Examples

```bash
# Material receipt (add stock)
curl -X POST "$BASE/api/resource/Stock%20Entry" \
  -H "$AUTH" -H "Content-Type: application/json" \
  -d '{
    "stock_entry_type": "Material Receipt",
    "company": "Hoyack (Demo)",
    "to_warehouse": "Stores - HOKD",
    "items": [
      {"item_code": "SKU001", "qty": 100, "basic_rate": 400}
    ]
  }'

# Material transfer between warehouses
curl -X POST "$BASE/api/resource/Stock%20Entry" \
  -H "$AUTH" -H "Content-Type: application/json" \
  -d '{
    "stock_entry_type": "Material Transfer",
    "company": "Hoyack (Demo)",
    "items": [
      {"item_code": "SKU001", "qty": 20, "s_warehouse": "Stores - HOKD", "t_warehouse": "Finished Goods - HOKD"}
    ]
  }'
```

---

## Delivery Note

Shipment of goods to a customer (often from a Sales Order).

### Key Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | Data | Auto-ID |
| `customer` | Link | Customer reference |
| `posting_date` | Date | Delivery date |
| `items` | Table | Delivered items |
| `status` | Select | Draft, To Bill, Completed, Cancelled, Return |

---

## Purchase Receipt

Receipt of goods from a supplier (often from a Purchase Order).

### Key Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | Data | Auto-ID |
| `supplier` | Link | Supplier reference |
| `posting_date` | Date | Receipt date |
| `items` | Table | Received items |
| `status` | Select | Draft, To Bill, Completed, Cancelled, Return |

---

## Stock Reports

```bash
# Stock Balance
curl -s "$BASE/api/method/frappe.desk.query_report.run" \
  -H "$AUTH" -H "Content-Type: application/json" \
  -d '{"report_name":"Stock Balance","filters":{"company":"Hoyack (Demo)"}}'

# Stock Ledger
curl -s "$BASE/api/method/frappe.desk.query_report.run" \
  -H "$AUTH" -H "Content-Type: application/json" \
  -d '{"report_name":"Stock Ledger","filters":{"company":"Hoyack (Demo)","from_date":"2026-01-01","to_date":"2026-12-31"}}'

# Stock Projected Qty
curl -s "$BASE/api/method/frappe.desk.query_report.run" \
  -H "$AUTH" -H "Content-Type: application/json" \
  -d '{"report_name":"Stock Projected Qty","filters":{"company":"Hoyack (Demo)"}}'
```
