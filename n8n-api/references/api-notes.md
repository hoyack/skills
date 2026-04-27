# n8n Public API Notes

Base URL for Shrubnet: `https://n8n.cluster.shrubnet.com`.

Authentication: pass the API key as `X-N8N-API-KEY`. Do not print the token. Load it from `.env`.

Common endpoints:

- `GET /api/v1/workflows?limit=20&cursor=...` — list workflows.
- `GET /api/v1/workflows/{id}` — retrieve one workflow definition.
- `POST /api/v1/workflows` — create a workflow.
- `PUT /api/v1/workflows/{id}` — replace/update a workflow.
- `DELETE /api/v1/workflows/{id}` — delete a workflow. Confirm first.
- `POST /api/v1/workflows/{id}/activate` — activate a workflow. Confirm first unless explicitly requested.
- `POST /api/v1/workflows/{id}/deactivate` — deactivate a workflow. Confirm first unless explicitly requested.
- `GET /api/v1/executions?limit=20&workflowId=...&status=...` — list executions.
- `GET /api/v1/executions/{id}?includeData=true` — inspect execution detail; may include sensitive data.
- `DELETE /api/v1/executions/{id}` — delete execution data. Confirm first.
- `GET /api/v1/credentials` — list credential metadata only; secret values are not returned.
- `POST /api/v1/credentials` / `DELETE /api/v1/credentials/{id}` — credential writes. Confirm and avoid exposing secrets.
- `GET /api/v1/tags` / `POST /api/v1/tags` / `DELETE /api/v1/tags/{id}` — manage workflow tags.
- `GET /api/v1/users` — list users if available in this n8n edition/config.

Response shape is usually `{ "data": [...], "nextCursor": "..." }` for list endpoints.

Safety:

- Treat workflow definitions, execution data, and credentials as sensitive.
- Do not send credentials, execution payloads, or private workflow details to external services without explicit user approval.
- Prefer read-only endpoints when investigating.
- Confirm before activating/deactivating workflows, deleting workflows/executions/credentials, or changing production automation.
