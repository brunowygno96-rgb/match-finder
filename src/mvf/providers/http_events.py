# src/mvf/providers/http_events.py
from __future__ import annotations
from typing import List, Dict, Any
from datetime import datetime, timezone

import requests

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

def fetch_next_events(team_id: int) -> List[Dict[str, Any]]:
    """
    Versão sem Selenium: chama diretamente a API pública do SofaScore.
    """
    url = f"https://api.sofascore.com/api/v1/team/{team_id}/events/next/0"
    headers = {
        "User-Agent": UA,
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://www.sofascore.com/",
        "Origin": "https://www.sofascore.com",
    }
    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    out: List[Dict[str, Any]] = []
    for ev in data.get("events", []) or []:
        ts = ev.get("startTimestamp")
        if not ts:
            continue
        out.append(
            {
                "ts": int(ts),
                "date_utc": datetime.fromtimestamp(int(ts), tz=timezone.utc),
                "home": ev.get("homeTeam", {}).get("name", ""),
                "away": ev.get("awayTeam", {}).get("name", ""),
                "tournament": ev.get("tournament", {}).get("name", ""),
                "sofascore_event_id": ev.get("id"),
            }
        )

    out.sort(key=lambda e: e["ts"])
    return out
