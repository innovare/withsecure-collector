# collector/main.py
# VERSION: v1.3.2
#
# FIXES:
# - Corrige avance de last_ts leyendo persistenceTimestamp real
# - Protección contra timestamps repetidos
# - Compatible con exclusiveStart=true (API WithSecure)
# - Mantiene state, anchor y paginación
# - Comentarios explicativos incluidos

import time
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
# Graceful shutdown
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
    """Devuelve timestamp ISO UTC"""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")

# --------------------------------------------------------------------
# MAIN
# --------------------------------------------------------------------
def main():
    log.info("WithSecure Events Collector started")

    # ------------------------------------------------------------
    # Scheduler en memoria por cliente
    # ------------------------------------------------------------
    sched = {}
    last_config_mtime = None
    config = None

    while not shutdown_requested:
        now = time.monotonic()

        # ========================================================
        # HOT-RELOAD config.yml
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

            # Inicializa estructura por cliente
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
                        # start_mode se aplica SOLO una vez
                        "start_initialized": False,
                    }

        # ========================================================
        # Selección de cliente listo para ejecutar
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
        # Ejecución del cliente
        # ========================================================
        name = next_client["name"]
        interval = next_client["interval"]

        log.info("Processing client: '%s'", name)

        # --------------------------------------------------------
        # Rate-limit por cliente
        # --------------------------------------------------------
        if sched[name]["rate_limit_until"] > now:
            sched[name]["next_run"] = sched[name]["rate_limit_until"]
            continue

        state = load_state(name)

        # ========================================================
        # start_mode (solo la primera vez)
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

            anchor = None
            sched[name]["start_initialized"] = True

        else:
            last_ts = state.get("last_ts", utc_now_iso())
            anchor = state.get("anchor")

        # ========================================================
        # Variables de control
        # ========================================================
        total_events = 0
        page = 0
        last_event_ts = last_ts

        # --------------------------------------------------------
        # PROTECCIÓN:
        # Guarda último timestamp procesado para evitar loops
        # --------------------------------------------------------
        last_seen_ts = last_ts

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

                # --------------------------------------------------
                # Orden defensivo por timestamp (API puede variar)
                # --------------------------------------------------
                items.sort(
                    key=lambda e: e.get("withsecure", {}).get(
                        "persistenceTimestamp", ""
                    )
                )

                save_events(name, items)

                for ev in items:
                    total_events += 1

                    # --------------------------------------------------
                    # LECTURA CORRECTA DEL TIMESTAMP REAL
                    # --------------------------------------------------
                    ws = ev.get("withsecure", {})
                    ts = ws.get("persistenceTimestamp")

                    if not ts:
                        continue

                    # --------------------------------------------------
                    # PROTECCIÓN CONTRA TIMESTAMPS REPETIDOS
                    #
                    # WithSecure usa exclusiveStart=true:
                    # - persistenceTimestampStart es EXCLUSIVO
                    # - Si enviamos el mismo ts, el API devuelve lo mismo
                    #
                    # Por eso SOLO avanzamos si el timestamp AUMENTA
                    # --------------------------------------------------
                    if ts > last_event_ts:
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
                log.error("Client '%s' failed: %s", name, msg)

        # ========================================================
        # Guardar estado SIEMPRE
        # ========================================================
        save_state(
            name,
            {
                "last_ts": last_event_ts,
                "anchor": anchor
            }
        )

        sched[name]["next_run"] = now + interval

        log.info(
            "Polling finished for %s | events=%s pages=%s last_ts=%s",
            name,
            total_events,
            page,
            last_event_ts
        )

        log.info(
            "Next polling for %s in %s seconds",
            name,
            interval
        )

    log.warning("Collector stopped gracefully")

# --------------------------------------------------------------------
# ENTRY POINT
# --------------------------------------------------------------------
if __name__ == "__main__":
    main()
