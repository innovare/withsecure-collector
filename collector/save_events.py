# collector/save_events.py
# VERSION: v1.3.0
#
# CHANGELOG:
# - Crea directorio si no existe
# - Mantiene formato JSONL

import json
from pathlib import Path
import logging

log = logging.getLogger(__name__)


def save_events(output_name: str, events: list):
    """
    Guarda eventos en el archivo definido por cliente (JSONL).
    """
    output_log = "events/" + output_name + '.log'

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
