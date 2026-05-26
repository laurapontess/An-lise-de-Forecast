"""
Seção de Resultados — Dashboard interativo de Forecast SDR

Tabs:
  1. Gap & Forecast        — KPIs de atingimento, gaps de meta
  2. Priorização por Nível — N2‒N7 nas 3 fases
  3. Limbo (Alerta Crítico)— Closed Won não encontradas no BI
  4. Carteira Lifecycle    — Meses 0‒3 e saídas
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from utils.formatting import fmt_currency, fmt_pct, fmt_number, fmt_short
from utils.constants import NIVEIS_ORDER, META_WEIGHT_NR, META_WEIGHT_SQL


# ── Helpers visuais ────────────────────────────────────────────────────────────

def _cor_ating(val: float) -> str:
    if val >= 0.8: return "normal"
    if val >= 0.5: return "off"
    return "inverse"


def _badge(texto: str, cor: str) -> str:
    """Retorna HTML de badge colorido."""
    cores = {
        "verde":    ("#d4edda", "#155724"),
        "amarelo":  ("#fff3cd", "#856404"),
        "vermelho": ("#f8d7da", "#721c24"),
        "azul":     ("#cce5ff", "#004085"),
    }
    bg, fg = cores.get(cor, ("#e9ecef", "#495057"))
    return (
        f'<span style="background:{bg};color:{fg};padding:2px 8px;'
        f'border-radius:12px;font-size:0.85em;font-weight:600">{texto}</span>'
    )


def _fmt_df_currency(df: pd.DataFrame, cols: list) -> pd.DataFrame:
    df = df.copy()
    for c in cols:
        if c in df.columns:
            df[c] = df[c].apply(fmt_currency)
    return df


# ── Render principal ───────────────────────────────────────────────────────────

def render(ctx, r1: dict, r2: dict, r3: dict, r4: dict):
    tab1, tab2, tab3, tab4 = st.tabs([
        "🎯 Gap & Forecast",
        "📊 Priorização por Nível",
        "🚨 Limbo",
        "📁 Carteira Lifecycle",
    ])

    with tab1:
        _tab_gap(ctx, r1)

    with tab2:
        _tab_niveis(r2)

    with tab3:
        _tab_limbo(r3)

    with tab4:
        _tab_carteira(r1)


# ── Tab 1 — Gap & Forecast ─────────────────────────────────────────────────────

def _tab_gap(ctx, r1: dict):
    st.subheader("🎯 Análise de Gap & Forecast do Mês")

    ating     = r1["ating_ponderado"]
    ating_nr  = r1["ating_nr"]
    ating_sql = r1["ating_sql"]

    # KPIs topo
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(
        "NR Projetado (Carteira)",
        fmt_currency(r1["nr_projetado"]),
        help="Net Revenue dos clientes ativos nos Meses 0‒3.",
    )
    c2.metric(
        "NR Potencial (Ativação)",
        fmt_currency(r1["nr_potencial_ativacao"]),
        help="Estimativa de NR se todos os clientes da Base 2 ativarem.",
    )
    c3.metric(
        "SQLs Realizados",
        str(r1["sqls_realizados"]),
        delta=f"Meta: {r1['meta_sqls']}",
        delta_color=_cor_ating(ating_sql),
    )
    c4.metric(
        "Atingimento Ponderado",
        f"{ating * 100:.1f}%",
        delta=f"NR {ating_nr*100:.0f}% | SQL {ating_sql*100:.0f}%",
        delta_color=_cor_ating(ating),
    )

    st.progress(min(ating, 1.0))

    # Gauge
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=ating * 100,
        delta={"reference": 100, "suffix": "%"},
        number={"suffix": "%", "font": {"size": 32}},
        title={"text": "Atingimento Ponderado (60% NR + 40% SQL)"},
        gauge={
            "axis": {"range": [0, 100]},
            "bar":  {"color": "#0066CC"},
            "steps": [
                {"range": [0, 50],   "color": "#FADBD8"},
                {"range": [50, 80],  "color": "#FEF9E7"},
                {"range": [80, 100], "color": "#D4EDDA"},
            ],
            "threshold": {
                "line": {"color": "#C0392B", "width": 3},
                "thickness": 0.75,
                "value": 100,
            },
        },
    ))
    fig_gauge.update_layout(height=280, margin=dict(t=60, b=20, l=30, r=30))
    st.plotly_chart(fig_gauge, use_container_width=True)

    st.markdown("---")
    st.markdown("### 📉 Detalhamento do Gap")

    col_a, col_b = st.columns(2)

    with col_a:
        # Gap NR
        nr_proj = r1["nr_projetado"]
        gap_nr  = r1["gap_nr"]
        meta_nr = r1["meta_nr"]

        if gap_nr > 0:
            st.error(f"**Gap de Net Revenue:** faltam **{fmt_currency(gap_nr)}** para atingir a meta.")
        else:
            st.success(f"**Net Revenue:** meta de {fmt_currency(meta_nr)} atingida! ✅")

        fig_nr = go.Figure()
        fig_nr.add_bar(name="NR Projetado", x=["Net Revenue"], y=[nr_proj],
                       marker_color="#0066CC")
        fig_nr.add_bar(name="Gap Restante", x=["Net Revenue"], y=[max(gap_nr, 0)],
                       marker_color="#FADBD8", marker_line_color="#C0392B",
                       marker_line_width=1.5)
        fig_nr.add_hline(y=meta_nr, line_dash="dash", line_color="#C0392B",
                         annotation_text=f"Meta: {fmt_short(meta_nr)}")
        fig_nr.update_layout(
            barmode="stack", title="Net Revenue vs. Meta",
            yaxis_tickformat=",.0f", height=280,
            margin=dict(t=50, b=20, l=20, r=20),
            showlegend=True,
        )
        st.plotly_chart(fig_nr, use_container_width=True)

    with col_b:
        # Gap SQL
        sql_real = r1["sqls_realizados"]
        gap_sql  = r1["gap_sql"]
        meta_sql = r1["meta_sqls"]

        if gap_sql > 0:
            st.error(f"**Gap de SQLs:** faltam **{gap_sql} SQL(s)** (realizados: {sql_real} / meta: {meta_sql}).")
        else:
            st.success(f"**SQLs:** meta de {meta_sql} atingida! ✅")

        fig_sql = go.Figure()
        fig_sql.add_bar(name="SQLs Realizados", x=["SQLs"], y=[sql_real],
                        marker_color="#1A7F3C")
        fig_sql.add_bar(name="Gap Restante", x=["SQLs"], y=[max(gap_sql, 0)],
                        marker_color="#FADBD8", marker_line_color="#C0392B",
                        marker_line_width=1.5)
        fig_sql.add_hline(y=meta_sql, line_dash="dash", line_color="#C0392B",
                          annotation_text=f"Meta: {meta_sql}")
        fig_sql.update_layout(
            barmode="stack", title="SQLs vs. Meta",
            height=280, margin=dict(t=50, b=20, l=20, r=20),
            showlegend=True,
        )
        st.plotly_chart(fig_sql, use_container_width=True)

    # Tabela de atingimento
    st.markdown("### ⚖️ Composição Ponderada da Meta")
    df_ating = pd.DataFrame([
        {
            "Indicador":    "Net Revenue",
            "Realizado":    fmt_currency(r1["nr_projetado"]),
            "Meta":         fmt_currency(r1["meta_nr"]),
            "Gap":          fmt_currency(r1["gap_nr"]),
            "Atingimento":  fmt_pct(ating_nr),
            "Peso":         "60%",
            "Contribuição": fmt_pct(ating_nr * META_WEIGHT_NR),
        },
        {
            "Indicador":    "SQLs (Closed Won)",
            "Realizado":    str(r1["sqls_realizados"]),
            "Meta":         str(r1["meta_sqls"]),
            "Gap":          str(r1["gap_sql"]),
            "Atingimento":  fmt_pct(ating_sql),
            "Peso":         "40%",
            "Contribuição": fmt_pct(ating_sql * META_WEIGHT_SQL),
        },
        {
            "Indicador":    "TOTAL PONDERADO",
            "Realizado":    "–",
            "Meta":         "100%",
            "Gap":          "–",
            "Atingimento":  f"{ating*100:.1f}%",
            "Peso":         "100%",
            "Contribuição": f"{ating*100:.1f}%",
        },
    ])
    st.dataframe(df_ating, use_container_width=True, hide_index=True)

    # Rodapé de perfil
    st.markdown("---")
    st.markdown(
        f"**Perfil:** {ctx.nome} &nbsp;|&nbsp; "
        f"**Senioridade:** {ctx.senioridade} &nbsp;|&nbsp; "
        f"**Período:** {ctx.mes_referencia} &nbsp;|&nbsp; "
        f"**Meta NR:** {fmt_currency(ctx.meta_net_revenue)} &nbsp;|&nbsp; "
        f"**Meta SQLs:** {ctx.meta_sqls}"
    )


# ── Tab 2 — Priorização por Nível ──────────────────────────────────────────────

def _tab_niveis(r2: dict):
    st.subheader("📊 Priorização por Nível (N2‒N7)")

    st.markdown("Cada conta é classificada pelo faturamento/GMV conforme a tabela de Níveis.")

    # Mapa de cores por fase
    fases = [
        ("📁 Fase 1 — Na Carteira Ativa", r2["resumo_carteira"],  "#0066CC", "carteira"),
        ("🔄 Fase 2 — Para Ativar",        r2["resumo_ativar"],    "#F39C12", "ativar"),
        ("⭐ Fase 3 — Closed Won (CRM)",    r2["resumo_crm_won"],   "#1A7F3C", "won"),
    ]

    # Gráfico comparativo
    comp_data = []
    for fase_label, resumo, cor, key in fases:
        for _, row in resumo.iterrows():
            comp_data.append({
                "Nível": row["Nível"],
                "Qtd":   row["Qtd Contas"],
                "Fase":  fase_label,
            })
    df_comp = pd.DataFrame(comp_data)

    if not df_comp.empty and df_comp["Qtd"].sum() > 0:
        fig = px.bar(
            df_comp[df_comp["Qtd"] > 0],
            x="Nível", y="Qtd", color="Fase",
            barmode="group",
            title="Quantidade de Contas por Nível e Fase",
            color_discrete_map={
                "📁 Fase 1 — Na Carteira Ativa": "#0066CC",
                "🔄 Fase 2 — Para Ativar":        "#F39C12",
                "⭐ Fase 3 — Closed Won (CRM)":    "#1A7F3C",
            },
            category_orders={"Nível": NIVEIS_ORDER},
        )
        fig.update_layout(height=350, xaxis_title="Nível", yaxis_title="Qtd de Contas")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Tabelas por fase
    for fase_label, resumo, cor, key in fases:
        st.markdown(f"#### {fase_label}")
        if resumo is not None and not resumo.empty and resumo["Qtd Contas"].sum() > 0:
            vol_col = [c for c in resumo.columns if "Volume" in c or "R$" in c]
            vol_col = vol_col[0] if vol_col else resumo.columns[-1]
            df_show = resumo[resumo["Qtd Contas"] > 0].copy()
            df_show[vol_col] = df_show[vol_col].apply(fmt_currency)
            st.dataframe(df_show[["Nível", "Qtd Contas", vol_col]],
                         use_container_width=True, hide_index=True)
        else:
            st.info("Nenhuma conta nesta fase.")
        st.markdown("")

    # Insights de Onb Nome (Base 2)
    st.markdown("---")
    st.markdown("### 🧑‍💼 Insights de Onboarding — Para Ativar")
    st.markdown(
        "Contas aguardando ativação e seus CS responsáveis. "
        "**Priorize o acompanhamento das contas de maior nível!**"
    )

    insights = r2.get("insights_onb", [])
    if not insights:
        st.info("Nenhuma conta pendente de onboarding.")
    else:
        for ins in insights:
            nivel    = ins["nivel"]
            onb      = ins["onb_nome"]
            qtd      = ins["qtd"]
            faltante = ins["gmv_faltante_total"]
            amount   = ins["amount_total"]

            icon = "🔴" if nivel in ("N6", "N7") else "🟡" if nivel in ("N4", "N5") else "🟢"
            msg = (
                f"{icon} **{qtd} conta(s) {nivel}** aguardando ativação "
                f"| CS: **{onb}** "
                f"| GMV faltante: **{fmt_currency(faltante)}** "
                f"| Volume total: {fmt_currency(amount)}"
            )
            st.info(msg)

    # Detalhes por nível (expandable)
    st.markdown("---")
    st.markdown("### 🔍 Detalhes por Nível")
    detalhes = r2.get("detalhes_por_nivel", {})
    for nivel in NIVEIS_ORDER:
        det = detalhes.get(nivel, {})
        cart = det.get("carteira", pd.DataFrame())
        atv  = det.get("ativar",   pd.DataFrame())
        won  = det.get("won",      pd.DataFrame())

        total_contas = len(cart) + len(atv) + len(won)
        if total_contas == 0:
            continue

        with st.expander(f"**{nivel}** — {total_contas} conta(s) no total"):
            c1, c2, c3 = st.columns(3)
            with c1:
                st.caption("📁 Na Carteira Ativa")
                if not cart.empty:
                    cols = ["Account Name"] + [c for c in ["GMV Total","Net Revenue","Months from Activation"] if c in cart.columns]
                    d = cart[cols].copy()
                    for col in ["GMV Total", "Net Revenue"]:
                        if col in d.columns:
                            d[col] = d[col].apply(fmt_currency)
                    st.dataframe(d, use_container_width=True, hide_index=True)
                else:
                    st.caption("Nenhuma conta.")

            with c2:
                st.caption("🔄 Para Ativar")
                if not atv.empty:
                    cols = ["Account Name"] + [c for c in ["Amount","GMV Faltante","Onb Nome","Onb Status"] if c in atv.columns]
                    d = atv[cols].copy()
                    for col in ["Amount","GMV Faltante"]:
                        if col in d.columns:
                            d[col] = d[col].apply(fmt_currency)
                    st.dataframe(d, use_container_width=True, hide_index=True)
                else:
                    st.caption("Nenhuma conta.")

            with c3:
                st.caption("⭐ Closed Won")
                if not won.empty:
                    cols = ["Account Name"] + [c for c in ["Opportunity Name","Amount"] if c in won.columns]
                    d = won[cols].copy()
                    if "Amount" in d.columns:
                        d["Amount"] = d["Amount"].apply(fmt_currency)
                    st.dataframe(d, use_container_width=True, hide_index=True)
                else:
                    st.caption("Nenhuma conta.")


# ── Tab 3 — Limbo ──────────────────────────────────────────────────────────────

def _tab_limbo(r3: dict):
    st.subheader("🚨 Alerta de Limbo — Contas sem Rastro no BI")

    count  = r3.get("total_limbo_count", 0)
    amount = r3.get("total_limbo_amount", 0.0)

    if count == 0:
        st.success(
            "✅ Nenhuma conta em limbo! Todos os Closed Won constam corretamente no BI."
        )
    else:
        st.error(
            f"🚨 **ALERTA CRÍTICO:** {count} conta(s) Closed Won **NÃO constam no BI** "
            f"(nem na Carteira Ativa, nem em Para Ativar).\n\n"
            f"Volume total em risco: **{fmt_currency(amount)}**"
        )

    st.markdown("---")
    st.markdown(
        """
        **Como interpretar:**
        - ✅ **Na Carteira Ativa** → Cliente ativado e gerando receita
        - 🔄 **Para Ativar** → Cliente fechado, aguardando atingir R$ 10k de GMV
        - 🚨 **Limbo** → Cliente Closed Won que **não aparece em nenhuma base do BI** — risco de perda de receita
        """
    )

    # Pivot de status
    pivot_count = r3.get("pivot_count")
    if pivot_count is not None and not pivot_count.empty:
        st.markdown("#### Distribuição de Closed Won por Nível × Status")
        st.dataframe(pivot_count, use_container_width=True, hide_index=True)

        # Gráfico de status
        won_class = r3.get("df_won_classificado")
        if won_class is not None and not won_class.empty and "Status" in won_class.columns:
            status_counts = won_class["Status"].value_counts().reset_index()
            status_counts.columns = ["Status", "Qtd"]
            fig_pie = px.pie(
                status_counts,
                values="Qtd",
                names="Status",
                title="Distribuição de Closed Won por Status",
                color="Status",
                color_discrete_map={
                    "Na Carteira Ativa": "#0066CC",
                    "Para Ativar":       "#F39C12",
                    "Limbo":             "#C0392B",
                },
            )
            st.plotly_chart(fig_pie, use_container_width=True)

    # Detalhes do Limbo
    limbo_df = r3.get("limbo_accounts")
    if limbo_df is not None and not limbo_df.empty:
        st.markdown("---")
        st.markdown("#### 📋 Lista Detalhada das Contas em Limbo")
        display = limbo_df.copy()
        if "Amount (R$)" in display.columns:
            display["Amount (R$)"] = display["Amount (R$)"].apply(fmt_currency)
        st.dataframe(display, use_container_width=True, hide_index=True)

        st.warning(
            "⚡ **Ação Recomendada:** Verifique com o time de CRM/Ops se esses clientes "
            "foram registrados corretamente no BI e acione o processo de ativação urgente."
        )
    elif count == 0:
        pass  # Já exibiu mensagem de sucesso acima
    else:
        st.info("Detalhes das contas em limbo não disponíveis.")


# ── Tab 4 — Carteira Lifecycle ──────────────────────────────────────────────────

def _tab_carteira(r1: dict):
    st.subheader("📁 Carteira Ativa — Lifecycle (Meses 0‒3)")
    st.markdown(
        "Um cliente gera receita para o SDR nos **4 primeiros meses de ativação** "
        "(Mês 0, 1, 2 e 3). Após o Mês 3, o cliente sai da carteira de geração de receita."
    )

    # Resumo por mês
    resumo = r1.get("df_resumo_por_mes")
    if resumo is not None and not resumo.empty:
        mes_labels = {0: "Mês 0 — Novo", 1: "Mês 1", 2: "Mês 2", 3: "Mês 3 (último mês)"}
        resumo_display = resumo.copy()
        resumo_display["Mês na Carteira"] = resumo_display["Mês na Carteira"].map(
            lambda x: mes_labels.get(x, f"Mês {x}")
        )
        resumo_display["NR Total (R$)"] = resumo_display["NR Total (R$)"].apply(fmt_currency)

        # Gráfico de barras por mês
        fig = px.bar(
            resumo,
            x="Mês na Carteira",
            y="NR Total (R$)",
            text="Qtd Clientes",
            title="Net Revenue por Mês de Lifecycle",
            color="Mês na Carteira",
            color_continuous_scale="Blues",
            labels={"NR Total (R$)": "NR (R$)", "Mês na Carteira": "Mês"},
        )
        fig.update_traces(texttemplate="%{text} clientes", textposition="outside")
        fig.update_layout(height=300, showlegend=False, xaxis_title="Mês na Carteira")
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(resumo_display, use_container_width=True, hide_index=True)

    st.markdown("---")

    # Saídas obrigatórias
    saindo = r1.get("df_carteira_saindo")
    if saindo is not None and not saindo.empty:
        st.error(
            f"⚠️ **{len(saindo)} cliente(s) saindo** do lifecycle — "
            "não contabilizam mais Net Revenue a partir deste mês."
        )
        cols_show = ["Account Name", "Net Revenue", "Months from Activation"]
        cols_show = [c for c in cols_show if c in saindo.columns]
        d = saindo[cols_show].copy()
        if "Net Revenue" in d.columns:
            d["Net Revenue"] = d["Net Revenue"].apply(fmt_currency)
        st.dataframe(d, use_container_width=True, hide_index=True)
    else:
        st.success("✅ Nenhum cliente saindo do lifecycle este mês.")

    st.markdown("---")

    # Detalhes da carteira ativa
    carteira = r1.get("df_carteira_ativa")
    if carteira is not None and not carteira.empty:
        with st.expander(f"🔍 Ver todos os {len(carteira)} clientes na carteira ativa"):
            cols_show = ["Account Name", "Net Revenue", "Take Rate", "Months from Activation"]
            if "Closer" in carteira.columns:
                cols_show = ["Closer"] + cols_show
            cols_show = [c for c in cols_show if c in carteira.columns]
            d = carteira[cols_show].copy()
            if "Net Revenue" in d.columns:
                d["Net Revenue"] = d["Net Revenue"].apply(fmt_currency)
            if "Take Rate" in d.columns:
                d["Take Rate"] = d["Take Rate"].apply(fmt_pct)
            st.dataframe(d, use_container_width=True, hide_index=True)
