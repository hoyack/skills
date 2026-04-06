# Projects Module

## Project

Top-level project tracking with tasks, timesheets, and costing.

### Key Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | Data | Project ID/name |
| `project_name` | Data | Display name |
| `company` | Link | Associated company |
| `status` | Select | `Open`, `Completed`, `Cancelled` |
| `priority` | Select | `Medium`, `Low`, `High` |
| `expected_start_date` | Date | Planned start |
| `expected_end_date` | Date | Planned end |
| `actual_start_date` | Date | Actual start |
| `actual_end_date` | Date | Actual completion |
| `percent_complete` | Percent | Progress percentage |
| `estimated_costing` | Currency | Budget |
| `total_costing_amount` | Currency | Actual cost |
| `is_active` | Select | `Yes`, `No` |
| `customer` | Link | Customer (if client project) |
| `department` | Link | Department |

### Examples

```bash
# List projects
curl -s "$BASE/api/resource/Project?fields=[\"name\",\"project_name\",\"status\",\"percent_complete\",\"expected_end_date\"]" \
  -H "$AUTH"

# Create project
curl -X POST "$BASE/api/resource/Project" \
  -H "$AUTH" -H "Content-Type: application/json" \
  -d '{
    "project_name": "Website Redesign",
    "company": "Hoyack",
    "status": "Open",
    "priority": "High",
    "expected_start_date": "2026-04-15",
    "expected_end_date": "2026-06-30",
    "estimated_costing": 25000
  }'

# Active projects with progress
curl -s "$BASE/api/resource/Project?filters=[[\"status\",\"=\",\"Open\"]]&fields=[\"name\",\"project_name\",\"percent_complete\",\"expected_end_date\",\"estimated_costing\"]" \
  -H "$AUTH"
```

---

## Task (Project Task)

Individual tasks within a project.

### Key Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | Data | Auto-ID |
| `subject` | Data | Task title |
| `project` | Link | Parent project |
| `status` | Select | `Open`, `Working`, `Pending Review`, `Overdue`, `Template`, `Completed`, `Cancelled` |
| `priority` | Select | `Low`, `Medium`, `High`, `Urgent` |
| `expected_time` | Float | Estimated hours |
| `actual_time` | Float | Logged hours |
| `exp_start_date` | Date | Expected start |
| `exp_end_date` | Date | Expected end |
| `completed_on` | Date | Completion date |
| `assigned_to` | Link (User) | Assignee |
| `description` | Text Editor | Task details |

### Examples

```bash
# List tasks for a project
curl -s "$BASE/api/resource/Task?filters=[[\"project\",\"=\",\"Website Redesign\"]]&fields=[\"name\",\"subject\",\"status\",\"priority\",\"exp_end_date\"]" \
  -H "$AUTH"

# Create task
curl -X POST "$BASE/api/resource/Task" \
  -H "$AUTH" -H "Content-Type: application/json" \
  -d '{
    "subject": "Design mockups",
    "project": "Website Redesign",
    "status": "Open",
    "priority": "High",
    "exp_start_date": "2026-04-15",
    "exp_end_date": "2026-04-25",
    "expected_time": 20
  }'

# Open tasks across all projects
curl -s "$BASE/api/resource/Task?filters=[[\"status\",\"in\",[\"Open\",\"Working\"]]]&fields=[\"name\",\"subject\",\"project\",\"priority\",\"exp_end_date\"]&order_by=exp_end_date asc" \
  -H "$AUTH"
```

---

## Timesheet

Time logging for project billing and employee tracking.

### Key Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | Data | Auto-ID |
| `employee` | Link | Employee reference |
| `company` | Link | Company |
| `time_logs` | Table (Timesheet Detail) | Time entries |
| `total_hours` | Float | Total logged hours |
| `total_billable_hours` | Float | Billable hours |
| `total_billed_hours` | Float | Already billed hours |
| `total_billable_amount` | Currency | Billable value |
| `status` | Select | Draft, Submitted, Billed, Payslip, Completed, Cancelled |

### Timesheet Detail (child table)

| Field | Type | Description |
|-------|------|-------------|
| `activity_type` | Link | Type of work |
| `from_time` | Datetime | Start time |
| `to_time` | Datetime | End time |
| `hours` | Float | Duration |
| `project` | Link | Project reference |
| `task` | Link | Task reference |
| `billable` | Check | Is billable |
| `billing_rate` | Currency | Hourly rate |
| `billing_amount` | Currency | Line total |

### Examples

```bash
# List timesheets
curl -s "$BASE/api/resource/Timesheet?fields=[\"name\",\"employee\",\"total_hours\",\"total_billable_amount\",\"status\"]" \
  -H "$AUTH"
```
