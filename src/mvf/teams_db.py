
from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, List, Optional
import json, unicodedata, re
from .providers.sofascore import team_id_from_url

DB_PATH = Path("config/teams.json")

def _normalize(text: str) -> str:
    s = unicodedata.normalize("NFKD", text or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower()
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def _load() -> Dict[str, Any]:
    if DB_PATH.exists():
        try:
            return json.loads(DB_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"teams": []}

def _save(db: Dict[str, Any]) -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    DB_PATH.write_text(json.dumps(db, ensure_ascii=False, indent=2), encoding="utf-8")

def list_all() -> List[Dict[str, Any]]:
    return _load().get("teams", [])

def add_team(name: str, team_id: int, aliases: Optional[List[str]] = None, url: Optional[str] = None) -> None:
    db = _load()
    name = name.strip()
    aliases = [a.strip() for a in (aliases or []) if a and a.strip()]
    norm_name = _normalize(name)
    if url and not team_id:
        tid = team_id_from_url(url)
        if tid:
            team_id = tid
    for t in db["teams"]:
        if t.get("id") == team_id or _normalize(t.get("name","")) == norm_name or norm_name in [ _normalize(a) for a in t.get("aliases",[]) ]:
            t["name"] = t.get("name") or name
            t["id"] = team_id
            t["url"] = url or t.get("url")
            merged = set(a for a in t.get("aliases",[]) if a) | set(aliases) | {name}
            t["aliases"] = sorted(list(merged))
            _save(db)
            return
    db["teams"].append({"name": name, "id": team_id, "aliases": sorted(list(set(aliases)|{name})), "url": url})
    _save(db)

def find_team_id(query_name: str) -> Optional[int]:
    q = _normalize(query_name)
    if not q:
        return None
    db = _load()
    best = (0, None)
    for t in db.get("teams", []):
        candidates = [t.get("name","")] + t.get("aliases",[])
        for cand in candidates:
            c = _normalize(cand)
            if c == q:
                return t.get("id")
            qs = set(q.split())
            cs = set(c.split())
            inter = len(qs & cs)
            score = 2*inter - abs(len(qs)-len(cs))
            if score > best[0]:
                best = (score, t.get("id"))
    return best[1]

def ensure_team(name: str, team_id: int, url: Optional[str] = None, aliases: Optional[List[str]] = None) -> None:
    if not find_team_id(name):
        add_team(name, team_id, aliases=aliases, url=url)
