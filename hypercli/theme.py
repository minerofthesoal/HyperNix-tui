"""OpenClaw-style red/black theme for hypercli."""

# Core palette — pure black with red accents, exactly OpenClaw-flavored.
BLACK = "#000000"
DARK_BLACK = "#050505"
PANEL_BLACK = "#0a0a0a"
BORDER_BLACK = "#1a0508"

RED_BRIGHT = "#ff2244"
RED = "#cc0033"
RED_DEEP = "#880022"
RED_MUTED = "#551119"
RED_GLOW = "#ff4466"

WHITE = "#f5f5f5"
GRAY = "#999999"
GRAY_DARK = "#444444"

# Semantic
ERROR = "#ff0033"
SUCCESS = "#66ddaa"
WARNING = "#ffaa33"
INFO = "#ff6688"

# Theme tokens used by Textual
HYPER_THEME = {
    "background": BLACK,
    "surface": PANEL_BLACK,
    "panel": PANEL_BLACK,
    "primary": RED,
    "secondary": RED_DEEP,
    "accent": RED_BRIGHT,
    "foreground": WHITE,
    "muted": GRAY,
    "border": RED_DEEP,
    "error": ERROR,
    "success": SUCCESS,
    "warning": WARNING,
}

BANNER = r"""
   _  _                 _   _  _        _
  | || |__ _ _ _ __ _  | | | || |_ _ __| |___
  | __ / _` | '_/ _` | | |_| || | '_/ __/ _ \_
  |_||_\__,_|_| \__,_|  \___/|_|_| \___\___/(_)
                              v0.70.3  //  hyperNix-tui
"""

def colored_banner() -> str:
    """Return the ANSI-colored banner."""
    from rich.text import Text
    text = Text(BANNER, style=f"bold {RED_BRIGHT} on {BLACK}")
    return text
