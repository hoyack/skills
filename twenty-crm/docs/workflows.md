# Workflow Objects Reference

Three related objects manage workflow automation: Workflow, WorkflowVersion, and WorkflowRun.

## Workflow

The top-level workflow definition.

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Unique identifier |
| `name` | String | Workflow name |
| `createdAt` | DateTime | Creation timestamp |
| `updatedAt` | DateTime | Last update timestamp |
| `deletedAt` | DateTime | Soft-delete timestamp |
| `position` | Float | Sort position |
| `createdBy` | Actor | Creation actor |
| `updatedBy` | Actor | Last update actor |

### Relations
- `versions` — WorkflowVersionConnection
- `runs` — WorkflowRunConnection
- `favorites` — FavoriteConnection

## WorkflowVersion

A specific version of a workflow with steps and triggers.

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Unique identifier |
| `name` | String | Version name |
| `workflowId` | UUID | FK to Workflow |
| `trigger` | RawJSON | Trigger configuration |
| `steps` | RawJSON | Step definitions |
| `status` | WorkflowVersionStatusEnum | ACTIVE, DRAFT, DEACTIVATED |
| `createdAt` | DateTime | Creation timestamp |
| `updatedAt` | DateTime | Last update timestamp |

## WorkflowRun

An execution instance of a workflow version.

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Unique identifier |
| `workflowVersionId` | UUID | FK to WorkflowVersion |
| `name` | String | Run name |
| `status` | WorkflowRunStatusEnum | Status of this run |
| `output` | RawJSON | Run output data |
| `startedAt` | DateTime | Execution start |
| `endedAt` | DateTime | Execution end |
| `createdAt` | DateTime | Creation timestamp |

## WorkflowAutomatedTrigger

Defines automated triggers for workflows.

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Unique identifier |
| `name` | String | Trigger name |
| `type` | String | Trigger type |
| `settings` | RawJSON | Trigger settings |

## Workflow Mutations

```graphql
# Activate a workflow version
mutation { activateWorkflowVersion(workflowVersionId: "uuid") { id status } }

# Deactivate
mutation { deactivateWorkflowVersion(workflowVersionId: "uuid") { id status } }

# Run a workflow version
mutation { runWorkflowVersion(input: { workflowVersionId: "uuid", payload: {} }) { workflowRun { id status } } }

# Stop a running workflow
mutation { stopWorkflowRun(workflowRunId: "uuid") { id status } }

# Create a draft from existing version
mutation { createDraftFromWorkflowVersion(input: { workflowId: "uuid", workflowVersionIdToCopy: "uuid" }) { id status } }

# Duplicate a workflow
mutation { duplicateWorkflow(input: { workflowId: "uuid" }) { workflow { id name } } }
```

## Step Management Mutations

```graphql
# Create step
mutation { createWorkflowVersionStep(input: { workflowVersionId: "uuid", stepType: "CODE", parentStepId: "uuid" }) { id } }

# Update step
mutation { updateWorkflowVersionStep(input: { step: { id: "uuid", name: "Updated", settings: {} } }) { id } }

# Delete step
mutation { deleteWorkflowVersionStep(input: { stepId: "uuid" }) { id } }

# Duplicate step
mutation { duplicateWorkflowVersionStep(input: { stepId: "uuid" }) { id } }
```

## Query Examples

```graphql
# List workflows with versions
query {
  workflows(first: 20) {
    edges {
      node {
        id name
        versions: workflowVersions(first: 5) {
          edges { node { id name status } }
        }
      }
    }
  }
}

# List recent workflow runs
query {
  workflowRuns(first: 20, orderBy: [{ createdAt: { direction: DescNullsLast } }]) {
    edges {
      node {
        id name status startedAt endedAt
        output
      }
    }
  }
}
```
