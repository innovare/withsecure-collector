# collector/logger.py
# VERSION: v1.3.0
#
# CHANGELOG:
# - DEBUG siempre se guarda en log/withsecure-collector.log
# - Consola muestra INFO+ por defecto
# - DEBUG en consola solo si DEBUG=1
# - Mantiene filename en el LOG

import logging
import os
import sys
from pathlib import Path

LOG_DIR = Path("log")
LOG_DIR.mkdir(exist_ok=True)

LOG_FILE = LOG_DIR / "withsecure-collector.log"

class LevelBasedStreamHandler(logging.StreamHandler):
    def emit(self, record):
        if record.levelno >= logging.WARNING:
            self.stream = sys.stderr
        else:
            self.stream = sys.stdout
        super().emit(record)
        
def setup_logger():
    # ------------------------------------------------------------
    # Root logger
    # ------------------------------------------------------------
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)  # capturamos TODO

    # ------------------------------------------------------------
    # Formatter
    # ------------------------------------------------------------
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(filename)s: %(message)s"
    )

    # ------------------------------------------------------------
    # File handler (DEBUG → archivo)
    # ------------------------------------------------------------
    file_handler = logging.FileHandler(
        LOG_FILE,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # ------------------------------------------------------------
    # Console handler
    # ------------------------------------------------------------
    debug_console = os.getenv("DEBUG", "0") == "1"

    console_handler = LevelBasedStreamHandler()
    console_handler.setLevel(
        logging.DEBUG if debug_console else logging.INFO
    )
    console_handler.setFormatter(formatter)

    # ------------------------------------------------------------
    # Avoid duplicate handlers on reload
    # ------------------------------------------------------------
    if not root.handlers:
        root.addHandler(file_handler)
        root.addHandler(console_handler)
