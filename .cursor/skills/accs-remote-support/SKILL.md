---
name: accs-remote-support
description: Use Adobe Commerce as a Cloud Service (ACCS) from a Cursor Cloud Agent on iPhone or web, without the user's Mac. Apply when the user asks about ACCS, catalog, orders, customers, store config, or remote Commerce support.
---

# ACCS remote support

This Cloud Agent can call **Adobe Commerce as a Cloud Service** without Cursor Desktop or My Machines.

## Connect

1. Non-secret config is in `accs/config.json` (client ID, tenant IDs, REST host).
2. The IMS client secret is the environment runtime secret `ADOBE_COMMERCE_CLIENT_SECRET`.
3. Run `python3 accs/client.py ping` to verify. Then use `python3 accs/client.py get /V1/...` or import `rest()` from `accs/client.py`.
4. Default environment is PRODUCTION. Pass `--env STAGE` or `--env DEV` when asked.

Never print the client secret, access token, or full customer PII unless the user asked for that record.

## If ping fails

- Secret missing: tell the user to add `ADOBE_COMMERCE_CLIENT_SECRET` on the Cloud Agent environment, then start a **new** agent (secrets inject at boot).
- HTTP 403 without store data: include `User-Agent` and `x-gw-ims-org-id` from the IMS JWT `org` claim (the client already does this).
- Do not use Desktop `~/.cursor/mcp.json`. That does not follow iPhone/cloud runs.

## Out of scope unless asked

Jazz OMS, QuickBooks, and Azure SQL are separate. Azure SQL is blocked from Cloud Agent IPs unless a firewall rule matches the current VM.
