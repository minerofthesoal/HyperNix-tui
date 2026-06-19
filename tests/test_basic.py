"""Smoke tests for hypercli."""

import hypercli
from hypercli import __version__
from hypercli.config import Config
from hypercli.providers import list_providers
from hypercli.tools import default_registry


def test_version():
    assert __version__ == "0.70.3"


def test_providers_listed():
    provs = list_providers()
    for p in ["hypernix", "openai", "anthropic", "ollama", "lmstudio", "rest"]:
        assert p in provs


def test_config_loads():
    cfg = Config.load()
    assert "hypernix" in cfg.providers


def test_default_registry():
    reg = default_registry()
    for name in ["read_file", "write_file", "list_dir", "web_search", "create_skill"]:
        assert name in reg.names()


def test_main_help(monkeypatch, capsys):
    import sys
    with monkeypatch.context() as m:
        m.setattr(sys, "argv", ["hypercli", "--version"])
        try:
            hypercli.main()
        except SystemExit:
            pass
        out = capsys.readouterr()
        assert "0.70.3" in out.out + out.err
