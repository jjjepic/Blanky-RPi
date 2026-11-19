"""Shared fixed-width event columns for the QML header and rows."""

COLUMN_WIDTHS = (5, 8, 10, 18, 9)
DESCRIPTION_WIDTH = 44


def event_header(lang: str) -> str:
    labels = ("ID", "Hora", "Origem", "Comando", "Estado", "Descrição") if lang == "pt" else (
        "ID", "Time", "Source", "Command", "State", "Description"
    )
    return " | ".join(label.ljust(width) for label, width in zip(labels, COLUMN_WIDTHS)) + " | " + labels[-1]


def event_divider() -> str:
    return " | ".join("-" * width for width in COLUMN_WIDTHS) + " | " + "-" * DESCRIPTION_WIDTH


def event_prefix(event_id: str, event_time: str, source: str, command: str, status: str) -> str:
    values = (event_id, event_time, source, command, status)
    return " | ".join(value.ljust(width) for value, width in zip(values, COLUMN_WIDTHS)) + " | "
