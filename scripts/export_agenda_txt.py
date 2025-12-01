
#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, sys
BASE = os.path.dirname(os.path.dirname(__file__))
SRC = os.path.join(BASE, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from mvf.multi import run_multi
from datetime import datetime, timedelta

def _plus4_time_str(date_ymd: str, hhmm: str) -> str:
    try:
        dt = datetime.strptime(f"{date_ymd} {hhmm}", "%Y-%m-%d %H:%M")
        dt2 = dt + timedelta(hours=4)
        return dt2.strftime("%H:%M")
    except Exception:
        return ""

def main():
    data = run_multi(next_per_team=2, tz="America/Fortaleza")
    lines = []
    for day in data.get("days", []):
        ymd = day.get("date","")
        try:
            br = datetime.strptime(ymd, "%Y-%m-%d").strftime("%d/%m/%Y")
        except Exception:
            br = ymd
        lines.append(f"dia {br}:")
        for item in day.get("items", []):
            try:
                dbr = datetime.strptime(item.get("date_local",""), "%Y-%m-%d").strftime("%d/%m/%Y")
            except Exception:
                dbr = item.get("date_local","")
            lines.append(f"{item.get('athlete','')} / {item.get('vs','')} / {item.get('tournament','')} / {item.get('time_local','')} / {_plus4_time_str(item.get('date_local',''), item.get('time_local',''))} {dbr}")
        lines.append("")
    out = os.path.join(BASE, "agenda.txt")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).strip()+"\n")
    print(f"Exportado para: {out}")

if __name__ == "__main__":
    sys.exit(main())
