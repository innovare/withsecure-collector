# collector/log_files.py
# VERSION: v1.0.0
#
# PURPOSE:
# - Garantiza la existencia de archivos .log por cliente
# - Requerido por Wazuh LogCollector
# - No escribe eventos falsos

import logging
from pathlib import Path

log = logging.getLogger(__name__)

EVENTS_DIR = Path("events")


def ensure_client_log(client_name: str) -> Path:
    """
    Crea el archivo de log del cliente si no existe.
    Devuelve la ruta del archivo.
    """
    EVENTS_DIR.mkdir(parents=True, exist_ok=True)

    log_path = EVENTS_DIR / f"{client_name}.log"

    if not log_path.exists():
        log_path.touch()
        log.info(
            "Wazuh log file created for client '%s': %s",
            client_name,
            log_path
        )

    return log_path
