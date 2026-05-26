import streamlit as st
from core.models import SDRContext


def render() -> SDRContext:
    st.sidebar.header("⚙️ Configurações do SDR")

    nome = st.sidebar.text_input(
        "Nome do SDR",
        placeholder="Ex: Maria Silva",
        help="Nome completo do SDR que usará este relatório.",
    )

    senioridade = st.sidebar.selectbox(
        "Senioridade",
        options=["Júnior", "Pleno"],
        help="Nível do SDR: Júnior ou Pleno.",
    )

    mes_ref = st.sidebar.text_input(
        "Mês de Referência",
        placeholder="Ex: Maio/2025",
        help="Período da análise (ex: Maio/2025).",
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("**🎯 Metas do Mês**")

    meta_nr = st.sidebar.number_input(
        "Meta Net Revenue (R$)",
        min_value=0.0,
        step=1_000.0,
        format="%.2f",
        help="Meta de Net Revenue declarada pela coordenação para o mês.",
    )

    meta_sqls = st.sidebar.number_input(
        "Meta de SQLs (#)",
        min_value=0,
        step=1,
        value=0,
        help="Quantidade de SQLs (Closed Won) que o SDR precisa atingir no mês.",
    )

    st.sidebar.markdown("---")
    st.sidebar.caption(
        "💡 **Como usar:** Preencha os campos acima e faça upload "
        "das 3 planilhas para iniciar a análise."
    )

    return SDRContext(
        nome=nome.strip() if nome else "SDR",
        senioridade=senioridade,
        meta_net_revenue=float(meta_nr),
        meta_sqls=int(meta_sqls),
        mes_referencia=mes_ref.strip() if mes_ref else "—",
    )
