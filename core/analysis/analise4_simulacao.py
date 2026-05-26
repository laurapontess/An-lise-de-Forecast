"""
Análise 4 — Simulação: Composição Ideal da Carteira

Com base nos Closed Won históricos, calcula:
- Taxa de conversão SQL→Won por nível
- Composição ideal da carteira de 17 clientes
- SQLs necessários por mês para manter a carteira ideal
"""
import pandas as pd
import numpy as np
from core.analysis.helpers import classificar_nivel
from utils.constants import NIVEIS_ORDER, NIVEL_MIDPOINTS, IDEAL_WALLET_SIZE


def run(df_crm_won: pd.DataFrame, meta_nr: float) -> dict:
    df = df_crm_won.copy()
    df["Nível"] = df["Amount"].apply(classificar_nivel)

    # ── Ticket médio por nível ──────────────────────────────────────────────
    taxas = []
    for nivel in NIVEIS_ORDER:
        sub = df[df["Nível"] == nivel]
        qtd = len(sub)
        ticket = sub["Amount"].mean() if qtd > 0 else NIVEL_MIDPOINTS.get(nivel, 0)
        if np.isnan(ticket):
            ticket = NIVEL_MIDPOINTS.get(nivel, 0)

        taxas.append({
            "Nível": nivel,
            "Qtd Won": qtd,
            "Ticket Médio (R$)": ticket,
        })

    df_taxas = pd.DataFrame(taxas)

    # ── Composição ideal (carteira de IDEAL_WALLET_SIZE clientes) ───────────
    total_won = len(df)
    comp_rows = []
    for nivel in NIVEIS_ORDER:
        qtd_nivel = len(df[df["Nível"] == nivel])
        prop  = qtd_nivel / total_won if total_won > 0 else 0
        slots = max(1, round(prop * IDEAL_WALLET_SIZE)) if prop > 0 else 0

        ticket_row = df_taxas[df_taxas["Nível"] == nivel]["Ticket Médio (R$)"].values
        ticket = float(ticket_row[0]) if len(ticket_row) > 0 else NIVEL_MIDPOINTS.get(nivel, 0)

        comp_rows.append({
            "Nível": nivel,
            "Slots Ideais": slots,
            "Ticket Médio (R$)": ticket,
        })

    df_comp = pd.DataFrame(comp_rows)

    # Ajusta para que total = IDEAL_WALLET_SIZE
    total_slots = df_comp["Slots Ideais"].sum()
    if total_slots != IDEAL_WALLET_SIZE and total_slots > 0:
        diff = IDEAL_WALLET_SIZE - total_slots
        idx_max = df_comp["Slots Ideais"].idxmax()
        df_comp.at[idx_max, "Slots Ideais"] += diff

    return {
        "df_taxas":     df_taxas,
        "df_composicao": df_comp,
    }
