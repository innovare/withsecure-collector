# collector/config_loader.py
# VERSION: v1.3.0
#
# CHANGELOG:
# - Implementa hot-reload REAL usando mtime
# - Cachea configuración en memoria
# - NO rompe validaciones existentes
# - Log explícito cuando config.yml cambia

def load_config():
    import os
    import yaml
    import logging
    from pathlib import Path

    log = logging.getLogger(__name__)

    # ------------------------------------------------------------
    # Cache estático en función
    # ------------------------------------------------------------
    if not hasattr(load_config, "_cache"):
        load_config._cache = {
            "mtime": None,
            "config": None
        }

    config_path = os.getenv("COLLECTOR_CONFIG", "config.yml")
    path = Path(config_path)

    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path.resolve()}")

    current_mtime = path.stat().st_mtime

    # ------------------------------------------------------------
    # HOT-RELOAD REAL (solo si el archivo cambió)
    # ------------------------------------------------------------
    if load_config._cache["mtime"] != current_mtime:
        with open(path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        if "clients" not in config or not isinstance(config["clients"], list):
            raise ValueError("config.yml must contain a 'clients' list")

        required_fields = [
            "client_id",
            "client_secret",
            #"token_url",
            #"events_url",
            "interval",
            #"output_log",
            #"state_file"
        ]

        for idx, client in enumerate(config["clients"]):
            for field in required_fields:
                if field not in client:
                    raise ValueError(f"Missing '{field}' in clients[{idx}]")

            # Rate-limit opcional
            if "rate_limit_per_minute" not in client:
                client["rate_limit_per_minute"] = 60

            if not isinstance(client["rate_limit_per_minute"], int) or client["rate_limit_per_minute"] <= 0:
                raise ValueError(
                    f"Invalid rate_limit_per_minute in clients[{idx}]"
                )

        load_config._cache["mtime"] = current_mtime
        load_config._cache["config"] = config

        log.info("config.yml reloaded (mtime changed)")

    return load_config._cache["config"]
