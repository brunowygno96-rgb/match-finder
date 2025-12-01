
from __future__ import annotations
import json, time, re
from datetime import datetime, timezone
from typing import List, Dict, Any
import undetected_chromedriver as uc
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

def _new_driver(headless: bool = True):
    opts = ChromeOptions()
    if headless:
        opts.add_argument("--headless=new")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument(f"--user-agent={UA}")
    opts.add_argument("--lang=pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7")
    try:
        return uc.Chrome(options=opts)
    except Exception as e:
        m = re.search(r"Current browser version is\\s+(\\d+)\\.", str(e))
        if not m:
            raise
        major = int(m.group(1))
        return uc.Chrome(options=opts, version_main=major)

def _open_json(url: str, headless: bool = True, wait: float = 5.0) -> Dict[str, Any]:
    driver = _new_driver(headless=headless)
    try:
        driver.get(url)
        time.sleep(wait)
        try:
            pre = driver.find_element(By.TAG_NAME, "pre")
            text = pre.text.strip()
        except Exception:
            text = driver.page_source
            text = re.sub(r"<[^>]+>", "", text).strip()
        if not text.startswith("{"):
            m = re.search(r"\\{.*\\}", text, flags=re.DOTALL)
            if m:
                text = m.group(0)
        return json.loads(text)
    finally:
        try:
            driver.quit()
        except Exception:
            pass
        del driver

def fetch_next_events(team_id: int) -> List[Dict[str, Any]]:
    """Busca os próximos eventos do time via API do SofaScore (com Selenium para driblar bloqueios)."""
    url = f"https://api.sofascore.com/api/v1/team/{team_id}/events/next/0"
    data = _open_json(url)
    out = []
    for ev in data.get("events", []) or []:
        ts = ev.get("startTimestamp")
        if not ts:
            continue
        out.append({
            "ts": int(ts),
            "date_utc": datetime.fromtimestamp(int(ts), tz=timezone.utc),
            "home": ev.get("homeTeam", {}).get("name", ""),
            "away": ev.get("awayTeam", {}).get("name", ""),
            "tournament": ev.get("tournament", {}).get("name", ""),
            "sofascore_event_id": ev.get("id")
        })
    out.sort(key=lambda e: e["ts"])
    return out
