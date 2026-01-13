# collector/api_client.py
# VERSION: v1.4.0
#
# CHANGELOG:
# - Envuelve el evento original en estructura:
#   {
#       "vendor": "withsecure",
#       "withsecure": <evento_original>
#   }
# - Mantiene conversión de timestamps epoch -> ISO
# - Mantiene rename serverTimestamp -> timestamp
# - No altera paginación ni state
# - Compatible con Wazuh / OpenSearch / SIEMs

import logging
import requests
from datetime import datetime, timezone, timedelta

log = logging.getLogger(__name__)

API_URL = "https://api.connect.withsecure.com"
EVENTS_PATH = "/security-events/v1/security-events"


# ----------------------------------------------------------------------
# Helper: epoch (int | float | numeric str) -> ISO 8601 UTC
# ----------------------------------------------------------------------
def _epoch_to_iso(value):
    try:
        if isinstance(value, str):
            if not value.isdigit():
                return value
            value = int(value)

        if not isinstance(value, (int, float)):
            return value

        # Detect milliseconds
        if value > 1_000_000_000_000:
            dt = datetime.fromtimestamp(value / 1000, tz=timezone.utc)
        else:
            dt = datetime.fromtimestamp(value, tz=timezone.utc)

        return dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    except Exception as e:
        log.debug("Epoch conversion failed (%s): %s", value, e)
        return value


# ----------------------------------------------------------------------
# Fetch events
# ----------------------------------------------------------------------
def fetch_events(auth, last_ts, anchor=None, org_id=None):
    token = auth.authenticate()

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-type": "application/x-www-form-urlencoded;charset=UTF-8",
        "User-Agent": "innovare-siem-collector"
    }

    if not last_ts:
        last_ts = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S.%fZ")

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
    raw_items = payload.get("items", [])

    wrapped_items = []

    # ------------------------------------------------------------------
    # NORMALIZATION + WRAPPING
    # ------------------------------------------------------------------
    for event in raw_items:
        # --------------------------------------------------------------
        # Convert epoch timestamps inside details
        # --------------------------------------------------------------
        details = event.get("details")
        if isinstance(details, dict):
            if "clientTimestamp" in details:
                details["clientTimestamp"] = _epoch_to_iso(
                    details["clientTimestamp"]
                )

            if "systemDataTimeCreated" in details:
                details["systemDataTimeCreated"] = _epoch_to_iso(
                    details["systemDataTimeCreated"]
                )

        # --------------------------------------------------------------
        # FINAL WRAP (REQUESTED FORMAT)
        # --------------------------------------------------------------
        wrapped_items.append({
            "vendor": "withsecure",
            "withsecure": event
        })

    return wrapped_items, payload.get("nextAnchor")
