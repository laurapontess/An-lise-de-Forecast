import pandas as pd
import numpy as np
from core.analysis.helpers import classificar_nivel, is_won, is_lost, is_pipeline
from utils.constants import NIVEIS, NIVEL_MIDPOINTS, IDEAL_WALLET_SIZE


def run(df_crm: pd.DataFrame, meta_nr: float) -> dict:
    df = df_crm.copy()
    df["Nível"] = df["Amount"].apply(classificar_nivel)

    niveis_order = list(NIVEIS.keys())

    # Taxas de conversão por nível
    taxas = []
    for nivel in niveis_order:
        subset = df[df["Nível"] == nivel]
        total = len(subset)
        won_df = subset[subset["Stage"].apply(is_won)]
        pipe_df = subset[subset["Stage"].apply(is_pipeline)]

        taxa_won = won_df.shape[0] / total if total > 0 else 0.0
        ticket = won_df["Amount"].mean() if not won_df.empty else NIVEL_MIDPOINTS.get(nivel, 0)
        ticket = ticket if not np.isnan(ticket) else NIVEL_MIDPOINTS.get(nivel, 0)

        taxas.append({
            "Nível": nivel,
            "Total Opps": total,
            "Won": won_df.shape[0],
            "Pipeline Ativo": pipe_df.shape[0],
            "Taxa SQL→Won": taxa_won,
            "Ticket Médio Won (R$)": ticket,
        })

    df_taxas = pd.DataFrame(taxas)

    # Composição ideal da carteira de 17 clientes
    won_all = df[df["Stage"].apply(is_won)]
    total_won = len(won_all)

    composicao = []
    for nivel in niveis_order:
        won_nivel = won_all[won_all["Nível"] == nivel]
        prop = len(won_nivel) / total_won if total_won > 0 else 0
        slots = max(1, round(prop * IDEAL_WALLET_SIZE)) if prop > 0 else 0

        ticket_row = df_taxas[df_taxas["Nível"] == nivel]["Ticket Médio Won (R$)"].values
        ticket = ticket_row[0] if len(ticket_row) > 0 else NIVEL_MIDPOINTS.get(nivel, 0)
        nr_contrib = slots * ticket * 0.05  # take rate médio estimado para projeção

        composicao.append({
            "Nível": nivel,
            "Slots Ideais": slots,
            "Ticket Médio (R$)": ticket,
            "NR Projetado (R$)": nr_contrib,
        })

    df_composicao = pd.DataFrame(composicao)
    # Ajustar total para IDEAL_WALLET_SIZE
    total_slots = df_composicao["Slots Ideais"].sum()
    if total_slots != IDEAL_WALLET_SIZE and total_slots > 0:
        diff = IDEAL_WALLET_SIZE - total_slots
        idx_max = df_composicao["Slots Ideais"].idxmax()
        df_composicao.at[idx_max, "Slots Ideais"] += diff

    # SQLs necessários por mês para N3 e N4
    sqls_necessarios = {}
    for nivel in ["N3", "N4"]:
        row = df_taxas[df_taxas["Nível"] == nivel]
        taxa = row["Taxa SQL→Won"].values[0] if not row.empty else 0.0
        slots_alvo = df_composicao[df_composicao["Nível"] == nivel]["Slots Ideais"].values
        slots = slots_alvo[0] if len(slots_alvo) > 0 else 0
        sqls_necessarios[nivel] = round(slots / taxa) if taxa > 0 else None

    # Distribuição recomendada de SQLs totais por nível
    dist_rows = []
    for nivel in niveis_order:
        taxa_row = df_taxas[df_taxas["Nível"] == nivel]["Taxa SQL→Won"].values
        taxa = taxa_row[0] if len(taxa_row) > 0 else 0.0
        comp_row = df_composicao[df_composicao["Nível"] == nivel]["Slots Ideais"].values
        slots = comp_row[0] if len(comp_row) > 0 else 0
        sqls_mes = round(slots / taxa) if taxa > 0 and slots > 0 else 0

        dist_rows.append({
            "Nível": nivel,
            "Slots na Carteira Ideal": slots,
            "Taxa SQL→Won": taxa,
            "SQLs/mês Necessários": sqls_mes,
        })

    df_distribuicao = pd.DataFrame(dist_rows)

    return {
        "df_taxas_conversao": df_taxas,
        "df_composicao_ideal": df_composicao,
        "sqls_necessarios_n3_n4": sqls_necessarios,
        "df_distribuicao_sqls": df_distribuicao,
    }
