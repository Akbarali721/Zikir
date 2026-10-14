"""Mahalliy bot (polling). Asosiy kirish: python -m app.bot.worker"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.bot.worker import main

if __name__ == "__main__":
    main()
