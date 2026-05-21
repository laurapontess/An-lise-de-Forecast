import streamlit as st
from core.models import SDRContext


def render() -> SDRContext:
    st.sidebar.header("Configurações do SDR")

    nome = st.sidebar.text_input("Nome do SDR", placeholder="Ex: Maria Silva")
    senioridade = st.sidebar.selectbox(
        "Senioridade", ["Júnior", "Pleno", "Sênior"]
    )
    meta_nr = st.sidebar.number_input(
        "Meta Net Revenue (R$)", min_value=0.0, step=1000.0, format="%.2f"
    )
    meta_sqls = st.sidebar.number_input(
        "Meta SQLs (#)", min_value=0, step=1, value=0
    )
    mes_ref = st.sidebar.text_input(
        "Mês de referência", placeholder="Ex: Maio/2025"
    )

    return SDRContext(
        nome=nome or "SDR",
        senioridade=senioridade,
        meta_net_revenue=float(meta_nr),
        meta_sqls=int(meta_sqls),
        mes_referencia=mes_ref or "—",
    )
