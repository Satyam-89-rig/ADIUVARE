from textual.widgets import Static


class EventDetail(Static):
    def show_event(self, event: dict | None) -> None:
        if not event:
            self.update("select a row to inspect")
            return

        breakdown = event.get("breakdown") or {}
        detail = event.get("detail") or {}
        lines = [
            "event detail",
            f"identity: {event.get('identity', '?')}",
            f"endpoint: {event.get('endpoint', '?')}",
            f"verdict: {event.get('verdict', 'allow')}",
            "",
            "signal detail",
        ]
        if isinstance(breakdown, dict) and breakdown:
            for name, score in sorted(breakdown.items(), key=lambda item: item[1], reverse=True):
                lines.append(f"- {name}: {float(score):0.2f}")
        else:
            lines.append("- none")

        ai = detail.get("ai") if isinstance(detail, dict) else None
        if isinstance(ai, dict) and ai:
            lines.append("")
            lines.append("ai detail")
            lines.append(f"ai verdict: {ai.get('verdict', 'n/a')}")
        note = detail.get("note") if isinstance(detail, dict) else None
        if note:
            lines.append("")
            lines.append(f"note: {note}")
        self.update("\n".join(lines))
