"""hypercli - OpenClaw-style red/black TUI for the hyperNix AI toolkit."""

__version__ = "0.70.3"
__author__ = "minerofthesoal"
__repo__ = "https://github.com/minerofthesoal/HyperNix-tui"

from .cli import main  # noqa: F401

__all__ = ["main", "__version__"]
