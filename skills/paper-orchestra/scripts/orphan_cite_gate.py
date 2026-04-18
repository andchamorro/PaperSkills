#!/usr/bin/env python3
"""
DEPRECATED — use citation_tool.py orphan-check instead.

    python scripts/citation_tool.py orphan-check desk/drafts/manuscript.md desk/refs.bib

This file is kept for backwards compatibility only. It forwards to citation_tool.py.
"""

import os
import sys

print(
    "WARNING: orphan_cite_gate.py is deprecated. Use: citation_tool.py orphan-check",
    file=sys.stderr,
)
# Forward to citation_tool.py orphan-check with the same arguments
script_dir = os.path.dirname(os.path.abspath(__file__))
os.execvp(
    sys.executable,
    [sys.executable, os.path.join(script_dir, "citation_tool.py"), "orphan-check"] + sys.argv[1:],
)
