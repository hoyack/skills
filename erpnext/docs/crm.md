# CRM Module

## Lead

A potential customer or prospect.

### Key Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | Data | Auto-ID (e.g., `CRM-LEAD-2026-00001`) |
| `lead_name` | Data | Person or company name |
| `company_name` | Data | Company name |
| `email_id` | Data | Primary email |
| `phone` | Data | Phone number |
| `mobile_no` | Data | Mobile number |
| `source` | Link | Lead source (Website, Referral, etc.) |
| `status` | Select | `Lead`, `Open`, `Replied`, `Opportunity`, `Quotation`, `Lost Quotation`, `Interested`, `Converted`, `Do Not Contact` |
| `lead_owner` | Link (User) | Assigned owner |
| `territory` | Link | Territory |
| `industry` | Link | Industry |
| `notes` | Text | Additional notes |

### Examples

```bash
# List leads
curl -s "$BASE/api/resource/Lead?fields=[\"name\",\"lead_name\",\"company_name\",\"email_id\",\"status\",\"source\"]&limit_page_length=20" \
  -H "$AUTH"

# Create lead
curl -X POST "$BASE/api/resource/Lead" \
  -H "$AUTH" -H "Content-Type: application/json" \
  -d '{
    "lead_name": "Jane Smith",
    "company_name": "Acme Corp",
    "email_id": "jane@acme.com",
    "phone": "+1-555-0123",
    "source": "Website",
    "status": "Open"
  }'

# Update lead status
curl -X PUT "$BASE/api/resource/Lead/CRM-LEAD-2026-00001" \
  -H "$AUTH" -H "Content-Type: application/json" \
  -d '{"status":"Interested"}'

# Filter: open leads
curl -s "$BASE/api/resource/Lead?filters=[[\"status\",\"in\",[\"Open\",\"Replied\"]]]&fields=[\"name\",\"lead_name\",\"email_id\",\"status\"]" \
  -H "$AUTH"
```

---

## Opportunity

A qualified sales opportunity linked to a lead or customer.

### Key Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | Data | Auto-ID |
| `opportunity_from` | Select | `Lead`, `Customer` |
| `party_name` | Dynamic Link | Lead or Customer reference |
| `opportunity_type` | Select | `Sales`, `Support`, `Maintenance` |
| `status` | Select | `Open`, `Quotation`, `Converted`, `Lost`, `Replied`, `Closed` |
| `expected_closing` | Date | Expected close date |
| `probability` | Percent | Win probability |
| `opportunity_amount` | Currency | Estimated value |
| `currency` | Link | Currency |
| `items` | Table (Opportunity Item) | Products/services of interest |
| `lost_reasons` | Table | Reasons if lost |
| `contact_person` | Link | Contact reference |

### Examples

```bash
# List opportunities
curl -s "$BASE/api/resource/Opportunity?fields=[\"name\",\"party_name\",\"opportunity_type\",\"status\",\"opportunity_amount\",\"expected_closing\"]" \
  -H "$AUTH"

# Create opportunity from lead
curl -X POST "$BASE/api/resource/Opportunity" \
  -H "$AUTH" -H "Content-Type: application/json" \
  -d '{
    "opportunity_from": "Lead",
    "party_name": "CRM-LEAD-2026-00001",
    "opportunity_type": "Sales",
    "expected_closing": "2026-06-30",
    "probability": 60,
    "opportunity_amount": 50000,
    "currency": "USD"
  }'

# Open opportunities pipeline
curl -s "$BASE/api/resource/Opportunity?filters=[[\"status\",\"=\",\"Open\"]]&fields=[\"name\",\"party_name\",\"opportunity_amount\",\"expected_closing\",\"probability\"]&order_by=expected_closing asc" \
  -H "$AUTH"
```

---

## Campaign

Marketing campaigns for lead generation and tracking.

### Key Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | Data | Campaign name |
| `campaign_type` | Link | Type (Email, Social Media, etc.) |
| `description` | Text | Campaign description |

### Examples

```bash
# List campaigns
curl -s "$BASE/api/resource/Campaign?fields=[\"name\",\"campaign_type\"]" -H "$AUTH"

# Create campaign
curl -X POST "$BASE/api/resource/Campaign" \
  -H "$AUTH" -H "Content-Type: application/json" \
  -d '{"name":"Q2 Product Launch","campaign_type":"Email"}'
```

---

## Contact

Contact person linked to customers, suppliers, or leads.

### Key Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | Data | Auto-ID |
| `first_name` | Data | First name |
| `last_name` | Data | Last name |
| `email_id` | Data | Primary email |
| `phone` | Data | Phone number |
| `mobile_no` | Data | Mobile number |
| `company_name` | Data | Associated company |
| `designation` | Data | Job title |
| `links` | Table (Dynamic Link) | Links to Customer/Supplier/Lead |

### Examples

```bash
# List contacts
curl -s "$BASE/api/resource/Contact?fields=[\"name\",\"first_name\",\"last_name\",\"email_id\",\"company_name\"]&limit_page_length=20" \
  -H "$AUTH"

# Create contact linked to customer
curl -X POST "$BASE/api/resource/Contact" \
  -H "$AUTH" -H "Content-Type: application/json" \
  -d '{
    "first_name": "John",
    "last_name": "Doe",
    "email_id": "john@acme.com",
    "phone": "+1-555-0456",
    "designation": "CTO",
    "links": [{"link_doctype": "Customer", "link_name": "Grant Plastics Ltd."}]
  }'
```
