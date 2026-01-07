# collector/api_client.py
# VERSION: v1.3.4
#
# FIX:
# - clientTimestamp y systemDataTimeCreated pueden venir como STRING epoch
# - Se convierten correctamente a ISO 8601
# - Sin alterar otros campos

import logging
import requests
from datetime import datetime, timezone

log = logging.getLogger(__name__)

API_URL = "https://api.connect.withsecure.com"
EVENTS_PATH = "/security-events/v1/security-events"


# ----------------------------------------------------------------------
# Helper: epoch (int | float | numeric str) -> ISO 8601
# ----------------------------------------------------------------------
def _epoch_to_iso(value):
    """
    Convierte epoch (segundos o milisegundos) a ISO 8601 UTC.
    Acepta int, float o string numérico.
    """
    try:
        # Soportar epoch como string numérico
        if isinstance(value, str):
            if not value.isdigit():
                return value
            value = int(value)

        if not isinstance(value, (int, float)):
            return value

        # Milisegundos vs segundos
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

    # ------------------------------------------------------------------
    # ENRICHMENT
    # ------------------------------------------------------------------
    for event in items:
        # Vendor
        event["vendor"] = "WithSecure"

        details = event.get("details")
        if not isinstance(details, dict):
            continue

        # Convertir SOLO los campos solicitados
        if "clientTimestamp" in details:
            details["clientTimestamp"] = _epoch_to_iso(
                details["clientTimestamp"]
            )

        if "systemDataTimeCreated" in details:
            details["systemDataTimeCreated"] = _epoch_to_iso(
                details["systemDataTimeCreated"]
            )

    return items, payload.get("nextAnchor")
