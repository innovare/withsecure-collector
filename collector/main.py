# collector/main.py
# VERSION: v1.3.1
#
# CHANGELOG:
# - NEW: start_mode por cliente (state | now | fixed)
# - NEW: start_date soportado con hot-reload
# - Mantiene scheduler cooperativo
# - Mantiene rate-limit por tenant
# - NO rompe state ni paginación
# - Compatible con graceful shutdown

import time
import json
import logging
import signal
from datetime import datetime, timezone
from pathlib import Path

from collector.logger import setup_logger
from collector.authentication import WithSecureAuth
from collector.api_client import fetch_events
from collector.state import load_state, save_state
from collector.save_events import save_events
from collector.config_loader import load_config

# --------------------------------------------------------------------
# Logging
# --------------------------------------------------------------------
setup_logger()
log = logging.getLogger(__name__)

CONFIG_PATH = Path("config.yml")

# --------------------------------------------------------------------
# Graceful shutdown flag
# --------------------------------------------------------------------
shutdown_requested = False

def handle_shutdown(signum, frame):
    global shutdown_requested
    shutdown_requested = True
    log.warning(
        "Shutdown signal received (%s). Finishing current cycle...",
        signum
    )

signal.signal(signal.SIGINT, handle_shutdown)
signal.signal(signal.SIGTERM, handle_shutdown)

# --------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------
def utc_now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")

# --------------------------------------------------------------------
# MAIN
# --------------------------------------------------------------------
def main():
    log.info("WithSecure Events Collector started")

    # ------------------------------------------------------------
    # Scheduler state (IN-MEMORY)
    # ------------------------------------------------------------
    sched = {}
    last_config_mtime = None
    config = None

    while not shutdown_requested:
        now = time.monotonic()

        # ========================================================
        # HOT-RELOAD CONFIG
        # ========================================================
        try:
            mtime = CONFIG_PATH.stat().st_mtime
        except FileNotFoundError:
            log.error("config.yml not found")
            time.sleep(5)
            continue

        if last_config_mtime != mtime:
            log.info("Reloading config.yml")
            config = load_config()
            last_config_mtime = mtime

            for client in config["clients"]:
                name = client["name"]
                if name not in sched:
                    sched[name] = {
                        "next_run": 0.0,
                        "auth": WithSecureAuth(
                            client["client_id"],
                            client["client_secret"]
                        ),
                        "rate_limit_until": 0.0,

                        # -----------------------------------------
                        # NEW: flag para aplicar start_mode una sola vez
                        # -----------------------------------------
                        "start_initialized": False,
                    }

        # ========================================================
        # SELECT NEXT CLIENT
        # ========================================================
        next_client = None
        next_time = None

        for client in config["clients"]:
            name = client["name"]
            if sched[name]["next_run"] <= now:
                next_client = client
                break

            if next_time is None or sched[name]["next_run"] < next_time:
                next_time = sched[name]["next_run"]

        if not next_client:
            time.sleep(max(0.1, next_time - now))
            continue

        # ========================================================
        # EXECUTE CLIENT
        # ========================================================
        name = next_client["name"]
        interval = next_client["interval"]

        log.info("Processing client: '%s'", name)

        # -----------------------------
        # Rate-limit per tenant
        # -----------------------------
        if sched[name]["rate_limit_until"] > now:
            sched[name]["next_run"] = sched[name]["rate_limit_until"]
            continue

        state = load_state(name)

        # ========================================================
        # NEW: start_mode resolution (ONCE per process or reload)
        # ========================================================
        if not sched[name]["start_initialized"]:
            mode = next_client.get("start_mode", "state")

            if mode == "state" and "last_ts" in state:
                last_ts = state["last_ts"]
                log.debug("start_mode=state last_ts=%s", last_ts)

            elif mode == "now":
                last_ts = utc_now_iso()
                log.info("start_mode=now starting at %s", last_ts)

            elif mode == "fixed":
                last_ts = next_client["start_date"]
                log.info("start_mode=fixed starting at %s", last_ts)

            else:
                last_ts = utc_now_iso()
                log.warning("start_mode fallback to now")

            sched[name]["start_initialized"] = True
            anchor = None

        else:
            last_ts = state.get("last_ts", utc_now_iso())
            anchor = state.get("anchor")

        total_events = 0
        page = 0
        last_event_ts = last_ts

        try:
            while True:
                page += 1

                items, next_anchor = fetch_events(
                    auth=sched[name]["auth"],
                    last_ts=last_event_ts,
                    anchor=anchor,
                    org_id=next_client.get("organization_id")
                )

                if not items:
                    break

                save_events(name, items)

                for ev in items:
                    total_events += 1

                    ws = ev.get("withsecure", {})
                    ts = ws.get("persistenceTimestamp")

                    if ts:
                        last_event_ts = ts

                if not next_anchor:
                    break

                anchor = next_anchor

        except RuntimeError as e:
            msg = str(e)
            if "429" in msg:
                sched[name]["rate_limit_until"] = now + interval
                log.warning("Rate-limit detected for %s", name)
            else:
                log.error("  - Client '%s' failed: %s", name, msg)

        # -----------------------------
        # SAVE STATE ALWAYS
        # -----------------------------
        save_state(
            name,
            {
                "last_ts": last_event_ts,
                "anchor": anchor
            }
        )

        sched[name]["next_run"] = now + interval

        log.info(
            "  - Polling for %s finished. events=%s pages=%s last_ts=%s",
            name,
            total_events,
            page,
            last_event_ts
        )

        log.info(
            "  - Next polling: %s in %s seconds.",
            name,
            interval
        )

    # ============================================================
    # FINAL SHUTDOWN
    # ============================================================
    log.warning("Collector stopped gracefully")

# --------------------------------------------------------------------
# ENTRY POINT
# --------------------------------------------------------------------
if __name__ == "__main__":
    main()
