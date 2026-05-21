import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from utils.formatting import fmt_currency, fmt_pct
from utils.constants import NIVEIS


def _color_ating(val: float) -> str:
    if val >= 0.8:
        return "green"
    elif val >= 0.5:
        return "orange"
    return "red"


def render(r1: dict, r2: dict, r3: dict, r4: dict):
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Análise 1 — Forecast",
        "🏷️ Análise 2 — Segmentação N1-N7",
        "🔀 Análise 3 — Cruzamento",
        "🎯 Análise 4 — Simulação SQLs",
    ])

    # ── TAB 1 ────────────────────────────────────────────────────
    with tab1:
        st.subheader("Forecast do Mês")

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("NR Projetado", fmt_currency(r1["nr_projetado"]))
        col2.metric("Pipeline Ativação", fmt_currency(r1["nr_pipeline"]))
        col3.metric("SQLs Quentes", str(r1["sqls_quentes"]))

        ating = r1["ating_ponderado"]
        col4.metric(
            "Atingimento Ponderado",
            f"{ating * 100:.1f}%",
            delta=f"NR {r1['ating_nr']*100:.0f}% | SQL {r1['ating_sql']*100:.0f}%",
        )

        st.progress(min(ating, 1.0))

        st.markdown("---")
        st.markdown("#### Carteira Ativa por Mês de Transição")
        resumo = r1["df_resumo_por_mes"].copy()
        mes_labels = {0: "Mês 0 (novo)", 1: "Mês 1", 2: "Mês 2"}
        resumo["Mês na Carteira"] = resumo["Mês na Carteira"].map(
            lambda x: mes_labels.get(x, str(x))
        )
        resumo.columns = ["Mês na Carteira", "Qtd Clientes", "NR Total (R$)"]

        def color_mes(val):
            if "0" in str(val):
                return "background-color: #d4edda"
            elif "1" in str(val):
                return "background-color: #fff3cd"
            elif "2" in str(val):
                return "background-color: #ffe0b2"
            return ""

        st.dataframe(
            resumo.style.applymap(color_mes, subset=["Mês na Carteira"]),
            use_container_width=True,
            hide_index=True,
        )

        if not r1["df_saidas"].empty:
            st.markdown("#### ⚠️ Saídas Obrigatórias (Mês 3)")
            st.error(f"{len(r1['df_saidas'])} cliente(s) saindo obrigatoriamente da carteira")
            cols = [c for c in ["Account Name", "Net Revenue", "Months from Activation"]
                    if c in r1["df_saidas"].columns]
            st.dataframe(r1["df_saidas"][cols], use_container_width=True, hide_index=True)
        else:
            st.info("Nenhuma saída obrigatória neste mês.")

        pipe = r1["df_pipeline_ativacao"]
        if not pipe.empty:
            st.markdown("#### Pipeline de Ativação")
            cols = [c for c in ["Account Name", "Amount", "GMV Faltante", "Probabilidade", "NR Esperado"]
                    if c in pipe.columns]
            display_pipe = pipe[cols].copy()
            if "Probabilidade" in display_pipe.columns:
                display_pipe["Probabilidade"] = display_pipe["Probabilidade"].apply(fmt_pct)
            if "Amount" in display_pipe.columns:
                display_pipe["Amount"] = display_pipe["Amount"].apply(fmt_currency)
            if "GMV Faltante" in display_pipe.columns:
                display_pipe["GMV Faltante"] = display_pipe["GMV Faltante"].apply(fmt_currency)
            if "NR Esperado" in display_pipe.columns:
                display_pipe["NR Esperado"] = display_pipe["NR Esperado"].apply(fmt_currency)
            st.dataframe(display_pipe, use_container_width=True, hide_index=True)

            fig = px.bar(
                pipe.head(15),
                x="Account Name",
                y="Probabilidade",
                title="Probabilidade de Ativação por Cliente",
                color="Probabilidade",
                color_continuous_scale=["red", "yellow", "green"],
                range_color=[0, 1],
            )
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)

    # ── TAB 2 ────────────────────────────────────────────────────
    with tab2:
        st.subheader("Segmentação por Nível N1–N7")

        tabela = r2["tabela_resumo"].copy()
        st.dataframe(
            tabela.style.background_gradient(subset=["Amount Total (R$)", "Amount Won (R$)"], cmap="Blues"),
            use_container_width=True,
            hide_index=True,
        )

        fig = px.bar(
            tabela,
            x="Nível",
            y=["Won", "Pipeline Ativo", "Lost"],
            title="Distribuição de Oportunidades por Nível",
            barmode="stack",
            color_discrete_map={"Won": "#28a745", "Pipeline Ativo": "#007bff", "Lost": "#dc3545"},
        )
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")
        st.markdown("#### Oportunidades por Nível")
        for nivel, df_nivel in r2["detalhe_por_nivel"].items():
            if df_nivel.empty:
                continue
            with st.expander(f"{nivel} — {len(df_nivel)} oportunidade(s)"):
                d = df_nivel.copy()
                if "Amount" in d.columns:
                    d["Amount"] = d["Amount"].apply(fmt_currency)
                if "Close Date" in d.columns:
                    d["Close Date"] = d["Close Date"].apply(
                        lambda x: x.strftime("%d/%m/%Y") if pd.notna(x) else ""
                    )
                st.dataframe(d, use_container_width=True, hide_index=True)

    # ── TAB 3 ────────────────────────────────────────────────────
    with tab3:
        st.subheader("Cruzamento Nível × Status da Carteira")

        if r3["pivot_count"].empty:
            st.info("Nenhum deal Closed Won encontrado para cruzamento.")
        else:
            st.markdown("#### Quantidade de Contas por Status")

            pivot_c = r3["pivot_count"].reset_index()
            st.dataframe(
                pivot_c.style.applymap(
                    lambda v: "background-color: #ffcccc; font-weight: bold"
                    if isinstance(v, (int, float)) and v > 0 and "Limbo" in str(pivot_c.columns),
                    subset=[c for c in pivot_c.columns if c != "Nível"],
                ),
                use_container_width=True,
            )

            st.markdown("#### Amount Total por Status (R$)")
            pivot_a = r3["pivot_amount"].reset_index().copy()
            for col in pivot_a.columns[1:]:
                pivot_a[col] = pivot_a[col].apply(fmt_currency)
            st.dataframe(pivot_a, use_container_width=True, hide_index=True)

            limbo = r3["limbo_detail"]
            limbo_nz = limbo[limbo["amount_total"] > 0] if not limbo.empty else limbo
            if not limbo_nz.empty:
                st.markdown("---")
                st.error(
                    f"⚠️ {fmt_currency(r3['total_limbo_amount'])} parados em Limbo — requer ação imediata"
                )
                l = limbo_nz.copy()
                l.columns = ["Nível", "Qtd Contas", "Amount Total (R$)"]
                l["Amount Total (R$)"] = l["Amount Total (R$)"].apply(fmt_currency)
                st.dataframe(l, use_container_width=True, hide_index=True)

                won_class = r3["df_won_classificado"]
                limbo_accounts = won_class[won_class["Status Carteira"] == "Limbo"][
                    ["Account Name", "Opportunity Name", "Amount", "Nível"]
                ].copy() if "Opportunity Name" in won_class.columns else \
                won_class[won_class["Status Carteira"] == "Limbo"][
                    ["Account Name", "Amount", "Nível"]
                ].copy()
                limbo_accounts["Amount"] = limbo_accounts["Amount"].apply(fmt_currency)
                with st.expander("Ver todas as contas em Limbo"):
                    st.dataframe(limbo_accounts, use_container_width=True, hide_index=True)

            # Sankey
            won_class = r3["df_won_classificado"]
            if not won_class.empty and "Status Carteira" in won_class.columns:
                status_counts = won_class["Status Carteira"].value_counts()
                fig = px.pie(
                    values=status_counts.values,
                    names=status_counts.index,
                    title="Distribuição de Clientes Won por Status",
                    color=status_counts.index,
                    color_discrete_map={
                        "Vendendo na carteira": "#28a745",
                        "Para ativar": "#ffc107",
                        "Limbo": "#dc3545",
                    },
                )
                st.plotly_chart(fig, use_container_width=True)

    # ── TAB 4 ────────────────────────────────────────────────────
    with tab4:
        st.subheader("Simulação de Meta de SQLs N3 e N4")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Taxas de Conversão por Nível")
            taxas = r4["df_taxas_conversao"].copy()
            taxas_display = taxas.copy()
            taxas_display["Taxa SQL→Won"] = taxas_display["Taxa SQL→Won"].apply(fmt_pct)
            taxas_display["Ticket Médio Won (R$)"] = taxas_display["Ticket Médio Won (R$)"].apply(fmt_currency)
            st.dataframe(taxas_display, use_container_width=True, hide_index=True)

            fig = px.bar(
                taxas[taxas["Total Opps"] > 0],
                x="Nível",
                y="Taxa SQL→Won",
                title="Taxa de Conversão SQL→Won por Nível",
                color="Taxa SQL→Won",
                color_continuous_scale=["red", "yellow", "green"],
            )
            fig.update_yaxes(tickformat=".0%")
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown("#### Composição Ideal da Carteira (17 clientes)")
            comp = r4["df_composicao_ideal"].copy()
            comp_display = comp.copy()
            comp_display["Ticket Médio (R$)"] = comp_display["Ticket Médio (R$)"].apply(fmt_currency)
            comp_display["NR Projetado (R$)"] = comp_display["NR Projetado (R$)"].apply(fmt_currency)
            st.dataframe(comp_display[comp_display["Slots Ideais"] > 0], use_container_width=True, hide_index=True)

            fig2 = px.pie(
                comp[comp["Slots Ideais"] > 0],
                values="Slots Ideais",
                names="Nível",
                title="Distribuição Ideal de Slots na Carteira",
            )
            st.plotly_chart(fig2, use_container_width=True)

        st.markdown("---")
        st.markdown("#### SQLs Necessários por Mês por Nível")
        dist = r4["df_distribuicao_sqls"].copy()
        dist_display = dist.copy()
        dist_display["Taxa SQL→Won"] = dist_display["Taxa SQL→Won"].apply(fmt_pct)
        st.dataframe(dist_display[dist_display["Slots na Carteira Ideal"] > 0],
                     use_container_width=True, hide_index=True)

        sqls = r4["sqls_necessarios_n3_n4"]
        c1, c2 = st.columns(2)
        c1.metric("SQLs N3 necessários/mês", sqls.get("N3") or "N/D")
        c2.metric("SQLs N4 necessários/mês", sqls.get("N4") or "N/D")
