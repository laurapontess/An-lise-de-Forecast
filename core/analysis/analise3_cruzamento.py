import pandas as pd
from core.analysis.helpers import classificar_nivel, is_won
from utils.constants import NIVEIS


def _normalize_name(name) -> str:
    return str(name).strip().lower()


def run(df_crm: pd.DataFrame, df_carteira: pd.DataFrame, df_ativar: pd.DataFrame) -> dict:
    accounts_carteira = set(df_carteira["Account Name"].apply(_normalize_name))
    accounts_ativar = set(df_ativar["Account Name"].apply(_normalize_name))

    won = df_crm[df_crm["Stage"].apply(is_won)].copy()

    if won.empty:
        empty = pd.DataFrame(columns=["Nível", "Vendendo na carteira", "Para ativar", "Limbo"])
        return {
            "pivot_matrix": empty,
            "df_won_classificado": won,
            "limbo_detail": pd.DataFrame(),
            "total_limbo_amount": 0.0,
        }

    def classify_status(row):
        acct = _normalize_name(row["Account Name"])
        if acct in accounts_carteira:
            return "Vendendo na carteira"
        elif acct in accounts_ativar:
            return "Para ativar"
        else:
            return "Limbo"

    won["Status Carteira"] = won.apply(classify_status, axis=1)
    won["Nível"] = won["Amount"].apply(classificar_nivel)

    niveis_order = list(NIVEIS.keys())
    status_cols = ["Vendendo na carteira", "Para ativar", "Limbo"]

    pivot_count = won.pivot_table(
        index="Nível",
        columns="Status Carteira",
        values="Amount",
        aggfunc="count",
        fill_value=0,
    ).reindex(index=niveis_order, columns=status_cols, fill_value=0)

    pivot_amount = won.pivot_table(
        index="Nível",
        columns="Status Carteira",
        values="Amount",
        aggfunc="sum",
        fill_value=0,
    ).reindex(index=niveis_order, columns=status_cols, fill_value=0)

    limbo_detail = (
        won[won["Status Carteira"] == "Limbo"]
        .groupby("Nível")
        .agg(qtd=("Account Name", "count"), amount_total=("Amount", "sum"))
        .reindex(niveis_order)
        .fillna(0)
        .reset_index()
    )

    total_limbo_amount = won[won["Status Carteira"] == "Limbo"]["Amount"].sum()

    return {
        "pivot_count": pivot_count,
        "pivot_amount": pivot_amount,
        "df_won_classificado": won,
        "limbo_detail": limbo_detail,
        "total_limbo_amount": total_limbo_amount,
    }
