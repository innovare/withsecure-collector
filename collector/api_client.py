# collector/api_client.py
# VERSION: v1.1.12
# FIX:
# - Payload EXACTLY as WithSecure example
# - Dict + list for engineGroup
# - persistenceTimestampStart from state
# - Correct Content-Type

import logging
import requests
from datetime import datetime, timezone

log = logging.getLogger(__name__)

API_URL = "https://api.connect.withsecure.com"
EVENTS_PATH = "/security-events/v1/security-events"

def fetch_events(auth, last_ts, anchor=None, org_id=None):
    token = auth.authenticate()

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-type": "application/x-www-form-urlencoded;charset=UTF-8",
        "User-Agent": "innovare-siem-collector"
    }

    # last_ts MUST come from state (RFC3339)
    if not last_ts:
        last_ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    params = {
        "limit": 200,
        "engineGroup": ["epp", "edr"],
        "persistenceTimestampStart": last_ts,
        "order": "asc",
        "exclusiveStart": "true",
    }

    if anchor:
        params["anchor"] = anchor

    if org_id:
        params["organizationId"] = org_id

    resp = requests.post(
        API_URL + EVENTS_PATH,
        headers=headers,
        data=params
    )

    if not resp.ok:
        raise RuntimeError(f"Event fetch failed: {resp.text}")

    payload = resp.json()
    return payload["items"], payload.get("nextAnchor")
