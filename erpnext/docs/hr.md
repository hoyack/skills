# HR Module

## Employee

Core employee record with personal and employment details.

### Key Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | Data | Employee ID (e.g., `HR-EMP-00001`) |
| `employee_name` | Data | Full name |
| `first_name` | Data | First name |
| `last_name` | Data | Last name |
| `company` | Link | Employing company |
| `status` | Select | `Active`, `Inactive`, `Suspended`, `Left` |
| `gender` | Select | Gender |
| `date_of_birth` | Date | DOB |
| `date_of_joining` | Date | Join date |
| `relieving_date` | Date | Termination date |
| `department` | Link | Department |
| `designation` | Link | Job title/designation |
| `reports_to` | Link (Employee) | Manager |
| `company_email` | Data | Work email |
| `personal_email` | Data | Personal email |
| `cell_phone` | Data | Mobile phone |
| `current_address` | Text | Address |
| `attendance_device_id` | Data | Biometric ID |
| `holiday_list` | Link | Holiday calendar |
| `leave_policy` | Link | Leave allocation policy |

### Examples

```bash
# List employees
curl -s "$BASE/api/resource/Employee?fields=[\"name\",\"employee_name\",\"department\",\"designation\",\"status\",\"date_of_joining\"]&limit_page_length=50" \
  -H "$AUTH"

# Create employee
curl -X POST "$BASE/api/resource/Employee" \
  -H "$AUTH" -H "Content-Type: application/json" \
  -d '{
    "first_name": "Jane",
    "last_name": "Smith",
    "company": "Hoyack",
    "date_of_joining": "2026-04-01",
    "date_of_birth": "1990-05-15",
    "gender": "Female",
    "department": "Engineering",
    "designation": "Software Engineer"
  }'

# Active employees by department
curl -s "$BASE/api/resource/Employee?filters=[[\"status\",\"=\",\"Active\"]]&fields=[\"name\",\"employee_name\",\"department\",\"designation\"]&group_by=department" \
  -H "$AUTH"

# Employee count
curl -s "$BASE/api/method/frappe.client.get_count" \
  -H "$AUTH" -H "Content-Type: application/json" \
  -d '{"doctype":"Employee","filters":[["status","=","Active"]]}'
```

---

## Leave Application

Employee leave/time-off requests.

### Key Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | Data | Auto-ID |
| `employee` | Link | Employee reference |
| `leave_type` | Link | Leave type (Casual, Sick, etc.) |
| `from_date` | Date | Start date |
| `to_date` | Date | End date |
| `total_leave_days` | Float | Number of days |
| `status` | Select | `Open`, `Approved`, `Rejected`, `Cancelled` |
| `leave_approver` | Link (User) | Approver |
| `description` | Text | Reason |

### Examples

```bash
# List leave applications
curl -s "$BASE/api/resource/Leave%20Application?fields=[\"name\",\"employee\",\"leave_type\",\"from_date\",\"to_date\",\"status\"]" \
  -H "$AUTH"

# Create leave application
curl -X POST "$BASE/api/resource/Leave%20Application" \
  -H "$AUTH" -H "Content-Type: application/json" \
  -d '{
    "employee": "HR-EMP-00001",
    "leave_type": "Casual Leave",
    "from_date": "2026-05-01",
    "to_date": "2026-05-02",
    "description": "Personal errands"
  }'

# Pending approvals
curl -s "$BASE/api/resource/Leave%20Application?filters=[[\"status\",\"=\",\"Open\"]]&fields=[\"name\",\"employee\",\"leave_type\",\"from_date\",\"to_date\"]" \
  -H "$AUTH"
```

---

## Attendance

Daily employee attendance records.

### Key Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | Data | Auto-ID |
| `employee` | Link | Employee reference |
| `attendance_date` | Date | Date |
| `status` | Select | `Present`, `Absent`, `Half Day`, `Work From Home`, `On Leave` |
| `late_entry` | Check | Late arrival flag |
| `early_exit` | Check | Early departure flag |

### Examples

```bash
# Today's attendance
curl -s "$BASE/api/resource/Attendance?filters=[[\"attendance_date\",\"=\",\"2026-04-05\"]]&fields=[\"name\",\"employee\",\"status\"]" \
  -H "$AUTH"

# Mark attendance
curl -X POST "$BASE/api/resource/Attendance" \
  -H "$AUTH" -H "Content-Type: application/json" \
  -d '{"employee":"HR-EMP-00001","attendance_date":"2026-04-05","status":"Present"}'
```

---

## Salary Slip / Payroll Entry

Payroll processing is done via **Payroll Entry** which generates **Salary Slips** for each employee.

### Key Salary Slip Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | Data | Auto-ID |
| `employee` | Link | Employee reference |
| `posting_date` | Date | Pay date |
| `start_date` | Date | Period start |
| `end_date` | Date | Period end |
| `gross_pay` | Currency | Gross salary |
| `total_deduction` | Currency | Total deductions |
| `net_pay` | Currency | Net pay |
| `earnings` | Table | Earning components |
| `deductions` | Table | Deduction components |

### Examples

```bash
# List salary slips
curl -s "$BASE/api/resource/Salary%20Slip?fields=[\"name\",\"employee\",\"posting_date\",\"gross_pay\",\"net_pay\"]" \
  -H "$AUTH"
```
