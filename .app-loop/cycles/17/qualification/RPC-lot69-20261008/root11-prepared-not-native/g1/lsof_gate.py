"""Barrière diagnostique courte : release du parent après admission de birth."""
from __future__ import annotations

import os
import select
import sys


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in ("17593", "5173", "17594"):
        return 2
    ready, _, _ = select.select([sys.stdin.buffer], [], [], 5)
    if not ready or os.read(sys.stdin.fileno(), 16) != b"GO":
        return 3  # aucun lsof si parent absent ou release différente.
    port = sys.argv[1]
    argv = ["/usr/sbin/lsof", "-nP", "-iTCP:" + port, "-sTCP:LISTEN", "-F", "p"]
    os.execve(argv[0], argv, {"PATH": "/usr/bin:/bin:/usr/sbin:/sbin", "LANG": "C", "LC_ALL": "C"})
    return 4


if __name__ == "__main__":
    raise SystemExit(main())
