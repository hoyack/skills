# Accounts Module

## Sales Invoice

Invoice issued to a customer for goods/services delivered.

### Key Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | Data | Auto-ID (e.g., `ACC-SINV-2026-00001`) |
| `customer` | Link | Customer reference |
| `customer_name` | Data | Customer display name |
| `company` | Link | Company issuing the invoice |
| `posting_date` | Date | Invoice date |
| `due_date` | Date | Payment due date |
| `currency` | Link | Transaction currency |
| `items` | Table (Sales Invoice Item) | Line items |
| `total` | Currency | Subtotal |
| `grand_total` | Currency | Total with taxes |
| `outstanding_amount` | Currency | Unpaid balance |
| `status` | Select | Draft, Unpaid, Overdue, Paid, Return, Credit Note Issued, Cancelled |
| `is_return` | Check | Credit note flag |
| `docstatus` | Int | 0=Draft, 1=Submitted, 2=Cancelled |

### Examples

```bash
# List invoices
curl -s "$BASE/api/resource/Sales%20Invoice?fields=[\"name\",\"customer\",\"posting_date\",\"grand_total\",\"outstanding_amount\",\"status\"]&limit_page_length=20" \
  -H "$AUTH"

# Get invoice detail (includes items, taxes, payments)
curl -s "$BASE/api/resource/Sales%20Invoice/ACC-SINV-2026-00001" -H "$AUTH"

# Unpaid invoices
curl -s "$BASE/api/resource/Sales%20Invoice?filters=[[\"outstanding_amount\",\">\",0],[\"docstatus\",\"=\",1]]&fields=[\"name\",\"customer\",\"grand_total\",\"outstanding_amount\",\"due_date\"]" \
  -H "$AUTH"

# Overdue invoices
curl -s "$BASE/api/resource/Sales%20Invoice?filters=[[\"outstanding_amount\",\">\",0],[\"due_date\",\"<\",\"2026-04-05\"],[\"docstatus\",\"=\",1]]&fields=[\"name\",\"customer\",\"outstanding_amount\",\"due_date\"]" \
  -H "$AUTH"

# Create sales invoice
curl -X POST "$BASE/api/resource/Sales%20Invoice" \
  -H "$AUTH" -H "Content-Type: application/json" \
  -d '{
    "customer": "Grant Plastics Ltd.",
    "company": "Hoyack (Demo)",
    "items": [
      {"item_code": "SKU001", "qty": 10, "rate": 400}
    ]
  }'
```

---

## Purchase Invoice

Invoice received from a supplier for goods/services.

### Key Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | Data | Auto-ID (e.g., `ACC-PINV-2026-00001`) |
| `supplier` | Link | Supplier reference |
| `posting_date` | Date | Invoice date |
| `due_date` | Date | Payment due date |
| `items` | Table (Purchase Invoice Item) | Line items |
| `grand_total` | Currency | Total amount |
| `outstanding_amount` | Currency | Unpaid balance |
| `status` | Select | Draft, Unpaid, Overdue, Paid, Return, Debit Note Issued, Cancelled |
| `docstatus` | Int | Workflow state |

### Examples

```bash
# List purchase invoices
curl -s "$BASE/api/resource/Purchase%20Invoice?fields=[\"name\",\"supplier\",\"posting_date\",\"grand_total\",\"outstanding_amount\",\"status\"]" \
  -H "$AUTH"

# Payables summary
curl -s "$BASE/api/resource/Purchase%20Invoice?filters=[[\"outstanding_amount\",\">\",0],[\"docstatus\",\"=\",1]]&fields=[\"name\",\"supplier\",\"outstanding_amount\",\"due_date\"]" \
  -H "$AUTH"
```

---

## Payment Entry

Record of a payment made or received.

### Key Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | Data | Auto-ID |
| `payment_type` | Select | `Receive`, `Pay`, `Internal Transfer` |
| `party_type` | Select | `Customer`, `Supplier`, `Employee`, `Shareholder` |
| `party` | Dynamic Link | Party reference |
| `paid_amount` | Currency | Amount paid |
| `paid_from` | Link (Account) | Source account |
| `paid_to` | Link (Account) | Target account |
| `reference_no` | Data | Check/transfer reference |
| `reference_date` | Date | Reference date |
| `references` | Table | Linked invoices |

### Examples

```bash
# List payments
curl -s "$BASE/api/resource/Payment%20Entry?fields=[\"name\",\"payment_type\",\"party\",\"paid_amount\",\"posting_date\"]" \
  -H "$AUTH"

# Create payment
curl -X POST "$BASE/api/resource/Payment%20Entry" \
  -H "$AUTH" -H "Content-Type: application/json" \
  -d '{
    "payment_type": "Receive",
    "party_type": "Customer",
    "party": "Grant Plastics Ltd.",
    "company": "Hoyack (Demo)",
    "paid_amount": 10000,
    "paid_from": "Debtors - HOKD",
    "paid_to": "Cash - HOKD",
    "reference_no": "CHK-001",
    "reference_date": "2026-04-05"
  }'
```

---

## Journal Entry

General accounting journal entries for adjustments, write-offs, etc.

### Key Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | Data | Auto-ID |
| `voucher_type` | Select | `Journal Entry`, `Inter Company Journal Entry`, `Bank Entry`, `Cash Entry`, `Credit Card Entry`, `Debit Note`, `Credit Note`, `Contra Entry`, `Excise Entry`, `Write Off Entry`, `Opening Entry`, `Depreciation Entry`, `Exchange Rate Revaluation`, `Exchange Gain Or Loss`, `Deferred Revenue`, `Deferred Expense` |
| `posting_date` | Date | Entry date |
| `accounts` | Table (Journal Entry Account) | Debit/credit lines |
| `total_debit` | Currency | Total debit |
| `total_credit` | Currency | Total credit |

### Examples

```bash
# List journal entries
curl -s "$BASE/api/resource/Journal%20Entry?fields=[\"name\",\"voucher_type\",\"posting_date\",\"total_debit\"]" \
  -H "$AUTH"
```

---

## Reports via API

```bash
# General Ledger
curl -s "$BASE/api/method/frappe.desk.query_report.run" \
  -H "$AUTH" -H "Content-Type: application/json" \
  -d '{"report_name":"General Ledger","filters":{"company":"Hoyack (Demo)","from_date":"2026-01-01","to_date":"2026-12-31"}}'

# Accounts Receivable
curl -s "$BASE/api/method/frappe.desk.query_report.run" \
  -H "$AUTH" -H "Content-Type: application/json" \
  -d '{"report_name":"Accounts Receivable","filters":{"company":"Hoyack (Demo)"}}'

# Accounts Payable
curl -s "$BASE/api/method/frappe.desk.query_report.run" \
  -H "$AUTH" -H "Content-Type: application/json" \
  -d '{"report_name":"Accounts Payable","filters":{"company":"Hoyack (Demo)"}}'

# Profit and Loss Statement
curl -s "$BASE/api/method/frappe.desk.query_report.run" \
  -H "$AUTH" -H "Content-Type: application/json" \
  -d '{"report_name":"Profit and Loss Statement","filters":{"company":"Hoyack (Demo)","fiscal_year":"2026","periodicity":"Monthly"}}'

# Balance Sheet
curl -s "$BASE/api/method/frappe.desk.query_report.run" \
  -H "$AUTH" -H "Content-Type: application/json" \
  -d '{"report_name":"Balance Sheet","filters":{"company":"Hoyack (Demo)","fiscal_year":"2026","periodicity":"Yearly"}}'
```
