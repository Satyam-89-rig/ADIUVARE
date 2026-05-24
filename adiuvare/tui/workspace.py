from textual.containers import Container


PALETTE = {
    "bg_base": "#0d1117",
    "bg_panel": "#161b22",
    "bg_row_select": "#1c2432",
    "bg_input": "#0d1117",
    "bg_input_focus": "#0d1820",
    "bg_tab_active": "#1a2332",
    "border_panel": "#21262d",
    "border_input": "#30363d",
    "border_focus": "#58a6ff",
    "text": "#e6edf3",
    "dim": "#8b949e",
    "very_dim": "#6e7681",
    "cyan": "#58a6ff",
    "green": "#3fb950",
    "orange": "#e3b341",
    "red": "#f85149",
    "white": "#ffffff",
    "purple": "#a371f7",
    "bar_hot": "#f85149",
    "bar_med": "#e3b341",
    "bar_dim": "#3a3010",
    "bar_green": "#3fb950",
    "btn_confirm": "#1a5fa5",
    "btn_whitelist": "#1a7a36",
    "btn_monitor": "#7a5a10",
    "btn_export": "#5a2ea6",
    "btn_primary": "#0a4a6a",
    "btn_save": "#0a6a6a",
}

DECISION_ICONS = {
    "allow": "o",
    "flag": "^",
    "throttle": "!",
    "block": "x",
}

DECISION_COLORS = {
    "allow": PALETTE["green"],
    "flag": PALETTE["orange"],
    "throttle": PALETTE["orange"],
    "block": PALETTE["red"],
}

SIGNAL_COLORS = {
    "payload": PALETTE["red"],
    "behavior": PALETTE["orange"],
    "identity": PALETTE["orange"],
    "context": "#c47a35",
}

FOOTER_READY = "Keyboard shortcuts active"
FOOTER_SEPARATOR = "  "

SHORTCUT_TABS = "[1-7] tabs"
SHORTCUT_QUIT = "[q] quit"
SHORTCUT_NAVIGATE = "[up/down] navigate"
SHORTCUT_SCROLL = "[up/down] scroll"
SHORTCUT_AUTO_REFRESH = "[auto 3s]"


def format_shortcut(key: str, label: str) -> str:
    return f"[{key}] {label}"


def join_shortcuts(*parts: str) -> str:
    return FOOTER_SEPARATOR.join(part for part in parts if part)


def footer_selected(value: str) -> str:
    return f"Selected: {value}"


class WorkspaceView(Container):
    """Provide the shared focus and footer conventions for each TUI screen."""

    DEFAULT_CSS = """
    WorkspaceView {
        width: 1fr;
        height: 1fr;
    }
    """

    shortcut_hints = ""
    primary_id: str | None = None
    search_id: str | None = None

    def refresh_view(self) -> None:
        return

    def footer_status(self) -> str:
        return FOOTER_READY

    def shortcut_summary(self) -> str:
        parts = [SHORTCUT_TABS]
        if self.shortcut_hints:
            parts.append(self.shortcut_hints)
        hints = join_shortcuts(*parts)
        if "[q]" not in hints.lower():
            hints = join_shortcuts(hints, SHORTCUT_QUIT)
        return hints

    def focus_primary(self) -> None:
        if not self.primary_id:
            return
        try:
            self.app.set_focus(self.query_one(f"#{self.primary_id}"))
        except Exception:
            return

    def focus_search(self) -> None:
        if not self.search_id:
            return
        try:
            self.app.set_focus(self.query_one(f"#{self.search_id}"))
        except Exception:
            return


def decision_color(verdict: str) -> str:
    return DECISION_COLORS.get(verdict, PALETTE["dim"])


def decision_icon(verdict: str) -> str:
    return DECISION_ICONS.get(verdict, "?")


def risk_color(risk: str) -> str:
    return {
        "normal": PALETTE["green"],
        "suspicious": PALETTE["orange"],
        "elevated": PALETTE["orange"],
        "hostile": PALETTE["red"],
        "critical": PALETTE["red"],
    }.get(risk, PALETTE["dim"])


def dominant_color(dominant: str) -> str:
    return SIGNAL_COLORS.get(dominant, PALETTE["cyan"])


def status_color(status: str) -> str:
    return {
        "ACTIVE": PALETTE["green"],
        "active": PALETTE["green"],
        "DISABLED": PALETTE["very_dim"],
        "disabled": PALETTE["very_dim"],
        "exempt": PALETTE["very_dim"],
    }.get(status, PALETTE["dim"])


def sensitivity_color(sensitivity: str) -> str:
    return {
        "critical": PALETTE["red"],
        "internal": PALETTE["orange"],
        "public": PALETTE["green"],
    }.get(sensitivity, PALETTE["dim"])


def render_signal_bar(value: float, max_value: float, width: int = 22) -> str:
    if max_value <= 0:
        max_value = 1.0
    filled = max(0, min(width, int((value / max_value) * width)))
    hot = int(filled * 0.55)
    med = filled - hot
    dim = width - filled
    return (
        f"[{PALETTE['bar_hot']}]{'█' * hot}[/]"
        f"[{PALETTE['bar_med']}]{'▓' * med}[/]"
        f"[{PALETTE['bar_dim']}]{'░' * dim}[/]"
    )


def render_decision_bar(value: float, max_value: float, color: str, width: int = 18) -> str:
    if max_value <= 0:
        max_value = 1.0
    filled = max(0, min(width, int((value / max_value) * width)))
    dim = width - filled
    return f"[{color}]{'█' * filled}[/][#1a1a1a]{'░' * dim}[/]"


def render_score_bar(value: float, width: int = 14) -> str:
    filled = max(0, min(width, int(value * width)))
    empty = width - filled
    color = PALETTE["red"] if value > 0.6 else PALETTE["orange"] if value > 0.4 else PALETTE["green"]
    return f"[{color}]{'█' * filled}[/][{PALETTE['border_input']}]{'░' * empty}[/]"


def render_sub_weight_bar(value: float, max_value: float, color: str, width: int = 20) -> str:
    if max_value <= 0:
        max_value = 1.0
    filled = max(0, min(width, int((value / max_value) * width)))
    dim = width - filled
    dim_bg = "#0a2010" if color == PALETTE["green"] else "#302000" if color == PALETTE["orange"] else "#201000"
    return f"[{color}]{'█' * filled}[/][{dim_bg}]{'░' * dim}[/]"


def styled_label(label: str, value: str = "", color: str = "") -> str:
    text_color = color or PALETTE["text"]
    return f"[{PALETTE['dim']}]{label:<14}[/] [{text_color}]{value}[/]"


def styled_header(title: str) -> str:
    return f"[{PALETTE['dim']} bold]{title.upper()}[/]"


def styled_separator() -> str:
    return f"[{PALETTE['border_panel']}]{'-' * 44}[/]"


def score_bar(score: float, width: int = 10) -> str:
    return render_score_bar(score, width)
