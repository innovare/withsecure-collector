# collector/config_loader.py
# VERSION: v1.3.1
#
# CHANGELOG:
# - Mantiene hot-reload REAL usando mtime
# - Cachea configuración en memoria
# - Valida estructura multi-tenant
# - NEW: start_mode por cliente (state | now | fixed)
# - NEW: start_date requerido cuando start_mode=fixed
# - Mantiene rate_limit_per_minute por cliente
# - NO rompe validaciones existentes

def load_config():
    import os
    import yaml
    import logging
    from pathlib import Path

    log = logging.getLogger(__name__)

    # ------------------------------------------------------------
    # Static cache (function attribute)
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
    # HOT-RELOAD REAL (only if file changed)
    # ------------------------------------------------------------
    if load_config._cache["mtime"] != current_mtime:
        with open(path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        # --------------------------------------------------------
        # Global validation
        # --------------------------------------------------------
        if "clients" not in config or not isinstance(config["clients"], list):
            raise ValueError("config.yml must contain a 'clients' list")

        # --------------------------------------------------------
        # Required client fields (base)
        # --------------------------------------------------------
        required_fields = [
            "name",
            "client_id",
            "client_secret",
            "interval",
        ]

        for idx, client in enumerate(config["clients"]):
            # --------------------------------------------
            # Mandatory fields
            # --------------------------------------------
            for field in required_fields:
                if field not in client:
                    raise ValueError(
                        f"Missing '{field}' in clients[{idx}]"
                    )

            # --------------------------------------------
            # Optional: rate-limit per tenant
            # --------------------------------------------
            if "rate_limit_per_minute" not in client:
                client["rate_limit_per_minute"] = 60

            if (
                not isinstance(client["rate_limit_per_minute"], int)
                or client["rate_limit_per_minute"] <= 0
            ):
                raise ValueError(
                    f"Invalid rate_limit_per_minute in clients[{idx}]"
                )

            # --------------------------------------------
            # NEW: start_mode handling
            # --------------------------------------------
            if "start_mode" not in client:
                client["start_mode"] = "state"

            if client["start_mode"] not in ("state", "now", "fixed"):
                raise ValueError(
                    f"Invalid start_mode in clients[{idx}]"
                )

            if client["start_mode"] == "fixed":
                if "start_date" not in client:
                    raise ValueError(
                        f"start_date required when start_mode='fixed' in clients[{idx}]"
                    )

        # --------------------------------------------------------
        # Update cache
        # --------------------------------------------------------
        load_config._cache["mtime"] = current_mtime
        load_config._cache["config"] = config

        log.info("config.yml reloaded (mtime changed)")

    return load_config._cache["config"]
