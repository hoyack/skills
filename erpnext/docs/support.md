# Support Module

## Issue

Customer support tickets / helpdesk issues.

### Key Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | Data | Auto-ID (e.g., `ISS-2026-00001`) |
| `subject` | Data | Issue title |
| `raised_by` | Data | Email of reporter |
| `customer` | Link | Customer reference |
| `status` | Select | `Open`, `Replied`, `On Hold`, `Resolved`, `Closed` |
| `priority` | Select | `Low`, `Medium`, `High`, `Urgent` |
| `issue_type` | Link | Issue classification |
| `description` | Text Editor | Issue details |
| `resolution_details` | Text Editor | How it was resolved |
| `opening_date` | Date | When opened |
| `resolution_date` | Datetime | When resolved |
| `first_responded_on` | Datetime | First response time |
| `avg_response_time` | Duration | Average response time |
| `resolution_time` | Duration | Time to resolution |

### Examples

```bash
# List open issues
curl -s "$BASE/api/resource/Issue?filters=[[\"status\",\"in\",[\"Open\",\"Replied\"]]]&fields=[\"name\",\"subject\",\"customer\",\"priority\",\"status\",\"opening_date\"]&order_by=priority desc" \
  -H "$AUTH"

# Create issue
curl -X POST "$BASE/api/resource/Issue" \
  -H "$AUTH" -H "Content-Type: application/json" \
  -d '{
    "subject": "Unable to process payment",
    "raised_by": "john@acme.com",
    "customer": "Grant Plastics Ltd.",
    "priority": "High",
    "description": "Customer reports payment gateway timeout on checkout."
  }'

# Resolve issue
curl -X PUT "$BASE/api/resource/Issue/ISS-2026-00001" \
  -H "$AUTH" -H "Content-Type: application/json" \
  -d '{"status":"Resolved","resolution_details":"Gateway config updated. Payment processing confirmed working."}'

# Issue metrics
curl -s "$BASE/api/method/frappe.client.get_count" \
  -H "$AUTH" -H "Content-Type: application/json" \
  -d '{"doctype":"Issue","filters":[["status","=","Open"]]}'
```

---

## Warranty Claim

Track warranty claims on sold products.

### Key Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | Data | Auto-ID |
| `customer` | Link | Customer reference |
| `serial_no` | Link | Serial number of item |
| `item_code` | Link | Item reference |
| `complaint` | Text | Customer complaint |
| `status` | Select | `Open`, `Closed`, `Work In Progress`, `Cancelled` |
| `warranty_amc_status` | Select | `Under Warranty`, `Out of Warranty`, `Under AMC` |
| `complaint_date` | Date | Date of complaint |
| `resolution_date` | Date | Resolution date |

### Examples

```bash
# List warranty claims
curl -s "$BASE/api/resource/Warranty%20Claim?fields=[\"name\",\"customer\",\"item_code\",\"status\",\"complaint_date\"]" \
  -H "$AUTH"

# Create warranty claim
curl -X POST "$BASE/api/resource/Warranty%20Claim" \
  -H "$AUTH" -H "Content-Type: application/json" \
  -d '{
    "customer": "Grant Plastics Ltd.",
    "item_code": "SKU004",
    "complaint": "Screen flickering after 2 months of use",
    "complaint_date": "2026-04-05"
  }'
```
