import streamlit as st


def render():
    st.subheader("Upload das Planilhas")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**Carteira Ativa**")
        st.caption("Colunas: Account Name, Net Revenue, Months from Activation")
        file_carteira = st.file_uploader(
            "Carteira Ativa", type=["xlsx", "csv"], key="carteira", label_visibility="collapsed"
        )
        if file_carteira:
            st.success("Arquivo carregado")

    with col2:
        st.markdown("**Clientes para Ativar**")
        st.caption("Colunas: Account Name, Amount, GMV Faltante")
        file_ativar = st.file_uploader(
            "Clientes para Ativar", type=["xlsx", "csv"], key="ativar", label_visibility="collapsed"
        )
        if file_ativar:
            st.success("Arquivo carregado")

    with col3:
        st.markdown("**CRM — Oportunidades**")
        st.caption("Colunas: Opportunity Name, Account Name, Stage, Amount")
        file_crm = st.file_uploader(
            "CRM Oportunidades", type=["xlsx", "csv"], key="crm", label_visibility="collapsed"
        )
        if file_crm:
            st.success("Arquivo carregado")

    return file_carteira, file_ativar, file_crm
