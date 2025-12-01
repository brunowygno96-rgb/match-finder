from __future__ import annotations
from typing import List, Dict, Any
from pathlib import Path
from collections import defaultdict
import json

from .runner_next import run_next

ATHLETES_PATH = Path("config/athletes.json")


def load_athletes() -> List[Dict[str, Any]]:
    """
    Lê config/athletes.json.
    Estrutura esperada:
    [
      {
        "name": "Nome do atleta",
        "team_label": "Nome do time",
        "team_id": 123456,
        "team_url": "https://www.sofascore.com/..."
      },
      ...
    ]
    """
    if not ATHLETES_PATH.exists():
        return []

    try:
        with ATHLETES_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
    except Exception:
        pass

    return []


def run_multi(next_per_team: int = 2, tz: str = "America/Fortaleza") -> Dict[str, Any]:
    """
    Monta uma agenda agrupada por dia para todos os atletas do arquivo athletes.json.
    Usa a função run_next para cada atleta/time.
    """
    athletes = load_athletes()
    agenda = defaultdict(list)

    for entry in athletes:
        name = entry.get("name") or ""
        label = entry.get("team_label") or entry.get("team") or ""
        team_id = entry.get("team_id")
        team_url = entry.get("team_url")

        if not (team_id or team_url or label):
            continue

        result = run_next(
            team=label,
            limit=next_per_team,
            tz=tz,
            team_id=team_id,
            team_url=team_url,
            debug=False,
        )

        if not result.get("ok"):
            # se deu erro pra esse atleta, ignora (ou poderia logar)
            continue

        for m in result.get("upcoming", []):
            date_key = m.get("date_local")
            if not date_key:
                continue

            line = {
                "athlete": name,
                "team_label": label,
                "tournament": m.get("tournament", ""),
                "time_local": m.get("time_local", ""),
                "date_local": m.get("date_local", ""),
                "event_url": m.get("event_url", ""),
                "vs": f"{m.get('home', '')} x {m.get('away', '')}",
            }
            agenda[date_key].append(line)

    sorted_days = sorted(agenda.keys())
    grouped = [{"date": day, "items": agenda[day]} for day in sorted_days]
    return {"days": grouped, "count": sum(len(v) for v in agenda.values())}
