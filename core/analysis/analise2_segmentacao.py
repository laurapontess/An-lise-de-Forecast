import pandas as pd
from core.analysis.helpers import classificar_nivel, is_won, is_lost, is_pipeline
from utils.constants import NIVEIS


def run(df_crm: pd.DataFrame) -> dict:
    df = df_crm.copy()
    df["Nível"] = df["Amount"].apply(classificar_nivel)

    niveis_order = list(NIVEIS.keys())
    rows = []

    for nivel in niveis_order:
        subset = df[df["Nível"] == nivel]
        if subset.empty:
            rows.append({
                "Nível": nivel, "Total Opps": 0, "Won": 0,
                "Pipeline Ativo": 0, "Lost": 0,
                "Amount Total (R$)": 0.0, "Amount Won (R$)": 0.0,
            })
            continue

        won_mask = subset["Stage"].apply(is_won)
        lost_mask = subset["Stage"].apply(is_lost)
        pipe_mask = subset["Stage"].apply(is_pipeline)

        rows.append({
            "Nível": nivel,
            "Total Opps": len(subset),
            "Won": int(won_mask.sum()),
            "Pipeline Ativo": int(pipe_mask.sum()),
            "Lost": int(lost_mask.sum()),
            "Amount Total (R$)": subset["Amount"].sum(),
            "Amount Won (R$)": subset.loc[won_mask, "Amount"].sum() if won_mask.any() else 0.0,
        })

    tabela_resumo = pd.DataFrame(rows)

    detalhe_por_nivel = {}
    for nivel in niveis_order:
        sub = df[df["Nível"] == nivel][
            ["Opportunity Name", "Account Name", "Stage", "Amount"]
            + (["Close Date"] if "Close Date" in df.columns else [])
        ].copy()
        sub = sub.sort_values("Amount", ascending=False).reset_index(drop=True)
        detalhe_por_nivel[nivel] = sub

    return {
        "tabela_resumo": tabela_resumo,
        "detalhe_por_nivel": detalhe_por_nivel,
        "df_crm_com_nivel": df,
    }
