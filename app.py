"""
Dashboard Interativo de Forecast SDR
Análise de Gap, Priorização por Nível, Alertas de Limbo e Relatório PDF.
"""
import streamlit as st
import sys
import os
import traceback

sys.path.insert(0, os.path.dirname(__file__))

from ui.sidebar import render as render_sidebar
from ui.upload_section import render as render_uploads
from ui.results_section import render as render_results

from core.loaders import load_carteira, load_clientes_ativar, load_crm
from core.analysis import analise1_forecast, analise2_segmentacao, analise3_cruzamento
from core.export.pdf_exporter import gerar_pdf


# ── Configuração da página ─────────────────────────────────────────────────────
st.set_page_config(
    page_title="Forecast SDR",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS customizado ────────────────────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stMetric"] {
    background: #F0F4F8;
    border-radius: 10px;
    padding: 12px 16px;
    border-left: 4px solid #0066CC;
}
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
}
.stTabs [data-baseweb="tab"] {
    height: 44px;
    padding: 0 16px;
    border-radius: 8px 8px 0 0;
}
div[data-testid="stExpander"] {
    border: 1px solid #E0E0E0;
    border-radius: 8px;
}
</style>
""", unsafe_allow_html=True)

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown(
    "<h1 style='color:#003B5C;margin-bottom:4px'>📈 Dashboard de Forecast SDR</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='color:#6C757D;font-size:0.95em;margin-top:0'>"
    "Preencha os dados na barra lateral e faça o upload das três planilhas para iniciar a análise.</p>",
    unsafe_allow_html=True,
)

# ── Sidebar ────────────────────────────────────────────────────────────────────
ctx = render_sidebar()

st.markdown("---")

# ── Upload das bases ───────────────────────────────────────────────────────────
file_carteira, file_ativar, file_crm = render_uploads()

st.markdown("---")

# ── Processamento e resultados ─────────────────────────────────────────────────
if file_carteira and file_ativar and file_crm:

    try:
        with st.spinner("⚙️ Processando dados e gerando análises…"):
            # Carrega e valida as bases
            df_carteira  = load_carteira(file_carteira)
            df_ativar    = load_clientes_ativar(file_ativar)
            df_crm_won   = load_crm(file_crm)          # já filtrado: Closed Won

            # Avisa se não há Closed Won
            if df_crm_won.empty:
                st.warning(
                    "⚠️ Nenhuma oportunidade 'Closed Won' encontrada na Base 3. "
                    "Verifique se a coluna 'Stage' contém o valor 'Closed Won'."
                )

            # Executa as análises
            r1 = analise1_forecast.run(
                df_carteira, df_ativar, df_crm_won,
                ctx.meta_net_revenue, ctx.meta_sqls,
            )
            r2 = analise2_segmentacao.run(df_carteira, df_ativar, df_crm_won)
            r3 = analise3_cruzamento.run(df_crm_won, df_carteira, df_ativar)

        # Alerta imediato de Limbo (antes das tabs)
        if r3.get("total_limbo_count", 0) > 0:
            from utils.formatting import fmt_currency
            cnt = r3["total_limbo_count"]
            amt = r3["total_limbo_amount"]
            st.error(
                f"🚨 **ALERTA CRÍTICO — LIMBO:** {cnt} conta(s) Closed Won "
                f"**não constam no BI** (nem carteira ativa, nem para ativar). "
                f"Volume total em risco: **{fmt_currency(amt)}**. "
                f"Veja a aba **🚨 Limbo** para detalhes."
            )

        # Renderiza resultados
        render_results(ctx, r1, r2, r3, r4=None)

        # ── Exportar PDF ───────────────────────────────────────────────────────
        st.markdown("---")
        st.subheader("📄 Exportar Relatório para Reunião de 1:1")
        st.markdown(
            "Clique no botão abaixo para gerar um PDF consolidado com todos os insights, "
            "análises de gap, alertas de limbo e priorização de níveis."
        )

        col_btn, col_info = st.columns([1, 3])
        with col_btn:
            if st.button("🖨️ Gerar Relatório PDF", type="primary", use_container_width=True):
                with st.spinner("Gerando PDF…"):
                    pdf_bytes = gerar_pdf(ctx, r1, r2, r3, r4=None)

                nome_arquivo = (
                    f"forecast_{ctx.nome.replace(' ', '_')}_"
                    f"{ctx.mes_referencia.replace('/', '-')}.pdf"
                )
                st.download_button(
                    label="⬇️ Baixar PDF",
                    data=pdf_bytes,
                    file_name=nome_arquivo,
                    mime="application/pdf",
                    use_container_width=True,
                )
                st.success(f"✅ PDF gerado: **{nome_arquivo}**")

        with col_info:
            st.info(
                "O PDF inclui: capa com dados do SDR, análise de gap, "
                "priorização por Nível N2‒N7 nas 3 fases, alertas de limbo, "
                "insights de CS e carteira ativa por lifecycle."
            )

    except ValueError as e:
        st.error(f"❌ Erro nos dados: {e}")
        with st.expander("Detalhes do erro"):
            st.code(traceback.format_exc())
    except Exception as e:
        st.error(f"❌ Erro inesperado: {e}")
        with st.expander("Detalhes técnicos"):
            st.code(traceback.format_exc())

else:
    # Estado inicial — guia de uso
    st.info("👆 Carregue as três planilhas acima para iniciar a análise.")
    st.markdown("---")
    st.markdown("""
    ### 📋 Guia Rápido

    | # | Planilha | Colunas Mínimas Obrigatórias |
    |---|----------|------------------------------|
    | 1 | **Carteira Ativa (BI)** | Account Name, Net Revenue, Months from Activation |
    | 2 | **Para Ativar (BI)** | Account Name, Amount, GMV Faltante |
    | 3 | **Oportunidades (Salesforce)** | Account Name, Stage, Amount |

    ### 🏷️ Tabela de Níveis por Faturamento/GMV

    | Nível | Faturamento Anual |
    |-------|-------------------|
    | N2 | R$ 100.000 a R$ 599.999 |
    | N3 | R$ 600.000 a R$ 999.999 |
    | N4 | R$ 1.000.000 a R$ 1.999.999 |
    | N5 | R$ 2.000.000 a R$ 4.999.999 |
    | N6 | R$ 5.000.000 a R$ 9.999.999 |
    | N7 | R$ 10.000.000 ou mais |

    ### ⚖️ Composição da Meta
    - **60%** de peso em Net Revenue
    - **40%** de peso em SQLs (Closed Won)

    ### 📅 Lifecycle de Receita
    Um cliente gera receita para o SDR nos **Meses 0, 1, 2 e 3** após a Activation Date (4 meses).
    """)
