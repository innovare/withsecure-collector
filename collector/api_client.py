# collector/api_client.py
# VERSION: v1.4.1
#
# CHANGELOG:
# - Se añade normalización de campos categorías EDR y Riesgo
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
from collector.normalizers import (
    normalize_categories,
    normalize_risk
)

log = logging.getLogger(__name__)

API_URL = "https://api.connect.withsecure.com"
EVENTS_PATH = "/security-events/v1/security-events"


# ----------------------------------------------------------------------
# Helper: epoch (int | float | numeric str) -> ISO 8601 UTC
# ----------------------------------------------------------------------
def _epoch_to_iso(value):
    """
    Normaliza timestamps para SIEM.
    Acepta:
      - epoch (segundos o ms)
      - ISO 8601 con Z
      - ISO 8601 con offset
    Devuelve:
      YYYY-MM-DDTHH:MM:SS.mmm+0000
    """
    try:
        # --------------------------------------------------
        # Epoch (int / float / numeric str)
        # --------------------------------------------------
        if isinstance(value, (int, float)) or (
            isinstance(value, str) and value.isdigit()
        ):
            value = int(value)
            if value > 1_000_000_000_000:
                dt = datetime.fromtimestamp(value / 1000, tz=timezone.utc)
            else:
                dt = datetime.fromtimestamp(value, tz=timezone.utc)

            return dt.strftime("%Y-%m-%dT%H:%M:%S.%f+0000")

        # --------------------------------------------------
        # ISO string
        # --------------------------------------------------
        if isinstance(value, str):
            # Caso ISO terminado en Z
            if value.endswith("Z"):
                return value[:-1] + "+0000"

            # Caso ISO con offset (+00:00, +0000, etc.)
            try:
                dt = datetime.fromisoformat(
                    value.replace("Z", "+00:00")
                )
                dt = dt.astimezone(timezone.utc)
                return dt.strftime("%Y-%m-%dT%H:%M:%S.%f+0000")
            except ValueError:
                return value

        return value

    except Exception as e:
        log.debug("Timestamp conversion failed (%s): %s", value, e)
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
        
        if "serverTimestamp" in event:
            event["serverTimestamp"] = _epoch_to_iso(
                event["serverTimestamp"]
            )
            
        if "clientTimestamp" in event:
            event["clientTimestamp"] = _epoch_to_iso(
                event["clientTimestamp"]
            )
                                    
        if isinstance(details, dict):
            if "created" in details:
                details["created"] = _epoch_to_iso(
                    details["created"]
                )
                
            if "modified" in details:
                details["modified"] = _epoch_to_iso(
                    details["modified"]
                )
                           
            if "clientTimestamp" in details:
                details["clientTimestamp"] = _epoch_to_iso(
                    details["clientTimestamp"]
                )

            if "systemDataTimeCreated" in details:
                details["systemDataTimeCreated"] = _epoch_to_iso(
                    details["systemDataTimeCreated"]
                )

            # --------------------------------------------------------------
            # Semantic normalization
            # --------------------------------------------------------------
            if "categories" in details:
                details["categories"] = normalize_categories(
                    details["categories"]
                )

            if "risk" in details:
                details["risk"] = normalize_risk(
                    details["risk"]
                )
            
        # --------------------------------------------------------------
        # FINAL WRAP (REQUESTED FORMAT)
        # --------------------------------------------------------------
        wrapped_items.append({
            "vendor": "withsecure",
            "withsecure": event
        })

    return wrapped_items, payload.get("nextAnchor")
