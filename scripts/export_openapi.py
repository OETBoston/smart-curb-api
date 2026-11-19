"""Write the app's OpenAPI spec to docs/openapi.json (no database needed)."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from main import app

out = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "docs" / "openapi.json"
out.write_text(json.dumps(app.openapi(), indent=2) + "\n")
print(f"Wrote {out}")
