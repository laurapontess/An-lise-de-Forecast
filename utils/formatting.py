def fmt_currency(value) -> str:
    """Formata valor em reais: R$ 1.234,56"""
    try:
        v = float(value)
    except (TypeError, ValueError):
        return "R$ –"
    if v != v:  # NaN
        return "R$ –"
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_pct(value) -> str:
    """Formata porcentagem: 45,3%"""
    try:
        v = float(value)
    except (TypeError, ValueError):
        return "–"
    if v != v:
        return "–"
    return f"{v * 100:.1f}%"


def fmt_number(value) -> str:
    """Formata inteiro com separador de milhar"""
    try:
        return f"{int(value):,}".replace(",", ".")
    except (TypeError, ValueError):
        return "–"


def fmt_short(value) -> str:
    """Versão curta para valores grandes: 1,2M / 850K"""
    try:
        v = float(value)
    except (TypeError, ValueError):
        return "–"
    if abs(v) >= 1_000_000:
        return f"R$ {v/1_000_000:.1f}M"
    if abs(v) >= 1_000:
        return f"R$ {v/1_000:.0f}K"
    return fmt_currency(v)
