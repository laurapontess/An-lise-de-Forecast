import pandas as pd
from utils.constants import NIVEIS, NIVEIS_ORDER


def classificar_nivel(amount: float) -> str:
    """Classifica conta pelo faturamento/GMV/Amount nos níveis N2‒N7."""
    try:
        v = float(amount)
    except (TypeError, ValueError):
        return "< N2"
    if v < 0:
        return "< N2"
    for nivel in reversed(NIVEIS_ORDER):
        low, high = NIVEIS[nivel]
        if low <= v <= high:
            return nivel
    return "< N2"


def normalize_key(val) -> str:
    """Normaliza string para comparação: minúsculo, sem espaços extras."""
    return str(val).strip().lower()


def build_lookup_set(df: pd.DataFrame, id_col: str, name_col: str) -> set:
    """
    Constrói conjunto de chaves para cruzamento.
    Tenta usar id_col primeiro; usa name_col como fallback.
    """
    keys = set()
    for _, row in df.iterrows():
        uid = str(row.get(id_col, "")).strip()
        name = normalize_key(row.get(name_col, ""))
        if uid and uid not in ("", "nan"):
            keys.add(uid.lower())
        if name:
            keys.add(name)
    return keys


def lookup_status(row: pd.Series, set_carteira: set, set_ativar: set) -> str:
    """
    Verifica em qual base o registro Closed Won está.
    Prioridade: User ID → Account Name.
    """
    uid = str(row.get("User ID", "")).strip().lower()
    name = normalize_key(row.get("Account Name", ""))

    in_carteira = (uid and uid != "nan" and uid in set_carteira) or (name in set_carteira)
    in_ativar   = (uid and uid != "nan" and uid in set_ativar)   or (name in set_ativar)

    if in_carteira:
        return "Na Carteira Ativa"
    if in_ativar:
        return "Para Ativar"
    return "Limbo"
