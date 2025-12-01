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

BASE_HEADERS = {
    "User-Agent": UA,
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    "Origin": "https://www.sofascore.com",
    "Referer": "https://www.sofascore.com/",
}

def fetch_next_events(team_id: int) -> List[Dict[str, Any]]:
    """
    Busca os próximos jogos de um time direto na API pública do SofaScore,
    sem usar Selenium ou navegador.
    """
    url = f"https://api.sofascore.com/api/v1/team/{team_id}/events/next/0"

    resp = requests.get(url, headers=BASE_HEADERS, timeout=10)
    resp.raise_for_status()  # se der 4xx/5xx aqui, levanta exceção

    data = resp.json()
    events = data.get("events", []) or []

    out: List[Dict[str, Any]] = []
    for ev in events:
        ts = ev.get("startTimestamp")
        if not ts:
            continue

        dt_utc = datetime.fromtimestamp(int(ts), tz=timezone.utc)

        out.append(
            {
                "ts": int(ts),
                "date_utc": dt_utc,
                "home": ev.get("homeTeam", {}).get("name", ""),
                "away": ev.get("awayTeam", {}).get("name", ""),
                "tournament": ev.get("tournament", {}).get("name", ""),
                "sofascore_event_id": ev.get("id"),
            }
        )

    # ordenar por data
    out.sort(key=lambda e: e["ts"])
    return out
