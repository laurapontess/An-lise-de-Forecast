import streamlit as st


def render():
    st.subheader("📂 Upload das Planilhas")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**📊 Base 1 — Carteira Ativa (BI)**")
        st.caption(
            "Clientes que atingiram ≥ R$ 10k de GMV. "
            "Colunas: User ID, Account Name, Net Revenue, Take Rate, Months from Activation, …"
        )
        file_carteira = st.file_uploader(
            "Carteira Ativa",
            type=["xlsx", "csv", "xls"],
            key="carteira",
            label_visibility="collapsed",
        )
        if file_carteira:
            st.success(f"✅ {file_carteira.name}")

    with col2:
        st.markdown("**🔄 Base 2 — Para Ativar (BI)**")
        st.caption(
            "Clientes fechados que ainda não atingiram R$ 10k de GMV. "
            "Colunas: User ID, Account Name, Amount, GMV Faltante, Onb Nome, …"
        )
        file_ativar = st.file_uploader(
            "Para Ativar",
            type=["xlsx", "csv", "xls"],
            key="ativar",
            label_visibility="collapsed",
        )
        if file_ativar:
            st.success(f"✅ {file_ativar.name}")

    with col3:
        st.markdown("**⭐ Base 3 — Oportunidades (Salesforce)**")
        st.caption(
            "Oportunidades do mês anterior — será filtrado apenas 'Closed Won'. "
            "Colunas: Account Name, Stage, Amount, Opportunity Name, …"
        )
        file_crm = st.file_uploader(
            "Oportunidades CRM",
            type=["xlsx", "csv", "xls"],
            key="crm",
            label_visibility="collapsed",
        )
        if file_crm:
            st.success(f"✅ {file_crm.name}")

    return file_carteira, file_ativar, file_crm
