# projects

Remote-support helpers for Adobe Commerce, used by Cursor Cloud Agents (including the iPhone app).

## ACCS (Adobe Commerce as a Cloud Service)

Production ACCS works from a Cloud Agent **without a Mac**. Cursor Desktop MCP is not required.

1. Keep `ADOBE_COMMERCE_CLIENT_SECRET` as a runtime secret on this Cloud Agent environment.
2. From the Cursor iOS app, start a Cloud Agent on this repo / environment.
3. Ask for ACCS work (catalog, orders, customers, store config). The agent should run:

```bash
python3 accs/client.py ping
```

Config (client ID and tenant IDs) lives in `accs/config.json`. The secret never goes in git.
