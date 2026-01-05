# collector/save_events.py
# VERSION: v1.0.1
#
# CHANGELOG:
# - Usa output_log definido por cliente en config.yml
# - No asume estructura de carpetas
# - Crea directorio si no existe
# - Mantiene formato JSONL

import json
from pathlib import Path
import logging

log = logging.getLogger(__name__)


def save_events(output_log: str, events: list):
    """
    Guarda eventos en el archivo definido por cliente (JSONL).
    """

    if not events:
        return

    output_path = Path(output_log)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("a", encoding="utf-8") as fh:
        for event in events:
            fh.write(json.dumps(event, ensure_ascii=False) + "\n")
        fh.flush()

    log.debug(
        "Saved %s events into %s",
        len(events),
        output_path
    )
