from typing import TYPE_CHECKING, cast

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import DataTable, Static

from ...signals.context import ContextSignal
from ...signals.ip_rep import IPRepSignal
from ..workspace import (
    FOOTER_READY,
    PALETTE,
    SHORTCUT_AUTO_REFRESH,
    SHORTCUT_NAVIGATE,
    WorkspaceView,
    format_shortcut,
    join_shortcuts,
    render_signal_bar,
    sensitivity_color,
)

if TYPE_CHECKING:
    from ..app import AdiuvareApp


SIGNAL_ORDER = ("payload", "behavior", "identity", "context", "ip_rep")
FIXED_SIGNAL_WEIGHTS = {
    "context": ContextSignal.weight,
    "ip_rep": IPRepSignal.weight,
}

SIGNAL_DESCRIPTIONS = {
    "payload": "Detects SQLi, XSS, path traversal via libinjection grammar and re2 patterns. Three-step: normalize -> libinjection -> re2. Deterministic overrides for boolean tautologies and EXEC patterns.",
    "behavior": "Tracks request frequency, burst patterns, and anomalous timing. Uses sliding windows with exponential decay.",
    "identity": "Evaluates identity reputation based on historical behavior, IP geo, and account age.",
    "context": "Built-in contextual heuristic for route sensitivity, unusual methods, oversized payloads, and hot paths like /admin or /auth. Fixed scorer weight today.",
    "ip_rep": "Built-in IP risk heuristic using local/private checks, TOR exit hints, and known noisy network prefixes. Fixed scorer weight today.",
}


