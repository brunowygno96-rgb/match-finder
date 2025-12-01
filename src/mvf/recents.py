
from __future__ import annotations
from typing import List, Dict, Any, Optional
from pathlib import Path
import json, time, unicodedata, re

RECENTS_PATH = Path("config/recents.json")
MAX_RECENTS = 15

def _normalize(text: str) -> str:
    s = unicodedata.normalize("NFKD", text or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower()
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def _load() -> Dict[str, Any]:
    if RECENTS_PATH.exists():
        try:
            return json.loads(RECENTS_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"items": []}

def _save(db: Dict[str, Any]) -> None:
    RECENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    RECENTS_PATH.write_text(json.dumps(db, ensure_ascii=False, indent=2), encoding="utf-8")

def list_recents() -> List[Dict[str, Any]]:
    db = _load()
    items = db.get("items", [])
    items.sort(key=lambda x: x.get("ts", 0), reverse=True)
    return items[:MAX_RECENTS]

def add_recent(name: Optional[str], team_id: Optional[int], url: Optional[str]) -> None:
    db = _load()
    items = db.get("items", [])
    key_id = str(team_id) if team_id else ""
    key_name = _normalize(name or "")
    new = []
    exists = False
    for it in items:
        if (key_id and str(it.get("team_id")) == key_id) or (key_name and _normalize(it.get("name","")) == key_name):
            if not exists:
                new.append({
                    "name": name or it.get("name") or "",
                    "team_id": team_id if team_id is not None else it.get("team_id"),
                    "url": url or it.get("url"),
                    "ts": int(time.time()),
                })
                exists = True
        else:
            new.append(it)
    if not exists:
        new.insert(0, {"name": name or (f"sofascore:{team_id}" if team_id else ""), "team_id": team_id, "url": url, "ts": int(time.time())})
    db["items"] = new[:MAX_RECENTS]
    _save(db)

def clear_recents() -> None:
    _save({"items": []})
