"""Load/save the set of already-seen product codes."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

STATE_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "seen_products.json"


def load_state(path: Path = STATE_PATH) -> dict[str, dict]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        content = f.read().strip()
    return json.loads(content) if content else {}


def save_state(state: dict[str, dict], path: Path = STATE_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, sort_keys=True, ensure_ascii=False)
        f.write("\n")


def record_seen(state: dict[str, dict], code: str, name: str, url: str) -> None:
    state[code] = {
        "name": name,
        "url": url,
        "first_seen": date.today().isoformat(),
    }


def last_find(state: dict[str, dict]) -> tuple[str | None, int]:
    """Newest ``first_seen`` date across the state, and how many items share it.

    Used by the weekly heartbeat email; the per-item ``first_seen`` already records
    this, so no extra state file is needed.
    """
    dates = [entry["first_seen"] for entry in state.values() if entry.get("first_seen")]
    if not dates:
        return None, 0
    newest = max(dates)
    return newest, dates.count(newest)
