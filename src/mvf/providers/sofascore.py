
from __future__ import annotations
import re, requests
from typing import Optional, Dict, Any

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
BASE_HEADERS = {
    "User-Agent": UA,
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    "Origin": "https://www.sofascore.com",
    "Referer": "https://www.sofascore.com/",
}
_session = None

def _ensure_session():
    global _session
    if _session is None:
        s = requests.Session()
        s.headers.update(BASE_HEADERS)
        try:
            s.get("https://www.sofascore.com", timeout=15)
        except Exception:
            pass
        _session = s
    return _session

def _get(path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    sess = _ensure_session()
    base = "https://api.sofascore.com/api/v1"
    url = f"{base}{path}" if not path.startswith("http") else path
    r = sess.get(url, params=params, timeout=20)
    r.raise_for_status()
    return r.json()

TEAM_URL_RX = re.compile(r"/team/[^/]+/(?P<id>\\d+)(?:$|/)")
def team_id_from_url(url: str) -> Optional[int]:
    m = TEAM_URL_RX.search(url or "")
    if not m:
        return None
    try:
        return int(m.group("id"))
    except Exception:
        return None

def search_team_id(team_query: str) -> Optional[int]:
    try:
        data = _get("/search/all", params={"q": team_query})
        teams = data.get("teams", [])
        if teams:
            q = (team_query or "").lower().strip()
            def score(t):
                name = (t.get("name") or "").lower()
                if q == name: return 100
                if q in name or name in q: return 80
                return len(set(q.split()) & set(name.split()))
            best = max(teams, key=score)
            return best.get("id")
    except Exception:
        pass
    return None
