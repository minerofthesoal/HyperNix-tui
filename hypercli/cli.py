"""CLI entrypoint — `hypercli` command."""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from typing import Optional, Sequence

from . import __version__
from .config import Config
from .providers import build_provider, list_providers
from .upgrade import needs_upgrade, upgrade_self


BANNER = r"""
   _  _                 _   _  _        _
  | || |__ _ _ _ __ _  | | | || |_ _ __| |___
  | __ / _` | '_/ _` | | |_| || | '_/ __/ _ \_
  |_||_\__,_|_| \__,_|  \___/|_|_| \___\___/(_)
                              v%s  //  hyperNix-tui
""" % __version__


def _print_banner() -> None:
    try:
        from rich.console import Console
        from rich.text import Text
        c = Console()
        c.print(Text(BANNER, style="bold #ff2244 on #000000"))
    except Exception:
        print(BANNER)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="hypercli",
        description="OpenClaw-style red/black TUI for the hyperNix toolkit.",
        epilog="Run `hypercli` with no args to launch the TUI.",
    )
    p.add_argument("--version", action="version", version=f"hypercli {__version__}")
    p.add_argument("-p", "--provider", choices=list_providers(),
                   help="provider to use (default: hypernix)")
    p.add_argument("-m", "--model", help="model name to use")
    p.add_argument("--no-tui", action="store_true",
                   help="run in plain REPL mode (no TUI)")
    p.add_argument("--prompt", "-P", help="run a single prompt and exit (no TUI)")
    p.add_argument("--upgrade", action="store_true",
                   help="upgrade hypercli from PyPI and exit")
    p.add_argument("--no-upgrade-check", action="store_true",
                   help="skip the auto-upgrade check")
    return p


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)

    if args.upgrade:
        ok, msg = upgrade_self()
        print("upgrade ok" if ok else "upgrade failed")
        print(msg)
        return 0 if ok else 1

    cfg = Config.load()
    if args.provider:
        cfg.active_provider = args.provider
    if args.model:
        cfg.active_model = args.model

    # Auto-upgrade check
    if cfg.auto_upgrade and not args.no_upgrade_check and sys.stdout.isatty():
        try:
            need, latest = needs_upgrade()
            if need and latest:
                print(f"[hypercli] newer version {latest} available. "
                      f"Run `hypercli --upgrade`.", file=sys.stderr)
        except Exception:
            pass

    if args.prompt:
        return asyncio.run(_run_once(cfg, args.prompt))

    if args.no_tui:
        return asyncio.run(_repl(cfg))

    # Full TUI
    try:
        from .tui import HyperApp
    except Exception as e:  # textual missing?
        print(f"[hypercli] TUI unavailable ({e}); falling back to REPL.", file=sys.stderr)
        return asyncio.run(_repl(cfg))

    app = HyperApp()
    # inject cfg/provider into the app
    app.config = cfg
    app.provider = build_provider(cfg)
    app.run()
    return 0


async def _run_once(cfg: Config, prompt: str) -> int:
    _print_banner()
    provider = build_provider(cfg)
    from .providers.base import Message
    msgs = [Message(role="user", content=prompt)]
    try:
        async for chunk in provider.stream(msgs, model=cfg.active_model):
            print(chunk, end="", flush=True)
        print()
    except Exception as e:
        print(f"[error] {e}", file=sys.stderr)
        return 1
    finally:
        await provider.aclose()
    return 0


async def _repl(cfg: Config) -> int:
    """Fallback REPL if textual isn't usable."""
    _print_banner()
    print(f"provider={cfg.active_provider} model={cfg.active_model}  (type :q to exit)\n")
    provider = build_provider(cfg)
    from .providers.base import Message
    from .tools import default_registry
    registry = default_registry()
    history: list[Message] = []
    SYSTEM = ("You are HyperNix. You can call tools. Be concise.")
    while True:
        try:
            line = input("❯ ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not line:
            continue
        if line in (":q", ":quit", ":exit"):
            break
        if line.startswith("/"):
            print("(slash commands only available in TUI mode)")
            continue
        history.append(Message(role="user", content=line))
        try:
            res = await provider.chat(
                [Message(role="system", content=SYSTEM)] + history,
                model=cfg.active_model, tools=registry.all(),
            )
            content = res.get("content", "")
            print(f"⚡ {content}\n")
            history.append(Message(role="assistant", content=content))
            # basic tool execution
            for call in (res.get("tool_calls") or []):
                fn = call.get("function") or call
                tname = fn.get("name", "")
                args = fn.get("arguments", {})
                if isinstance(args, str):
                    import json
                    args = json.loads(args or "{}")
                tr = await registry.call(tname, args)
                print(f"🛠 {tname} → {tr.output[:400] if tr.ok else tr.error}")
                history.append(Message(role="tool", content=tr.output if tr.ok else f"ERROR: {tr.error}",
                                       name=tname))
        except Exception as e:
            print(f"[error] {e}")
    await provider.aclose()
    return 0


if __name__ == "__main__":
    sys.exit(main())
