def fmt_currency(value: float) -> str:
    if value is None or (isinstance(value, float) and value != value):
        return "R$ -"
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_pct(value: float) -> str:
    if value is None:
        return "-"
    return f"{value * 100:.1f}%"


def fmt_number(value) -> str:
    if value is None:
        return "-"
    return f"{int(value):,}".replace(",", ".")
