#!/usr/bin/env python3
"""Small n8n Public API helper for OpenClaw skills.

Loads N8N_BASE_URL and N8N_API_KEY from ../.env by default. Prints redacted,
human-readable summaries for common read operations; can also issue arbitrary
public API requests when needed.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

SKILL_DIR = Path(__file__).resolve().parents[1]
DEFAULT_ENV = SKILL_DIR / ".env"


def load_env(path: Path = DEFAULT_ENV) -> None:
    if not path.exists():
        return
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def config() -> tuple[str, str]:
    load_env()
    base = os.environ.get("N8N_BASE_URL", "").rstrip("/")
    key = os.environ.get("N8N_API_KEY", "")
    if not base or not key:
        raise SystemExit("Missing N8N_BASE_URL or N8N_API_KEY. Configure skills/n8n-api/.env")
    return base, key


def request(method: str, path: str, body: Optional[Dict[str, Any]] = None, params: Optional[Dict[str, Any]] = None) -> Any:
    base, key = config()
    if not path.startswith("/"):
        path = "/" + path
    url = base + path
    if params:
        clean = {k: v for k, v in params.items() if v is not None}
        if clean:
            url += "?" + urlencode(clean)
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = Request(url, data=data, method=method.upper())
    req.add_header("X-N8N-API-KEY", key)
    req.add_header("Accept", "application/json")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            if not raw:
                return None
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                return raw
    except HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        raise SystemExit(f"HTTP {e.code} {e.reason}: {raw[:1000]}")
    except URLError as e:
        raise SystemExit(f"Request failed: {e}")


def print_json(data: Any) -> None:
    print(json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False))


def list_workflows(args: argparse.Namespace) -> None:
    data = request("GET", "/api/v1/workflows", params={"limit": args.limit, "cursor": args.cursor, "active": args.active})
    if args.json:
        print_json(data)
        return
    items = data.get("data", []) if isinstance(data, dict) else []
    print(f"workflows: {len(items)}")
    for w in items:
        print(f"- {w.get('id')} | active={w.get('active')} | {w.get('name')}")
    if isinstance(data, dict) and data.get("nextCursor"):
        print(f"nextCursor: {data['nextCursor']}")


def get_workflow(args: argparse.Namespace) -> None:
    print_json(request("GET", f"/api/v1/workflows/{args.id}"))


def list_executions(args: argparse.Namespace) -> None:
    data = request("GET", "/api/v1/executions", params={"limit": args.limit, "cursor": args.cursor, "workflowId": args.workflow_id, "status": args.status})
    if args.json:
        print_json(data)
        return
    items = data.get("data", []) if isinstance(data, dict) else []
    print(f"executions: {len(items)}")
    for e in items:
        print(f"- {e.get('id')} | {e.get('status')} | workflow={e.get('workflowId')} | started={e.get('startedAt')} stopped={e.get('stoppedAt')}")
    if isinstance(data, dict) and data.get("nextCursor"):
        print(f"nextCursor: {data['nextCursor']}")


def get_execution(args: argparse.Namespace) -> None:
    print_json(request("GET", f"/api/v1/executions/{args.id}", params={"includeData": str(args.include_data).lower()}))


def raw(args: argparse.Namespace) -> None:
    body = json.loads(args.body) if args.body else None
    params = dict(pair.split("=", 1) for pair in args.query) if args.query else None
    print_json(request(args.method, args.path, body=body, params=params))


def main() -> None:
    p = argparse.ArgumentParser(description="n8n Public API helper")
    sub = p.add_subparsers(dest="cmd", required=True)

    w = sub.add_parser("workflows", help="List workflows")
    w.add_argument("--limit", type=int, default=20)
    w.add_argument("--cursor")
    w.add_argument("--active", choices=["true", "false"])
    w.add_argument("--json", action="store_true")
    w.set_defaults(func=list_workflows)

    gw = sub.add_parser("workflow", help="Get one workflow")
    gw.add_argument("id")
    gw.set_defaults(func=get_workflow)

    e = sub.add_parser("executions", help="List executions")
    e.add_argument("--limit", type=int, default=20)
    e.add_argument("--cursor")
    e.add_argument("--workflow-id")
    e.add_argument("--status")
    e.add_argument("--json", action="store_true")
    e.set_defaults(func=list_executions)

    ge = sub.add_parser("execution", help="Get one execution")
    ge.add_argument("id")
    ge.add_argument("--include-data", action="store_true")
    ge.set_defaults(func=get_execution)

    r = sub.add_parser("raw", help="Arbitrary /api/v1 request")
    r.add_argument("method")
    r.add_argument("path")
    r.add_argument("--query", action="append", default=[], help="key=value query param; may repeat")
    r.add_argument("--body", help="JSON request body")
    r.set_defaults(func=raw)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
