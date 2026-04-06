# Selling Module

## Customer

The primary customer/client record.

### Key Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | Data | Auto-generated ID or customer name |
| `customer_name` | Data | Display name |
| `customer_type` | Select | `Company`, `Individual` |
| `customer_group` | Link | Customer group classification |
| `territory` | Link | Territory assignment |
| `default_currency` | Link | Default transaction currency |
| `default_price_list` | Link | Default price list |
| `tax_id` | Data | Tax identification number |
| `account_manager` | Link (User) | Assigned account manager |
| `disabled` | Check | Whether customer is active |
| `image` | Attach Image | Customer logo |

### Examples

```bash
AUTH="Authorization: token $ERPNEXT_API_KEY:$ERPNEXT_API_SECRET"
BASE="$ERPNEXT_BASE_URL"

# List customers
curl -s "$BASE/api/resource/Customer?fields=[\"name\",\"customer_name\",\"customer_group\",\"territory\",\"customer_type\"]&limit_page_length=20" \
  -H "$AUTH"

# Get customer detail
curl -s "$BASE/api/resource/Customer/Grant%20Plastics%20Ltd." -H "$AUTH"

# Create customer
curl -X POST "$BASE/api/resource/Customer" \
  -H "$AUTH" -H "Content-Type: application/json" \
  -d '{"customer_name":"Acme Corp","customer_type":"Company","customer_group":"Commercial","territory":"United States"}'

# Update customer
curl -X PUT "$BASE/api/resource/Customer/Acme%20Corp" \
  -H "$AUTH" -H "Content-Type: application/json" \
  -d '{"territory":"Europe"}'

# Search customers
curl -s "$BASE/api/method/frappe.desk.search.search_link?doctype=Customer&txt=Grant" -H "$AUTH"
```

---

## Sales Order

A confirmed order from a customer before delivery and invoicing.

### Key Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | Data | Auto-ID (e.g., `SAL-ORD-2026-00001`) |
| `customer` | Link | Customer reference |
| `transaction_date` | Date | Order date |
| `delivery_date` | Date | Expected delivery |
| `company` | Link | Selling company |
| `currency` | Link | Transaction currency |
| `selling_price_list` | Link | Price list used |
| `items` | Table (Sales Order Item) | Line items |
| `total` | Currency | Total before tax |
| `grand_total` | Currency | Total after tax |
| `status` | Select | Draft, To Deliver and Bill, To Bill, To Deliver, Completed, Cancelled |
| `docstatus` | Int | 0=Draft, 1=Submitted, 2=Cancelled |

### Sales Order Item (child table)

| Field | Type | Description |
|-------|------|-------------|
| `item_code` | Link (Item) | Item reference |
| `item_name` | Data | Item display name |
| `qty` | Float | Quantity ordered |
| `rate` | Currency | Unit price |
| `amount` | Currency | Line total (qty × rate) |
| `uom` | Link | Unit of measure |
| `delivery_date` | Date | Line-level delivery date |
| `warehouse` | Link | Source warehouse |

### Examples

```bash
# List sales orders
curl -s "$BASE/api/resource/Sales%20Order?fields=[\"name\",\"customer\",\"transaction_date\",\"grand_total\",\"status\"]&limit_page_length=20" \
  -H "$AUTH"

# Get full sales order with items
curl -s "$BASE/api/resource/Sales%20Order/SAL-ORD-2026-00001" -H "$AUTH"

# Create sales order
curl -X POST "$BASE/api/resource/Sales%20Order" \
  -H "$AUTH" -H "Content-Type: application/json" \
  -d '{
    "customer": "Grant Plastics Ltd.",
    "company": "Hoyack (Demo)",
    "delivery_date": "2026-05-01",
    "items": [
      {"item_code": "SKU001", "qty": 10, "rate": 400, "delivery_date": "2026-05-01"},
      {"item_code": "SKU002", "qty": 5, "rate": 300, "delivery_date": "2026-05-01"}
    ]
  }'

# Submit sales order (lock it)
POST /api/method/frappe.client.submit
{"doc":{"doctype":"Sales Order","name":"SAL-ORD-2026-00006"}}

# Filter: open orders over $10k
curl -s "$BASE/api/resource/Sales%20Order?filters=[[\"docstatus\",\"=\",1],[\"grand_total\",\">\",10000]]&fields=[\"name\",\"customer\",\"grand_total\",\"status\"]" \
  -H "$AUTH"
```

---

## Quotation

A sales proposal sent to a lead or customer before order confirmation.

### Key Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | Data | Auto-ID |
| `quotation_to` | Select | `Customer` or `Lead` |
| `party_name` | Dynamic Link | Customer or Lead name |
| `transaction_date` | Date | Quotation date |
| `valid_till` | Date | Validity date |
| `items` | Table (Quotation Item) | Line items |
| `grand_total` | Currency | Total amount |
| `status` | Select | Draft, Open, Replied, Ordered, Lost, Cancelled |

### Examples

```bash
# List quotations
curl -s "$BASE/api/resource/Quotation?fields=[\"name\",\"party_name\",\"grand_total\",\"status\",\"valid_till\"]" \
  -H "$AUTH"

# Create quotation
curl -X POST "$BASE/api/resource/Quotation" \
  -H "$AUTH" -H "Content-Type: application/json" \
  -d '{
    "quotation_to": "Customer",
    "party_name": "Grant Plastics Ltd.",
    "company": "Hoyack (Demo)",
    "valid_till": "2026-05-01",
    "items": [
      {"item_code": "SKU001", "qty": 100, "rate": 380}
    ]
  }'
```
