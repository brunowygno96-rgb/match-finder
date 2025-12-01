
from __future__ import annotations
import argparse, json
from .providers.sofascore import search_team_id, team_id_from_url
from .providers.browser_events import fetch_next_events
from .utils import to_local, now_utc
from .teams_db import find_team_id as db_find_team_id, ensure_team as db_ensure_team

def run_next(team: str | None, limit: int, tz: str = "America/Fortaleza",
             team_id: int | None = None, team_url: str | None = None, debug: bool = False):
    if team_id is None and team_url:
        team_id = team_id_from_url(team_url)
    if team_id is None and team:
        team_id = db_find_team_id(team)
    if team_id is None and team:
        team_id = search_team_id(team)
    if not team_id:
        label = team or team_url or "unknown"
        return {"team": label, "error": "Team not found on SofaScore"}
    items = fetch_next_events(team_id=team_id)
    items = items[:max(limit,0)]
    if team:
        db_ensure_team(team, team_id, url=team_url)
    out_matches = []
    for e in items:
        loc = to_local(e["date_utc"], tz)
        out_matches.append({
            "date_local": loc.date().isoformat(),
            "time_local": loc.strftime("%H:%M"),
            "home": e["home"],
            "away": e["away"],
            "tournament": e["tournament"],
            "sofascore_event_id": e["sofascore_event_id"],
            "event_url": f"https://www.sofascore.com/event/{e['sofascore_event_id']}"
        })
    return {
        "team": team if team else f"sofascore:{team_id}",
        "checked_at": to_local(now_utc(), tz).isoformat(),
        "upcoming": out_matches
    }

def main():
    ap = argparse.ArgumentParser(description="Buscar próximos jogos de um time no SofaScore (sem YouTube)")
    ap.add_argument("--team", help="Nome do time (ex: 'Benfica Futsal')")
    ap.add_argument("--team-id", type=int, help="ID do time no SofaScore (ex: 306038)")
    ap.add_argument("--team-url", help="URL do time no SofaScore (ex: https://.../team/cartagena-fs/306038)")
    ap.add_argument("--next", type=int, default=3, help="Quantos próximos jogos listar (default=3)")
    ap.add_argument("--tz", default="America/Fortaleza", help="Timezone para datas locais")
    ap.add_argument("--debug", action="store_true", help="Log extra")
    args = ap.parse_args()
    result = run_next(args.team, args.next, tz=args.tz, team_id=args.team_id, team_url=args.team_url, debug=args.debug)
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
