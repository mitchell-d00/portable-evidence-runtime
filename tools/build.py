#!/usr/bin/env python3
"""Standard-library-only deterministic builder for the offline, single-file UI."""
from pathlib import Path
import hashlib
import sys
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
TEMPLATE = (SRC / "index.template.html").read_text(encoding="utf-8")
parts = {
    "@@CSS@@": (SRC / "style.css").read_text(encoding="utf-8"),
    "@@ENGINE@@": (SRC / "engine.js").read_text(encoding="utf-8"),
    "@@APP@@": (SRC / "app.js").read_text(encoding="utf-8"),
}
result = TEMPLATE
for marker, content in parts.items():
    if result.count(marker) != 1:
        raise SystemExit(f"expected exactly one {marker}")
    if "</script" in content.lower() and marker != "@@CSS@@":
        raise SystemExit(f"unsafe script delimiter in {marker}")
    result = result.replace(marker, content)
p = ROOT / "index.html"
if "--check" in sys.argv:
    if not p.exists() or p.read_text(encoding="utf-8") != result:
        raise SystemExit("index.html is stale; run python3 tools/build.py")
    print("PASS: offline index.html matches source components")
else:
    p.write_text(result, encoding="utf-8")
    print("built index.html", len(result.encode("utf-8")), "bytes", hashlib.sha256(result.encode()).hexdigest())
