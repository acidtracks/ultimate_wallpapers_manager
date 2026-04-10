import json
from pathlib import Path


def read(state_file: Path) -> dict:
    try:
        return json.loads(state_file.read_text())
    except Exception:
        return {"last_category": "game"}


def write(state_file: Path, data: dict) -> None:
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text(json.dumps(data))