class SignalsScreen(WorkspaceView):
    shortcut_hints = join_shortcuts(
        SHORTCUT_NAVIGATE,
        format_shortcut("Enter", "select"),
        SHORTCUT_AUTO_REFRESH,
    )
    primary_id = "signals-table"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._selected_signal = "payload"

    def compose(self) -> ComposeResult:
        with Horizontal(id="signals-outer"):
            with Vertical(id="signals-col-left"):
                yield DataTable(id="signals-table")
                yield Static("", id="signals-detail")
            with Vertical(id="signals-col-right"):
                yield DataTable(id="signals-routes-table")
                yield Static("", id="signals-pressure")
                yield Static("", id="signals-top-contrib")

    def on_mount(self) -> None:
        table = self.query_one("#signals-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("SIGNAL", "TYPE", "WEIGHT", "STATUS", "HITS")

        routes = self.query_one("#signals-routes-table", DataTable)
        routes.cursor_type = "row"
        routes.add_columns("ROUTE", "STATUS", "SENSITIVITY", "POLICY", "AI MODE")

        self.refresh_view()

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        if event.data_table.id == "signals-table" and 0 <= event.cursor_row < len(SIGNAL_ORDER):
            self._selected_signal = SIGNAL_ORDER[event.cursor_row]
            self._render_detail()

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        if event.data_table.id == "signals-table" and 0 <= event.cursor_row < len(SIGNAL_ORDER):
            self._selected_signal = SIGNAL_ORDER[event.cursor_row]
            self._render_detail()

    def refresh_view(self) -> None:
        rows = self._app().recent_rows(145)
        weights = {
            "payload": float(self._app().config.weights.payload),
            "behavior": float(self._app().config.weights.behavior),
            "identity": float(self._app().config.weights.identity),
            "context": FIXED_SIGNAL_WEIGHTS["context"],
            "ip_rep": FIXED_SIGNAL_WEIGHTS["ip_rep"],
        }
        hits: dict[str, int] = {}
        for row in rows:
            for name, score in (row.get("breakdown") or {}).items():
                if float(score) > 0.05:
                    hits[str(name)] = hits.get(str(name), 0) + 1

        table = self.query_one("#signals-table", DataTable)
        table.clear(columns=False)
        for name in SIGNAL_ORDER:
            weight = weights.get(name, 0.0)
            active = weight > 0.0 or hits.get(name, 0) > 0
            hit_count = hits.get(name, 0)
            status_color = PALETTE["green"] if active else PALETTE["very_dim"]
            hit_color = PALETTE["cyan"] if active else PALETTE["very_dim"]
            table.add_row(
                Text(name, style=PALETTE["text"]),
                Text("built-in", style=PALETTE["dim"]),
                Text(f"{weight:.3f}", style=PALETTE["cyan"]),
                Text("ACTIVE" if active else "DISABLED", style=status_color),
                Text(str(hit_count), style=hit_color),
            )

        routes = self.query_one("#signals-routes-table", DataTable)
        routes.clear(columns=False)
        route_rows = self._app().route_overview()
        for route in route_rows:
            status = route["status"]
            if status == "exempt":
                status_text = Text(status, style=PALETTE["very_dim"])
            else:
                status_text = Text(status, style=PALETTE["green"])

            sensitivity = route["sensitivity"]
            ai_mode = route["ai_mode"]
            ai_color = PALETTE["red"] if ai_mode == "critical" else PALETTE["orange"] if ai_mode == "assist" else PALETTE["very_dim"]
            routes.add_row(
                Text(route["route"], style=PALETTE["dim"]),
                status_text,
                Text(sensitivity, style=sensitivity_color(sensitivity)),
                Text(route["policy"], style=PALETTE["cyan"]),
                Text(ai_mode, style=ai_color),
            )
        if not route_rows:
            routes.add_row(
                Text("no live route metadata", style=PALETTE["very_dim"]),
                Text("-", style=PALETTE["very_dim"]),
                Text("-", style=PALETTE["very_dim"]),
                Text("-", style=PALETTE["very_dim"]),
                Text("-", style=PALETTE["very_dim"]),
            )

        self._render_detail()
        self._render_pressure(rows)
        self._render_top_contrib(rows)

    def footer_status(self) -> str:
        return FOOTER_READY

    def _render_detail(self) -> None:
        name = self._selected_signal
        weights = {
            "payload": float(self._app().config.weights.payload),
            "behavior": float(self._app().config.weights.behavior),
            "identity": float(self._app().config.weights.identity),
            "context": FIXED_SIGNAL_WEIGHTS["context"],
            "ip_rep": FIXED_SIGNAL_WEIGHTS["ip_rep"],
        }
        description = SIGNAL_DESCRIPTIONS.get(name, "No description available.")

        rows = self._app().recent_rows(145)
        hits = sum(1 for row in rows if float((row.get("breakdown") or {}).get(name, 0)) > 0.05)
        contribution = sum(float((row.get("breakdown") or {}).get(name, 0)) for row in rows)
        weight = weights.get(name, 0.0)
        active = weight > 0.0 or hits > 0
        fixed = name in FIXED_SIGNAL_WEIGHTS
        weight_text = f"{weight:.3f} (fixed)" if fixed else f"{weight:.3f}"

        lines = [
            f"[{PALETTE['dim']} bold]SIGNAL DETAIL[/]",
            "",
            f"[{PALETTE['cyan']} bold]{name}[/]",
            "",
            f"[{PALETTE['dim']}]Type          [/] [{PALETTE['text']}]{'built-in fixed' if fixed else 'built-in'}[/]",
            f"[{PALETTE['dim']}]Weight        [/] [{PALETTE['cyan']}]{weight_text}[/]",
            f"[{PALETTE['dim']}]Status        [/] [{PALETTE['green'] if active else PALETTE['very_dim']}]{'ACTIVE' if active else 'DISABLED'}[/]",
            f"[{PALETTE['dim']}]Recent hits   [/] [{PALETTE['cyan']}]{hits}[/]",
            f"[{PALETTE['dim']}]Contribution  [/] [{PALETTE['cyan']}]{contribution:.1f}[/]",
            "",
            f"[{PALETTE['border_panel']}]{'-' * 44}[/]",
            f"[{PALETTE['very_dim']}]DESCRIPTION[/]",
            "",
            f"[{PALETTE['dim']}]{description}[/]",
        ]
        self.query_one("#signals-detail", Static).update("\n".join(lines))

    def _render_pressure(self, rows: list[dict]) -> None:
        totals: dict[str, float] = {}
        for row in rows:
            for name, value in (row.get("breakdown") or {}).items():
                totals[str(name)] = totals.get(str(name), 0.0) + float(value)

        peak = max(totals.values()) if totals else 1.0
        lines = [f"[{PALETTE['dim']} bold]AGGREGATE SIGNAL PRESSURE[/]", ""]
        for name in ("payload", "behavior", "identity", "context"):
            value = totals.get(name, 0.0)
            bar = render_signal_bar(value, peak, 20)
            lines.append(f"  [{PALETTE['cyan']}]{name:<10}[/] {bar} [{PALETTE['text']}]{value:>6.1f}[/]")
        self.query_one("#signals-pressure", Static).update("\n".join(lines))

    def _render_top_contrib(self, rows: list[dict]) -> None:
        totals: dict[str, float] = {}
        for row in rows:
            for name, value in (row.get("breakdown") or {}).items():
                totals[str(name)] = totals.get(str(name), 0.0) + float(value)

        ordered = sorted(totals.items(), key=lambda item: item[1], reverse=True)
        total = sum(value for _, value in ordered) or 1.0
        lines = [f"[{PALETTE['dim']} bold]TOP SIGNALS BY CONTRIBUTION[/]", ""]
        for name, value in ordered:
            pct = (value / total) * 100
            lines.append(
                f"  [{PALETTE['text']}]{name:<12}[/] [{PALETTE['cyan']}]{value:>6.1f}[/] [{PALETTE['dim']}]{pct:>5.1f}%[/]"
            )
        self.query_one("#signals-top-contrib", Static).update("\n".join(lines))

    def _app(self):
        return cast("AdiuvareApp", self.app)
