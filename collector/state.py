# collector/state.py
# VERSION: v1.3.0
# CHANGELOG:
# - Guarda correctamente anchor por cliente

import json
from pathlib import Path

STATE_DIR = Path("state")
STATE_DIR.mkdir(exist_ok=True)

def load_state(client):
    f = STATE_DIR / f"{client}.json"
    if not f.exists():
        return {}
    return json.loads(f.read_text())

def save_state(client, state):
    f = STATE_DIR / f"{client}.json"
    f.write_text(json.dumps(state, indent=2))
