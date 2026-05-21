import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from ui.sidebar import render as render_sidebar
from ui.upload_section import render as render_uploads
from ui.results_section import render as render_results
from core.loaders import load_carteira, load_clientes_ativar, load_crm
from core.analysis import analise1_forecast, analise2_segmentacao, analise3_cruzamento, analise4_simulacao
from core.export.word_exporter import gerar_word

st.set_page_config(
    page_title="Forecast SDR — Hotmart",
    page_icon="📈",
    layout="wide",
)

st.title("📈 Análise de Forecast SDR — Hotmart")
st.markdown("Preencha os dados na barra lateral e faça o upload das três planilhas.")

ctx = render_sidebar()

st.markdown("---")
file_carteira, file_ativar, file_crm = render_uploads()

if file_carteira and file_ativar and file_crm:
    st.markdown("---")
    try:
        with st.spinner("Processando análises..."):
            df_carteira = load_carteira(file_carteira)
            df_ativar = load_clientes_ativar(file_ativar)
            df_crm = load_crm(file_crm)

            r1 = analise1_forecast.run(df_carteira, df_ativar, df_crm,
                                       ctx.meta_net_revenue, ctx.meta_sqls)
            r2 = analise2_segmentacao.run(df_crm)
            r3 = analise3_cruzamento.run(df_crm, df_carteira, df_ativar)
            r4 = analise4_simulacao.run(df_crm, ctx.meta_net_revenue)

        render_results(r1, r2, r3, r4)

        st.markdown("---")
        st.subheader("📄 Exportar Relatório")
        if st.button("Gerar Word (.docx)", type="primary"):
            with st.spinner("Gerando documento..."):
                word_bytes = gerar_word(ctx, r1, r2, r3, r4)
            file_name = f"forecast_{ctx.nome.replace(' ', '_')}_{ctx.mes_referencia.replace('/', '-')}.docx"
            st.download_button(
                label="⬇️ Baixar Relatório Word",
                data=word_bytes,
                file_name=file_name,
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )

    except ValueError as e:
        st.error(f"Erro nos dados: {e}")
    except Exception as e:
        st.error(f"Erro inesperado: {e}")
        with st.expander("Detalhes do erro"):
            import traceback
            st.code(traceback.format_exc())
else:
    st.info("Carregue as três planilhas para iniciar a análise.")
