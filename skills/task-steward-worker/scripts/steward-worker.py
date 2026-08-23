#!/usr/bin/env python3
"""Small Task Steward worker client.

Uses only Python stdlib. Credentials remain in process environment/argv and are
never persisted by this helper.
"""
from __future__ import annotations

import argparse
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

DEFAULT_URL = "http://127.0.0.1:9777"
RECEIPT_KINDS = ("heartbeat", "status", "complete", "blocked", "yield")


def request_json(
    method: str,
    path: str,
    *,
    payload: dict[str, Any] | None = None,
    base_url: str | None = None,
) -> dict[str, Any]:
    base = (base_url or os.environ.get("STEWARD_URL") or DEFAULT_URL).rstrip("/")
    token = os.environ.get("STEWARD_API_TOKEN")
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(base + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        try:
            detail = json.loads(exc.read().decode("utf-8"))
            message = detail.get("message") or detail.get("error") or f"HTTP {exc.code}"
        except Exception:
            message = f"HTTP {exc.code}"
        raise SystemExit(f"Task Steward request failed: {message}") from None
    except urllib.error.URLError:
        raise SystemExit("Task Steward request failed: connection error") from None

    try:
        result = json.loads(body)
    except json.JSONDecodeError:
        raise SystemExit("Task Steward returned invalid JSON") from None
    if not isinstance(result, dict):
        raise SystemExit("Task Steward returned a non-object JSON response")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", help="Task Steward base URL; defaults to STEWARD_URL or loopback")
    sub = parser.add_subparsers(dest="command", required=True)

    claim = sub.add_parser("claim")
    claim.add_argument("--worker", required=True)

    dispatch = sub.add_parser("dispatch")
    dispatch.add_argument("--worker", required=True)

    sub.add_parser("status")

    receipt = sub.add_parser("receipt")
    receipt.add_argument("--worker", required=True)
    receipt.add_argument("--project", required=True)
    receipt.add_argument("--task-ref", required=True)
    receipt.add_argument("--generation", type=int, required=True)
    receipt.add_argument("--lease-token", required=True)
    receipt.add_argument("--kind", choices=RECEIPT_KINDS, required=True)
    receipt.add_argument("--detail")

    args = parser.parse_args()
    if args.command == "claim":
        query = urllib.parse.urlencode({"worker": args.worker})
        result = request_json("GET", f"/v1/assignment?{query}", base_url=args.url)
    elif args.command == "dispatch":
        result = request_json(
            "POST", "/v1/dispatch", payload={"worker": args.worker}, base_url=args.url
        )
    elif args.command == "status":
        result = request_json("GET", "/v1/status", base_url=args.url)
    else:
        result = request_json(
            "POST",
            "/v1/receipt",
            payload={
                "worker": args.worker,
                "project": args.project,
                "task_ref": args.task_ref,
                "generation": args.generation,
                "lease_token": args.lease_token,
                "kind": args.kind,
                "detail": args.detail,
            },
            base_url=args.url,
        )
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
