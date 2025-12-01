
from __future__ import annotations
from datetime import datetime, timezone
try:
    from zoneinfo import ZoneInfo
except Exception:
    ZoneInfo = None
import pytz

def now_utc() -> datetime:
    return datetime.now(timezone.utc)

def to_local(dt_utc: datetime, tz: str = "America/Fortaleza") -> datetime:
    if ZoneInfo is not None:
        try:
            return dt_utc.astimezone(ZoneInfo(tz))
        except Exception:
            pass
    return dt_utc.astimezone(pytz.timezone(tz))
