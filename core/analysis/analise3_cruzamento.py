"""
Análise 3 — Cruzamento: Closed Won × Bases BI

Para cada oportunidade Closed Won (Base 3):
  - Está na Base 1 (Carteira Ativa)?   → "Na Carteira Ativa"
  - Está na Base 2 (Para Ativar)?      → "Para Ativar"
  - Não está em nenhuma?               → ⚠️ LIMBO (alerta crítico)

Chave de cruzamento: User ID (quando disponível) + Account Name (fallback).
"""
import pandas as pd
from core.analysis.helpers import classificar_nivel, build_lookup_set, lookup_status
from utils.constants import NIVEIS_ORDER


def run(
    df_crm_won: pd.DataFrame,
    df_carteira: pd.DataFrame,
    df_ativar:   pd.DataFrame,
) -> dict:

    # Conjuntos de chaves das bases BI
    set_carteira = build_lookup_set(df_carteira, "User ID", "Account Name")
    set_ativar   = build_lookup_set(df_ativar,   "User ID", "Account Name")

    if df_crm_won.empty:
        return {
            "df_won_classificado": pd.DataFrame(),
            "limbo_accounts":      pd.DataFrame(),
            "total_limbo_amount":  0.0,
            "total_limbo_count":   0,
            "pivot_count":         pd.DataFrame(),
            "pivot_amount":        pd.DataFrame(),
        }

    # Classifica cada Closed Won
    won = df_crm_won.copy()
    won["Status"] = won.apply(
        lambda r: lookup_status(r, set_carteira, set_ativar), axis=1
    )
    won["Nível"] = won["Amount"].apply(classificar_nivel)

    # ── Pivot: contagem e volume por (Nível × Status) ───────────────────────
    status_cols = ["Na Carteira Ativa", "Para Ativar", "Limbo"]
    all_niveis  = NIVEIS_ORDER

    pivot_count  = _make_pivot(won, "Amount", "count",  all_niveis, status_cols)
    pivot_amount = _make_pivot(won, "Amount", "sum",    all_niveis, status_cols)

    # ── Detalhes do Limbo ───────────────────────────────────────────────────
    limbo_df = won[won["Status"] == "Limbo"].copy()
    limbo_accounts = _build_limbo_detail(limbo_df)

    total_limbo_amount = limbo_df["Amount"].sum()
    total_limbo_count  = len(limbo_df)

    return {
        "df_won_classificado": won,
        "limbo_accounts":      limbo_accounts,
        "total_limbo_amount":  total_limbo_amount,
        "total_limbo_count":   total_limbo_count,
        "pivot_count":         pivot_count.reset_index(),
        "pivot_amount":        pivot_amount.reset_index(),
    }


# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_pivot(
    df: pd.DataFrame,
    value_col: str,
    aggfunc: str,
    niveis: list,
    status_cols: list,
) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(0, index=niveis, columns=status_cols)

    pivot = df.pivot_table(
        index="Nível",
        columns="Status",
        values=value_col,
        aggfunc=aggfunc,
        fill_value=0,
    )
    return pivot.reindex(index=niveis, columns=status_cols, fill_value=0)


def _build_limbo_detail(limbo_df: pd.DataFrame) -> pd.DataFrame:
    """Retorna tabela detalhada das contas em Limbo."""
    if limbo_df.empty:
        return pd.DataFrame(columns=["Nível", "Account Name", "Opportunity Name", "Amount (R$)"])

    cols_base = ["Nível", "Account Name", "Amount"]
    if "Opportunity Name" in limbo_df.columns:
        cols_base = ["Nível", "Account Name", "Opportunity Name", "Amount"]

    detail = limbo_df[cols_base].copy().sort_values(["Nível", "Amount"], ascending=[True, False])
    detail = detail.rename(columns={"Amount": "Amount (R$)"})
    return detail.reset_index(drop=True)
