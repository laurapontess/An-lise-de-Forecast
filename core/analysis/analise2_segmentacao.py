"""
Análise 2 — Segmentação por Nível (N2‒N7) nas 3 fases

Fase 1 — Na Carteira Ativa    (Base 1): classifica por GMV Total
Fase 2 — Para Ativar          (Base 2): classifica por Amount; agrupa por Onb Nome
Fase 3 — Closed Won (CRM)     (Base 3): classifica por Amount
"""
import pandas as pd
from core.analysis.helpers import classificar_nivel
from utils.constants import NIVEIS_ORDER


# ── Utilitário ─────────────────────────────────────────────────────────────────

def _resumo_por_nivel(df: pd.DataFrame, valor_col: str, label_fase: str) -> pd.DataFrame:
    """Agrupa DataFrame por nível e retorna tabela resumo."""
    df = df.copy()
    df["Nível"] = df[valor_col].apply(classificar_nivel)

    rows = []
    for nivel in NIVEIS_ORDER:
        sub = df[df["Nível"] == nivel]
        rows.append({
            "Nível": nivel,
            "Qtd Contas": len(sub),
            f"Volume Total (R$)": sub[valor_col].sum(),
        })

    result = pd.DataFrame(rows)
    result["Fase"] = label_fase
    return result


# ── Análise principal ──────────────────────────────────────────────────────────

def run(
    df_carteira: pd.DataFrame,
    df_ativar: pd.DataFrame,
    df_crm_won: pd.DataFrame,
) -> dict:

    # Escolhe coluna de valor para Base 1
    valor_carteira = "GMV Total" if "GMV Total" in df_carteira.columns else "Net Revenue"

    # ── Resumos gerais ──────────────────────────────────────────────────────
    resumo_carteira  = _resumo_por_nivel(df_carteira,  valor_carteira, "Na Carteira")
    resumo_ativar    = _resumo_por_nivel(df_ativar,    "Amount",       "Para Ativar")
    resumo_crm_won   = _resumo_por_nivel(df_crm_won,   "Amount",       "Closed Won")

    # ── Detalhes com nível classificado ────────────────────────────────────
    df_cart = df_carteira.copy()
    df_cart["Nível"] = df_cart[valor_carteira].apply(classificar_nivel)

    df_atv = df_ativar.copy()
    df_atv["Nível"] = df_atv["Amount"].apply(classificar_nivel)

    df_won = df_crm_won.copy()
    df_won["Nível"] = df_won["Amount"].apply(classificar_nivel)

    # ── Insight de Onb Nome (Base 2) ────────────────────────────────────────
    # "Você tem X contas N6 aguardando ativação que dependem do CS [Onb Nome]."
    insights_onb = _insight_onb(df_atv)

    # ── Detalhes por nível para cada fase ───────────────────────────────────
    detalhes = {}
    for nivel in NIVEIS_ORDER:
        c = df_cart[df_cart["Nível"] == nivel].copy()
        a = df_atv[df_atv["Nível"] == nivel].copy()
        w = df_won[df_won["Nível"] == nivel].copy()
        detalhes[nivel] = {"carteira": c, "ativar": a, "won": w}

    return {
        "resumo_carteira":  resumo_carteira,
        "resumo_ativar":    resumo_ativar,
        "resumo_crm_won":   resumo_crm_won,
        "insights_onb":     insights_onb,
        "df_carteira":      df_cart,
        "df_ativar":        df_atv,
        "df_won":           df_won,
        "detalhes_por_nivel": detalhes,
        "valor_col_carteira": valor_carteira,
    }


def _insight_onb(df_atv_com_nivel: pd.DataFrame) -> list[dict]:
    """
    Retorna lista de insights: por nível + CS responsável.
    Ex: {"nivel": "N6", "onb_nome": "João", "qtd": 3, "gmv_faltante_total": 45000}
    """
    if df_atv_com_nivel.empty:
        return []

    insights = []
    for nivel in NIVEIS_ORDER:
        sub = df_atv_com_nivel[df_atv_com_nivel["Nível"] == nivel]
        if sub.empty:
            continue

        if "Onb Nome" in sub.columns:
            grouped = (
                sub.groupby("Onb Nome", dropna=False)
                .agg(
                    qtd=("Account Name", "count"),
                    gmv_faltante=("GMV Faltante", "sum"),
                    amount_total=("Amount", "sum"),
                )
                .reset_index()
                .sort_values("qtd", ascending=False)
            )
            for _, row in grouped.iterrows():
                insights.append({
                    "nivel":               nivel,
                    "onb_nome":            str(row["Onb Nome"]),
                    "qtd":                 int(row["qtd"]),
                    "gmv_faltante_total":  float(row["gmv_faltante"]),
                    "amount_total":        float(row["amount_total"]),
                })
        else:
            insights.append({
                "nivel":               nivel,
                "onb_nome":            "N/D",
                "qtd":                 len(sub),
                "gmv_faltante_total":  sub["GMV Faltante"].sum(),
                "amount_total":        sub["Amount"].sum(),
            })

    return insights
