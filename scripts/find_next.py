
#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, sys
BASE = os.path.dirname(os.path.dirname(__file__))
SRC = os.path.join(BASE, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from mvf.runner_next import main

if __name__ == "__main__":
    sys.exit(main())
