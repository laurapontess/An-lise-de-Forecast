"""
Análise 1 — Forecast do Mês & Gap de Meta

Regras de negócio:
- Lifecycle: cliente gera receita nos Meses 0, 1, 2 e 3 (4 meses inclusive).
- NR é extraído diretamente da coluna Net Revenue da Base 1 (já usa Take Rate individual).
- SQLs = quantidade de oportunidades Closed Won na Base 3.
- Meta ponderada: 60% NR + 40% SQL.
"""
import pandas as pd
from utils.constants import META_WEIGHT_NR, META_WEIGHT_SQL, MAX_LIFECYCLE_MONTH


def run(
    df_carteira: pd.DataFrame,
    df_ativar: pd.DataFrame,
    df_crm_won: pd.DataFrame,
    meta_nr: float,
    meta_sqls: int,
) -> dict:

    # ── Carteira Ativa (lifecycle 0‒3) ─────────────────────────────────────
    lifecycle_mask = df_carteira["Months from Activation"].between(0, MAX_LIFECYCLE_MONTH)
    carteira_ativa  = df_carteira[lifecycle_mask].copy()
    carteira_saindo = df_carteira[~lifecycle_mask].copy()   # mês > 3, fora do ciclo

    # NR já calculado com Take Rate individual por cliente
    nr_projetado = carteira_ativa["Net Revenue"].sum()

    # Resumo por mês de transição
    resumo_por_mes = (
        carteira_ativa
        .groupby("Months from Activation", sort=True)
        .agg(qtd=("Account Name", "count"), nr=("Net Revenue", "sum"))
        .reset_index()
        .rename(columns={
            "Months from Activation": "Mês na Carteira",
            "qtd": "Qtd Clientes",
            "nr": "NR Total (R$)",
        })
    )

    # ── SQLs Realizados ─────────────────────────────────────────────────────
    sqls_realizados = len(df_crm_won)  # cada linha = 1 Closed Won = 1 SQL

    # ── Gap de Meta ─────────────────────────────────────────────────────────
    gap_nr   = max(meta_nr  - nr_projetado,  0.0)
    gap_sql  = max(meta_sqls - sqls_realizados, 0)

    # ── Atingimento Ponderado ───────────────────────────────────────────────
    ating_nr  = min(nr_projetado / meta_nr,    1.0) if meta_nr  > 0 else 0.0
    ating_sql = min(sqls_realizados / meta_sqls, 1.0) if meta_sqls > 0 else 0.0
    ating_ponderado = ating_nr * META_WEIGHT_NR + ating_sql * META_WEIGHT_SQL

    # ── NR Potencial de Ativação (Base 2) ───────────────────────────────────
    # Estimativa: se cliente ativar, Take Rate médio da carteira × Amount
    tr_medio = carteira_ativa["Take Rate"].mean() if "Take Rate" in carteira_ativa.columns and len(carteira_ativa) > 0 else 0.05
    nr_potencial_ativacao = (df_ativar["Amount"] * tr_medio).sum()

    return {
        # KPIs principais
        "nr_projetado":          nr_projetado,
        "nr_potencial_ativacao": nr_potencial_ativacao,
        "sqls_realizados":       sqls_realizados,
        "meta_nr":               meta_nr,
        "meta_sqls":             meta_sqls,
        # Gaps
        "gap_nr":                gap_nr,
        "gap_sql":               gap_sql,
        # Atingimento
        "ating_nr":              ating_nr,
        "ating_sql":             ating_sql,
        "ating_ponderado":       ating_ponderado,
        # DataFrames
        "df_carteira_ativa":     carteira_ativa,
        "df_carteira_saindo":    carteira_saindo,
        "df_resumo_por_mes":     resumo_por_mes,
        "take_rate_medio":       tr_medio,
    }
