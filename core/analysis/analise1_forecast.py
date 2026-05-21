import pandas as pd
from core.analysis.helpers import calcular_prob_ativacao, is_pipeline, is_won
from utils.constants import META_WEIGHT_NR, META_WEIGHT_SQL, ACTIVATION_THRESHOLD


def run(df_carteira: pd.DataFrame, df_ativar: pd.DataFrame, df_crm: pd.DataFrame,
        meta_nr: float, meta_sqls: int) -> dict:

    # Carteira ativa: excluir mês 3 (saem obrigatoriamente)
    carteira_ativa = df_carteira[df_carteira["Months from Activation"] < 3].copy()
    saidas = df_carteira[df_carteira["Months from Activation"] >= 3].copy()

    nr_projetado = carteira_ativa["Net Revenue"].sum()

    # Resumo por mês de transição
    resumo_por_mes = (
        carteira_ativa.groupby("Months from Activation")
        .agg(qtd_clientes=("Account Name", "count"), nr_total=("Net Revenue", "sum"))
        .reset_index()
        .rename(columns={"Months from Activation": "Mês na Carteira"})
    )

    # Pipeline de ativação com probabilidade
    df_ativar = df_ativar.copy()
    df_ativar["Probabilidade"] = df_ativar["GMV Faltante"].apply(calcular_prob_ativacao)
    df_ativar["NR Esperado"] = df_ativar.apply(
        lambda r: r.get("Net Revenue", r["Amount"] * 0.05) * r["Probabilidade"]
        if "Net Revenue" in df_ativar.columns
        else r["Amount"] * 0.05 * r["Probabilidade"],
        axis=1,
    )
    nr_pipeline = df_ativar["NR Esperado"].sum()

    # SQLs quentes: oportunidades em pipeline ativo no CRM
    sqls_quentes = int(df_crm["Stage"].apply(is_pipeline).sum()) if not df_crm.empty else 0

    # Atingimento ponderado
    ating_nr = min(nr_projetado / meta_nr, 1.0) if meta_nr > 0 else 0.0
    ating_sql = min(sqls_quentes / meta_sqls, 1.0) if meta_sqls > 0 else 0.0
    ating_ponderado = ating_nr * META_WEIGHT_NR + ating_sql * META_WEIGHT_SQL

    # Forecast total (projetado + melhor caso do pipeline)
    nr_forecast_total = nr_projetado + nr_pipeline

    return {
        "nr_projetado": nr_projetado,
        "nr_pipeline": nr_pipeline,
        "nr_forecast_total": nr_forecast_total,
        "sqls_quentes": sqls_quentes,
        "ating_nr": ating_nr,
        "ating_sql": ating_sql,
        "ating_ponderado": ating_ponderado,
        "df_carteira_ativa": carteira_ativa,
        "df_resumo_por_mes": resumo_por_mes,
        "df_saidas": saidas,
        "df_pipeline_ativacao": df_ativar.sort_values("Probabilidade", ascending=False),
    }
