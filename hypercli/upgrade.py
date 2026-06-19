"""Self-upgrade — pip install --upgrade hypercli, restart required."""

from __future__ import annotations

import subprocess
import sys
from typing import Optional, Tuple

from . import __version__


def current_version() -> str:
    return __version__


def latest_pypi_version(package: str = "hypercli") -> Optional[str]:
    try:
        import httpx
        r = httpx.get(f"https://pypi.org/pypi/{package}/json", timeout=10)
        r.raise_for_status()
        return r.json()["info"]["version"]
    except Exception:
        return None


def upgrade_self() -> Tuple[bool, str]:
    """Run `pip install --upgrade hypercli` in the current interpreter."""
    cmd = [sys.executable, "-m", "pip", "install", "--upgrade",
           "--user", "hypercli"]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        ok = proc.returncode == 0
        msg = (proc.stdout or "") + (proc.stderr or "")
        return ok, msg
    except Exception as e:
        return False, str(e)


def needs_upgrade() -> Tuple[bool, Optional[str]]:
    latest = latest_pypi_version()
    if not latest:
        return False, None
    try:
        from packaging.version import Version
        return Version(latest) > Version(__version__), latest
    except Exception:
        return (latest != __version__), latest
