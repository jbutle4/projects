#!/usr/bin/env python3
"""Adobe Commerce as a Cloud Service (ACCS) REST client for Cloud Agents.

Reads non-secret config from accs/config.json. The IMS client secret must be
present as ADOBE_COMMERCE_CLIENT_SECRET in the Cloud Agent environment.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

CONFIG_PATH = Path(__file__).resolve().parent / "config.json"
USER_AGENT = "Commerce-CloudAgent/1.0"


def load_config() -> dict[str, Any]:
    with CONFIG_PATH.open() as fh:
        return json.load(fh)


def _http(
    method: str,
    url: str,
    data: bytes | None = None,
    headers: dict[str, str] | None = None,
    timeout: int = 30,
) -> tuple[int, bytes]:
    req_headers = {"User-Agent": USER_AGENT}
    if headers:
        req_headers.update(headers)
    request = urllib.request.Request(url, data=data, headers=req_headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as err:
        return err.code, err.read()


def _jwt_claim(token: str, name: str) -> str | None:
    payload = token.split(".")[1]
    payload += "=" * (-len(payload) % 4)
    claims = json.loads(base64.urlsafe_b64decode(payload))
    value = claims.get(name)
    return value if isinstance(value, str) else None


def get_token(config: dict[str, Any] | None = None) -> tuple[str, str]:
    config = config or load_config()
    secret_name = str(config["secretEnvVar"])
    secret = os.environ.get(secret_name)
    if not secret:
        raise RuntimeError(
            f"Missing {secret_name}. Add it as a Cloud Agent environment "
            "runtime secret, then start a new agent so it is injected at boot."
        )

    status, body = _http(
        "POST",
        str(config["imsTokenUrl"]),
        urllib.parse.urlencode(
            {
                "client_id": config["clientId"],
                "client_secret": secret,
                "grant_type": "client_credentials",
                "scope": config["scope"],
            }
        ).encode(),
        {"Content-Type": "application/x-www-form-urlencoded"},
    )
    if status != 200:
        raise RuntimeError(f"IMS token failed: HTTP {status}")
    token = json.loads(body)["access_token"]
    org = _jwt_claim(token, "org")
    if not org:
        raise RuntimeError("IMS token did not include an org claim")
    return token, org


def rest(
    method: str,
    path: str,
    *,
    environment: str | None = None,
    payload: Any = None,
    config: dict[str, Any] | None = None,
) -> tuple[int, Any]:
    config = config or load_config()
    env_name = (environment or str(config["defaultEnvironment"])).upper()
    tenants: dict[str, str] = config["tenants"]
    if env_name not in tenants:
        raise RuntimeError(f"Unknown ACCS environment {env_name}")
    token, org = get_token(config)
    url = f"{config['restHost'].rstrip('/')}/{tenants[env_name]}{path}"
    headers = {
        "Authorization": f"Bearer {token}",
        "x-api-key": str(config["clientId"]),
        "x-gw-ims-org-id": org,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    data = None if payload is None else json.dumps(payload).encode()
    status, body = _http(method.upper(), url, data, headers)
    if not body:
        return status, None
    try:
        return status, json.loads(body)
    except json.JSONDecodeError:
        return status, body.decode("utf-8", "replace")


def ping(environment: str | None = None) -> dict[str, Any]:
    status, data = rest("GET", "/V1/store/storeConfigs", environment=environment)
    ok = status == 200 and isinstance(data, list) and bool(data)
    store = data[0] if ok else {}
    return {
        "ok": ok,
        "http": status,
        "environment": (environment or load_config()["defaultEnvironment"]).upper(),
        "store_code": store.get("code") if isinstance(store, dict) else None,
        "locale": store.get("locale") if isinstance(store, dict) else None,
        "currency": store.get("base_currency_code") if isinstance(store, dict) else None,
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="ACCS REST helper")
    parser.add_argument("--env", default=None, help="DEV, STAGE, or PRODUCTION")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("ping", help="Verify IMS + store config")
    get_cmd = sub.add_parser("get", help="GET a REST path such as /V1/products")
    get_cmd.add_argument("path")
    args = parser.parse_args(argv)

    try:
        if args.command == "ping":
            print(json.dumps(ping(args.env), indent=2))
            return 0
        if args.command == "get":
            status, data = rest("GET", args.path, environment=args.env)
            print(json.dumps({"http": status, "body": data}, indent=2, default=str)[:8000])
            return 0 if status < 400 else 1
        raise RuntimeError(f"Unhandled command {args.command}")
    except RuntimeError as err:
        print(str(err), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
