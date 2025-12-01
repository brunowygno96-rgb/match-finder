
from __future__ import annotations
from typing import List, Dict, Any, Optional
from pathlib import Path
from collections import defaultdict

from .runner_next import run_next
from .providers.sofascore import team_id_from_url, search_team_id
from .teams_db import find_team_id as db_find_team_id

ATHLETES_PATH = Path("config/athletes.json")

def load_athletes() -> List[Dict[str, Any]]:
    if ATHLETES_PATH.exists():
        try:
            import json
            return json.loads(ATHLETES_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return [
        {"name": "Atleta A", "team_id": 306038, "team_label": "Cartagena FS"},
        {"name": "Atleta B", "team_id": 306038, "team_label": "Cartagena FS"}
    ]

def _resolve_team_id(entry: Dict[str, Any]) -> Optional[int]:
    if entry.get("team_id"):
        return int(entry["team_id"])
    if entry.get("team_url"):
        tid = team_id_from_url(entry["team_url"])
        if tid:
            return tid
    if entry.get("team_name"):
        tid = db_find_team_id(entry["team_name"])
        if tid:
            return tid
        return search_team_id(entry["team_name"])
    return None

def run_multi(next_per_team: int = 2, tz: str = "America/Fortaleza") -> Dict[str, Any]:
    athletes = load_athletes()
    agenda = defaultdict(list)

    for ent in athletes:
        name = ent.get("name") or "Sem nome"
        team_id = _resolve_team_id(ent)
        label = ent.get("team_label") or ent.get("team_name") or (f"sofascore:{team_id}" if team_id else "")
        if not team_id:
            continue

        result = run_next(team=None, limit=next_per_team, tz=tz, team_id=team_id, team_url=None)
        for m in result.get("upcoming", []):
            date_key = m["date_local"]
            line = {
                "athlete": name,
                "team_label": label,
                "tournament": m.get("tournament",""),
                "time_local": m.get("time_local",""),
                "date_local": m.get("date_local",""),
                "event_url": m.get("event_url",""),
                "vs": f"{m.get('home','')} x {m.get('away','')}",
            }
            agenda[date_key].append(line)

    sorted_days = sorted(agenda.keys())
    grouped = [{"date": day, "items": agenda[day]} for day in sorted_days]
    return {"days": grouped, "count": sum(len(v) for v in agenda.values())}
