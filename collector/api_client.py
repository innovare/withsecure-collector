# collector/api_client.py
# VERSION: v1.3.8
#
# CHANGE:
# - Agrupa todos los campos del evento bajo "withsecure"
# - Mantiene vendor en top-level
# - Compatible con Wazuh JSON native decoding
#

import logging
import requests
from datetime import datetime, timezone

from collector.normalizers import (
    normalize_categories,
    normalize_risk
)

log = logging.getLogger(__name__)

API_URL = "https://api.connect.withsecure.com"
EVENTS_PATH = "/security-events/v1/security-events"


# ----------------------------------------------------------------------
# Helper: epoch (int | float | numeric str) -> ISO 8601
# ----------------------------------------------------------------------
def _epoch_to_iso(value):
    try:
        if isinstance(value, str):
            if not value.isdigit():
                return value
            value = int(value)

        if not isinstance(value, (int, float)):
            return value

        if value > 1_000_000_000_000:
            dt = datetime.fromtimestamp(value / 1000, tz=timezone.utc)
        else:
            dt = datetime.fromtimestamp(value, tz=timezone.utc)

        return dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    except Exception as e:
        log.debug("Epoch conversion failed (%s): %s", value, e)
        return value


# ----------------------------------------------------------------------
# API
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
        last_ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    params = {
        "limit": 200,
        "engineGroup": ["epp", "edr"],
        "persistenceTimestampStart": last_ts,
        "order": "asc",
        "exclusiveStart": "true",
        "language": "es-MX",
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
    items = payload.get("items", [])

    output_events = []

    # ------------------------------------------------------------------
    # ENRICHMENT + REPACK
    # ------------------------------------------------------------------
    for event in items:
        details = event.get("details")
        if isinstance(details, dict):

            # Timestamp normalization
            if "clientTimestamp" in details:
                details["clientTimestamp"] = _epoch_to_iso(
                    details["clientTimestamp"]
                )

            if "systemDataTimeCreated" in details:
                details["systemDataTimeCreated"] = _epoch_to_iso(
                    details["systemDataTimeCreated"]
                )

            # Semantic normalization
            if "categories" in details:
                details["categories"] = normalize_categories(
                    details["categories"]
                )

            if "risk" in details:
                details["risk"] = normalize_risk(
                    details["risk"]
                )

        # --------------------------------------------------------------
        # FINAL STRUCTURE (SIEM-SAFE)
        # --------------------------------------------------------------
        wrapped_event = {
            "vendor": "WithSecure",
            "withsecure": event
        }

        # Evitar duplicar vendor dentro del objeto
        wrapped_event["withsecure"].pop("vendor", None)

        output_events.append(wrapped_event)

    return output_events, payload.get("nextAnchor")
