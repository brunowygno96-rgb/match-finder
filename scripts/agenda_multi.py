
#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, sys, json
BASE = os.path.dirname(os.path.dirname(__file__))
SRC = os.path.join(BASE, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from mvf.multi import run_multi

def main():
    data = run_multi(next_per_team=2, tz="America/Fortaleza")
    print(json.dumps(data, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    sys.exit(main())
