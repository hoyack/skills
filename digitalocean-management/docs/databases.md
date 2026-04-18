# Managed Databases Reference

Fully-managed database clusters with automated backups, failover, and patching. Use these instead of self-hosting on a Droplet for any production workload with state.

## Supported Engines

| Engine | API slug | Versions | Best For |
|---|---|---|---|
| PostgreSQL | `pg` | 14, 15, 16 | General relational workloads; default choice |
| MySQL | `mysql` | 8 | Legacy apps, MySQL-specific features |
| Redis | `redis` | 7 | Cache, rate limits, queues, session store |
| MongoDB | `mongodb` | 6, 7 | Document-heavy workloads |
| Kafka | `kafka` | 3.5, 3.6, 3.7 | Event streaming |

## Cluster Object

Key fields from `GET /v2/databases/{cluster_uuid}`:

| Field | Description |
|---|---|
| `id` | Cluster UUID |
| `name` | |
| `engine` | `pg`, `mysql`, `redis`, `mongodb`, `kafka` |
| `version` | `"16"`, `"8"`, etc. |
| `region` | Slug |
| `size` | `db-s-1vcpu-1gb` etc. |
| `status` | `creating`, `online`, `resizing`, `forking`, `migrating`, `offline` |
| `num_nodes` | 1 for single, 2+ for HA with standby |
| `connection` | `{ host, port, user, password, database, uri, ssl }` — primary |
| `private_connection` | Same shape, VPC-internal hostnames |
| `standby_connection` | If HA; read-replica endpoint |
| `maintenance_window` | `{ day, hour, pending, description }` |
| `backup_restore` | Present if forked from a backup |
| `vpc_uuid` | |

## Sizes

Start small, scale up. Resizing is online (few-second blip during failover) on HA clusters.

### Development / light production
| Slug | vCPU | RAM | ~$/mo |
|---|---|---|---|
| `db-s-1vcpu-1gb` | 1 | 1 GB | $15 |
| `db-s-1vcpu-2gb` | 1 | 2 GB | $30 |
| `db-s-2vcpu-4gb` | 2 | 4 GB | $60 |

### General / memory-heavy
| Slug | vCPU | RAM |
|---|---|---|
| `db-s-4vcpu-8gb` | 4 | 8 GB |
| `db-s-6vcpu-16gb` | 6 | 16 GB |

Add standby nodes for HA: `num_nodes: 2` roughly doubles the price; enables automatic failover.

## Creating a Cluster

Minimal Postgres create:

```bash
curl -X POST -H "Authorization: Bearer $DIGITALOCEAN_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "thunderstaff-pg",
    "engine": "pg",
    "version": "16",
    "region": "nyc3",
    "size": "db-s-1vcpu-1gb",
    "num_nodes": 1,
    "tags": ["thunderstaff", "prod"]
  }' \
  https://api.digitalocean.com/v2/databases
```

Provisioning takes 3-7 minutes. Poll until `status == "online"`.

## Connecting

Two connection URIs are returned:

- **`connection.uri`** — public hostname, TLS required. Use from outside DO or during dev.
- **`private_connection.uri`** — VPC-internal hostname. Use from App Platform apps / Droplets in the same region/VPC. No bandwidth charges; faster; not exposed to the internet.

Example Postgres URI:
```
postgresql://doadmin:<password>@thunderstaff-pg-do-user-12345.c.db.ondigitalocean.com:25060/defaultdb?sslmode=require
```

Standard connection requirements:
- **TLS** — mandatory; `sslmode=require` or verify-full
- **CA cert** — DO provides a cluster-specific CA cert; for verify-full, download and supply via `sslrootcert=`
- **Port** — `25060` for Postgres, `25061` for connection pool

## Trusted Sources (firewall)

Managed databases ship with no inbound allow — you must add sources:

```bash
curl -X PUT -H "Authorization: Bearer $DIGITALOCEAN_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "rules": [
      {"type": "droplet", "value": "<droplet-id>"},
      {"type": "app", "value": "<app-uuid>"},
      {"type": "k8s", "value": "<cluster-uuid>"},
      {"type": "tag", "value": "<tag-name>"},
      {"type": "ip_addr", "value": "<ip/cidr>"}
    ]
  }' \
  https://api.digitalocean.com/v2/databases/<cluster-uuid>/firewall
```

