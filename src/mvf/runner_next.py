from __future__ import annotations
from typing import Optional, Dict, Any, List
import argparse, json

from .providers.sofascore import search_team_id, team_id_from_url
from .providers.http_events import fetch_next_events
from .utils import to_local, now_utc


def _resolve_team_id(
    team: Optional[str],
    team_id: Optional[int],
    team_url: Optional[str],
) -> Optional[int]:
    """
    Resolve o ID do time a partir de (team_id, team_url, nome).
    Prioridade:
    1) team_id indicado
    2) team_url (extrai id da URL)
    3) nome do time -> busca na API do SofaScore
    """
    if team_id:
        return int(team_id)

    if team_url:
        tid = team_id_from_url(team_url)
        if tid:
            return tid

    if team:
        tid = search_team_id(team)
        if tid:
            return tid

    return None


def run_next(
    team: Optional[str],
    limit: int,
    tz: str = "America/Fortaleza",
    team_id: Optional[int] = None,
    team_url: Optional[str] = None,
    debug: bool = False,
) -> Dict[str, Any]:
    """
    Busca os próximos jogos de um time usando apenas a API HTTP do SofaScore.
    Retorna um dicionário com metadados e lista de partidas.
    """

    tid = _resolve_team_id(team, team_id, team_url)
    if tid is None:
        return {
            "ok": False,
            "error": "team_not_found",
            "message": "Não foi possível resolver o ID do time.",
            "team_input": team,
            "team_url": team_url,
        }

    try:
        events = fetch_next_events(tid)
    except Exception as e:
        return {
            "ok": False,
            "error": "fetch_failed",
            "message": f"Erro ao consultar SofaScore: {e!s}",
            "team_id": tid,
        }

    # limita quantidade
    events = events[: max(0, limit)]

    upcoming: List[Dict[str, Any]] = []
    for ev in events:
        dt_local = to_local(ev["date_utc"], tz=tz)
        date_local = dt_local.strftime("%Y-%m-%d")
        time_local = dt_local.strftime("%H:%M")

        event_id = ev.get("sofascore_event_id")
        event_url = (
            f"https://www.sofascore.com/event/{event_id}"
            if event_id
            else None
        )

        upcoming.append(
            {
                "date_local": date_local,
                "time_local": time_local,
                "home": ev.get("home", ""),
                "away": ev.get("away", ""),
                "tournament": ev.get("tournament", ""),
                "sofascore_event_id": event_id,
                "event_url": event_url,
            }
        )

    return {
        "ok": True,
        "team": team,
        "team_id": tid,
        "tz": tz,
        "checked_at": now_utc().isoformat(),
        "count": len(upcoming),
        "upcoming": upcoming,
    }


# --------- CLI local (opcional, pra teste no terminal) ---------


def main():
    ap = argparse.ArgumentParser(
        description="Buscar próximos jogos de um time no SofaScore (sem Selenium)"
    )
    ap.add_argument("--team", help="Nome do time (ex: 'Benfica Futsal')")
    ap.add_argument("--team-id", type=int, help="ID do time no SofaScore")
    ap.add_argument("--team-url", help="URL do time no SofaScore")
    ap.add_argument(
        "--next", type=int, default=3, help="Quantos próximos jogos listar (default=3)"
    )
    ap.add_argument(
        "--tz",
        default="America/Fortaleza",
        help="Timezone para datas locais (default=America/Fortaleza)",
    )
    ap.add_argument("--debug", action="store_true", help="Log extra (não usado aqui)")
    args = ap.parse_args()

    result = run_next(
        args.team,
        args.next,
        tz=args.tz,
        team_id=args.team_id,
        team_url=args.team_url,
        debug=args.debug,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