Preferred: `type: "app"` (binds to an App Platform app) or `type: "droplet"` (binds to a specific VM). IP ranges work but create drift if your office/home IP changes.

## Connection Pools (Postgres)

Postgres connections are expensive. For apps that open lots of them (like serverless / many instances), create a PgBouncer pool:

```bash
curl -X POST -H "Authorization: Bearer $DIGITALOCEAN_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "app-pool",
    "mode": "transaction",
    "size": 20,
    "db": "defaultdb",
    "user": "doadmin"
  }' \
  https://api.digitalocean.com/v2/databases/<cluster-uuid>/pools
```

The pool has its own host/port (on `25061`) — app connects to the pool URI, pool talks to the real Postgres on the back. Use `transaction` mode for most web apps.

## Databases and Users

### Create a new database inside a cluster
```bash
curl -X POST -H "Authorization: Bearer $DIGITALOCEAN_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "thunderstaff"}' \
  https://api.digitalocean.com/v2/databases/<cluster-uuid>/dbs
```

### Create a new user
```bash
curl -X POST -H "Authorization: Bearer $DIGITALOCEAN_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "app"}' \
  https://api.digitalocean.com/v2/databases/<cluster-uuid>/users
```

Response includes a generated password. Best practice: create a dedicated user per app, grant only the needed databases, and bind that user's credentials to the app's env vars.

## Backups

- Automatic daily, up to 7 days retained
- Point-in-time restore available within the retention window
- Manual forks — create a new cluster from any point-in-time snapshot of an existing cluster (useful for staging, accidental-delete recovery)

Fork:
```bash
curl -X POST -H "Authorization: Bearer $DIGITALOCEAN_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "thunderstaff-pg-fork",
    "engine": "pg",
    "version": "16",
    "region": "nyc3",
    "size": "db-s-1vcpu-1gb",
    "num_nodes": 1,
    "backup_restore": {
      "database_name": "thunderstaff-pg",
      "backup_created_at": "2026-04-14T03:00:00Z"
    }
  }' \
  https://api.digitalocean.com/v2/databases
```

## Integration with App Platform

The cleanest pattern:

1. Create the App Platform app spec with an inline `databases` component, e.g.:
   ```yaml
   databases:
     - name: db
       engine: PG
       version: "16"
       production: true
       cluster_name: thunderstaff-pg
   ```
2. Reference in service envs: `value: ${db.DATABASE_URL}`
3. DO manages the attachment — the app's private IP is automatically added to trusted sources

If the database already exists (created out-of-band), reference it by `cluster_name` in the spec instead of letting the spec create it.

## Engine-Specific Notes

### Postgres

- `sslmode=require` is the safe minimum
- For long-running connections, consider a connection pool (see above)
- Default user `doadmin` has superuser — create a least-privilege user for the app
- `ALTER SYSTEM` is restricted; GUC changes via cluster config endpoint

### Redis

- Persistence defaults: RDB snapshots; AOF available
- Redis 7+: streams, functions, ACLs
- Not a durable store — treat as cache + ephemeral queue

### MongoDB

- TLS mandatory
- Replica set mode even on 1-node clusters (connection string uses `mongodb+srv://`)
- Atlas SDKs and drivers work identically

### MySQL

- Default auth plugin is `mysql_native_password` — some modern drivers want `caching_sha2_password`; configurable
- InnoDB only; no MyISAM

### Kafka

- 3-node minimum (so pricier floor)
- Brokers, ZooKeeper, schema registry are all managed
- SASL/SSL for auth

## Common Pitfalls

| Symptom | Likely Cause |
|---|---|
| App can't connect — timeout | Trusted sources doesn't include the app/Droplet |
| `SSL connection required` error | Client not using TLS; add `sslmode=require` |
| Connection limit hit | No pool; add PgBouncer pool and point app at pool URI |
| Slow queries after resize | Postgres stats need reanalyze; `ANALYZE;` after big resize |
| Fork/restore stuck | Backup timestamp before retention window; pick newer point |
| `password authentication failed` | Used wrong user, or credentials rotated; fetch fresh from API |
