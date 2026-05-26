"""
Gerador de PDF — Relatório Executivo de Forecast SDR

Usa ReportLab para criar um relatório formatado com:
  - Capa com dados do SDR
  - KPIs e análise de gap
  - Priorização por Nível (N2‒N7) nas 3 fases
  - Alertas de Limbo
  - Insights de CS (Onb Nome)
  - Rodapé de perfil
"""
import io
from datetime import date

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from utils.formatting import fmt_currency, fmt_pct, fmt_number

# ── Paleta de cores ────────────────────────────────────────────────────────────
AZUL_ESCURO  = colors.HexColor("#003B5C")
AZUL_MEDIO   = colors.HexColor("#0066CC")
AZUL_CLARO   = colors.HexColor("#E8F4FD")
VERDE        = colors.HexColor("#1A7F3C")
VERDE_CLARO  = colors.HexColor("#D4EDDA")
VERMELHO     = colors.HexColor("#C0392B")
VERMELHO_CLARO = colors.HexColor("#FADBD8")
AMARELO      = colors.HexColor("#F39C12")
AMARELO_CLARO= colors.HexColor("#FEF9E7")
CINZA_CLARO  = colors.HexColor("#F8F9FA")
CINZA_MEDIO  = colors.HexColor("#6C757D")
BRANCO       = colors.white
PRETO        = colors.black

PAGE_W, PAGE_H = A4
MARGIN = 2 * cm


# ── Styles ─────────────────────────────────────────────────────────────────────

def _build_styles():
    base = getSampleStyleSheet()
    styles = {
        "title": ParagraphStyle(
            "Title", parent=base["Title"],
            fontSize=26, textColor=AZUL_ESCURO,
            spaceAfter=6, alignment=TA_CENTER, leading=32,
        ),
        "subtitle": ParagraphStyle(
            "Subtitle", parent=base["Normal"],
            fontSize=13, textColor=AZUL_MEDIO,
            spaceAfter=4, alignment=TA_CENTER, leading=18,
        ),
        "h1": ParagraphStyle(
            "H1", parent=base["Heading1"],
            fontSize=14, textColor=BRANCO,
            spaceBefore=4, spaceAfter=4,
            backColor=AZUL_ESCURO, leading=20,
            leftIndent=-6, rightIndent=-6,
            borderPad=6,
        ),
        "h2": ParagraphStyle(
            "H2", parent=base["Heading2"],
            fontSize=12, textColor=AZUL_ESCURO,
            spaceBefore=10, spaceAfter=4, leading=16,
        ),
        "body": ParagraphStyle(
            "Body", parent=base["Normal"],
            fontSize=9, textColor=PRETO,
            spaceAfter=4, leading=13,
        ),
        "body_bold": ParagraphStyle(
            "BodyBold", parent=base["Normal"],
            fontSize=9, textColor=PRETO,
            spaceAfter=4, leading=13, fontName="Helvetica-Bold",
        ),
        "alert_red": ParagraphStyle(
            "AlertRed", parent=base["Normal"],
            fontSize=10, textColor=VERMELHO,
            spaceAfter=4, leading=14, fontName="Helvetica-Bold",
        ),
        "alert_green": ParagraphStyle(
            "AlertGreen", parent=base["Normal"],
            fontSize=10, textColor=VERDE,
            spaceAfter=4, leading=14, fontName="Helvetica-Bold",
        ),
        "caption": ParagraphStyle(
            "Caption", parent=base["Normal"],
            fontSize=8, textColor=CINZA_MEDIO,
            spaceAfter=2, leading=11, alignment=TA_CENTER,
        ),
        "footer": ParagraphStyle(
            "Footer", parent=base["Normal"],
            fontSize=8, textColor=CINZA_MEDIO,
            alignment=TA_RIGHT, leading=11,
        ),
    }
    return styles


# ── Componentes reutilizáveis ──────────────────────────────────────────────────

def _hr():
    return HRFlowable(width="100%", thickness=1, color=AZUL_ESCURO, spaceAfter=6)


def _spacer(h=0.3):
    return Spacer(1, h * cm)


def _section_title(text: str, styles: dict):
    return [
        _spacer(0.3),
        Paragraph(f"&nbsp;&nbsp;{text}", styles["h1"]),
        _spacer(0.2),
    ]


def _subsection_title(text: str, styles: dict):
    return [Paragraph(text, styles["h2"])]


def _kpi_table(kpis: list) -> Table:
    """
    kpis = [(label, value, bg_color), ...]
    Cria tabela de métricas horizontais.
    """
    n = len(kpis)
    header_row = [Paragraph(f"<b>{label}</b>", ParagraphStyle(
        "KpiH", fontSize=8, textColor=BRANCO, alignment=TA_CENTER,
        fontName="Helvetica-Bold",
    )) for label, _, _ in kpis]
    value_row  = [Paragraph(f"<b>{value}</b>", ParagraphStyle(
        "KpiV", fontSize=12, textColor=PRETO, alignment=TA_CENTER,
        fontName="Helvetica-Bold", leading=16,
    )) for _, value, _ in kpis]

    col_w = (PAGE_W - 2 * MARGIN) / n
    t = Table([header_row, value_row], colWidths=[col_w] * n, rowHeights=[20, 28])
    ts = [
        ("BACKGROUND", (0, 0), (-1, 0), AZUL_ESCURO),
        ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",   (0, 0), (-1, 0), 8),
        ("TEXTCOLOR",  (0, 0), (-1, 0), BRANCO),
        ("ALIGN",      (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
        ("GRID",       (0, 0), (-1, -1), 0.5, AZUL_MEDIO),
        ("ROWBACKGROUNDS", (0, 1), (-1, 1), [CINZA_CLARO]),
    ]
    for i, (_, _, bg) in enumerate(kpis):
        if bg:
            ts.append(("BACKGROUND", (i, 1), (i, 1), bg))
    t.setStyle(TableStyle(ts))
    return t


def _data_table(headers: list, rows: list, col_widths=None, stripe=True,
                header_bg=None, alert_col: int = None, alert_val: str = None) -> Table:
    """Cria tabela de dados formatada."""
    header_bg = header_bg or AZUL_MEDIO
    available = PAGE_W - 2 * MARGIN

    if col_widths is None:
        col_widths = [available / len(headers)] * len(headers)

    def _cell(txt, bold=False, align=TA_LEFT, size=8):
        style = ParagraphStyle(
            "Cell", fontSize=size, leading=12,
            fontName="Helvetica-Bold" if bold else "Helvetica",
            alignment=align,
        )
        return Paragraph(str(txt), style)

    header_cells = [_cell(h, bold=True, align=TA_CENTER) for h in headers]
    data = [header_cells]

    for i, row in enumerate(rows):
        bg = CINZA_CLARO if (stripe and i % 2 == 0) else BRANCO
        cells = []
        for j, val in enumerate(row):
            is_alert = (alert_col is not None and j == alert_col
                        and str(val) == alert_val)
            cells.append(_cell(val, bold=is_alert))
        data.append(cells)

    t = Table(data, colWidths=col_widths, repeatRows=1)
    ts = [
        ("BACKGROUND", (0, 0), (-1, 0), header_bg),
        ("TEXTCOLOR",  (0, 0), (-1, 0), BRANCO),
        ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",   (0, 0), (-1, 0), 8),
        ("ALIGN",      (0, 0), (-1, 0), "CENTER"),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
        ("GRID",       (0, 0), (-1, -1), 0.4, colors.HexColor("#CCCCCC")),
        ("FONTSIZE",   (0, 1), (-1, -1), 8),
    ]
    if stripe:
        for i in range(1, len(rows) + 1):
            bg = CINZA_CLARO if i % 2 == 0 else BRANCO
            ts.append(("BACKGROUND", (0, i), (-1, i), bg))

    t.setStyle(TableStyle(ts))
    return t


# ── Gerador principal ──────────────────────────────────────────────────────────

def gerar_pdf(ctx, r1: dict, r2: dict, r3: dict, r4: dict) -> bytes:
    """
    Retorna bytes do PDF pronto para download.
    ctx: SDRContext
    r1: resultado analise1_forecast
    r2: resultado analise2_segmentacao
    r3: resultado analise3_cruzamento
    r4: resultado analise4_simulacao (opcional, pode ser None)
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN, bottomMargin=MARGIN + 0.5 * cm,
        title=f"Forecast SDR — {ctx.nome}",
        author="Dashboard de Forecast SDR",
    )

    styles = _build_styles()
    story  = []

    # ══════════════════════════════════════════════════════════════════════════
    # CAPA
    # ══════════════════════════════════════════════════════════════════════════
    story += _capa(ctx, styles)
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # 1. ANÁLISE DE GAP & FORECAST
    # ══════════════════════════════════════════════════════════════════════════
    story += _section_title("1. Análise de Gap & Forecast do Mês", styles)
    story += _secao_gap(r1, styles)
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # 2. PRIORIZAÇÃO POR NÍVEL (N2‒N7)
    # ══════════════════════════════════════════════════════════════════════════
    story += _section_title("2. Priorização por Nível (N2‒N7)", styles)
    story += _secao_niveis(r2, styles)

    # ══════════════════════════════════════════════════════════════════════════
    # 3. ALERTA DE LIMBO
    # ══════════════════════════════════════════════════════════════════════════
    story.append(PageBreak())
    story += _section_title("3. ⚠️  Alerta de Limbo — Contas sem Rastro no BI", styles)
    story += _secao_limbo(r3, styles)

    # ══════════════════════════════════════════════════════════════════════════
    # 4. INSIGHTS DE CS / ONB NOME (Base 2)
    # ══════════════════════════════════════════════════════════════════════════
    story += _section_title("4. Dependências de Onboarding — Para Ativar", styles)
    story += _secao_onb(r2, styles)

    # ══════════════════════════════════════════════════════════════════════════
    # 5. CARTEIRA ATIVA — LIFECYCLE
    # ══════════════════════════════════════════════════════════════════════════
    story.append(PageBreak())
    story += _section_title("5. Carteira Ativa — Lifecycle (Meses 0‒3)", styles)
    story += _secao_carteira(r1, styles)

    # ══════════════════════════════════════════════════════════════════════════
    # RODAPÉ DE PERFIL
    # ══════════════════════════════════════════════════════════════════════════
    story += _rodape_perfil(ctx, r1, styles)

    doc.build(story)
    buf.seek(0)
    return buf.read()


# ── Seções ─────────────────────────────────────────────────────────────────────

def _capa(ctx, styles) -> list:
    el = []
    el.append(_spacer(3))
    el.append(Paragraph("📈 Análise de Forecast SDR", styles["title"]))
    el.append(_spacer(0.5))
    el.append(Paragraph(f"<b>{ctx.nome}</b>", styles["subtitle"]))
    el.append(Paragraph(f"{ctx.senioridade}  &bull;  {ctx.mes_referencia}", styles["subtitle"]))
    el.append(_spacer(1.5))

    # Metas em destaque
    meta_table = Table(
        [[
            Paragraph("<b>Meta Net Revenue</b>", ParagraphStyle(
                "MT", fontSize=11, textColor=BRANCO, alignment=TA_CENTER,
                fontName="Helvetica-Bold",
            )),
            Paragraph("<b>Meta SQLs</b>", ParagraphStyle(
                "MT", fontSize=11, textColor=BRANCO, alignment=TA_CENTER,
                fontName="Helvetica-Bold",
            )),
        ], [
            Paragraph(fmt_currency(ctx.meta_net_revenue), ParagraphStyle(
                "MV", fontSize=16, textColor=AZUL_ESCURO, alignment=TA_CENTER,
                fontName="Helvetica-Bold",
            )),
            Paragraph(str(ctx.meta_sqls), ParagraphStyle(
                "MV", fontSize=16, textColor=AZUL_ESCURO, alignment=TA_CENTER,
                fontName="Helvetica-Bold",
            )),
        ]],
        colWidths=[(PAGE_W - 2 * MARGIN) / 2] * 2,
        rowHeights=[25, 35],
    )
    meta_table.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, 0), AZUL_ESCURO),
        ("BACKGROUND",  (0, 1), (-1, 1), AZUL_CLARO),
        ("GRID",        (0, 0), (-1, -1), 0.5, AZUL_MEDIO),
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
    ]))
    el.append(meta_table)
    el.append(_spacer(3))
    el.append(Paragraph(
        f"Gerado em: {date.today().strftime('%d/%m/%Y')} &nbsp;&nbsp; | &nbsp;&nbsp; Reunião de 1:1",
        styles["caption"],
    ))
    return el


def _secao_gap(r1: dict, styles: dict) -> list:
    el = []

    ating = r1["ating_ponderado"]
    ating_nr  = r1["ating_nr"]
    ating_sql = r1["ating_sql"]

    # Cor do atingimento
    if ating >= 0.8:
        ating_bg, ating_str = VERDE_CLARO,     f"✅  {ating*100:.1f}%"
    elif ating >= 0.5:
        ating_bg, ating_str = AMARELO_CLARO,   f"⚠️  {ating*100:.1f}%"
    else:
        ating_bg, ating_str = VERMELHO_CLARO,  f"🔴  {ating*100:.1f}%"

    el.append(_kpi_table([
        ("NR Projetado (Carteira)",    fmt_currency(r1["nr_projetado"]),          None),
        ("NR Potencial (Ativação)",    fmt_currency(r1["nr_potencial_ativacao"]), None),
        ("SQLs Realizados",            str(r1["sqls_realizados"]),                None),
        ("Atingimento Ponderado",      ating_str,                                 ating_bg),
    ]))
    el.append(_spacer(0.5))

    # Detalhes do atingimento
    detail_table = _data_table(
        ["Indicador", "Realizado", "Meta", "Gap", "Atingimento", "Peso"],
        [
            [
                "Net Revenue",
                fmt_currency(r1["nr_projetado"]),
                fmt_currency(r1["meta_nr"]),
                fmt_currency(r1["gap_nr"]),
                fmt_pct(ating_nr),
                "60%",
            ],
            [
                "SQLs (Closed Won)",
                str(r1["sqls_realizados"]),
                str(r1["meta_sqls"]),
                str(r1["gap_sql"]),
                fmt_pct(ating_sql),
                "40%",
            ],
            [
                "TOTAL PONDERADO",
                "–",
                "100%",
                "–",
                f"{ating*100:.1f}%",
                "100%",
            ],
        ],
        col_widths=[
            4.5*cm, 3*cm, 3*cm, 3*cm, 2.5*cm, 1.5*cm,
        ],
    )
    el.append(detail_table)
    el.append(_spacer(0.5))

    # Mensagem de gap
    if r1["gap_nr"] > 0:
        el.append(Paragraph(
            f"⚡ Gap de Net Revenue: faltam <b>{fmt_currency(r1['gap_nr'])}</b> para atingir a meta.",
            styles["alert_red"],
        ))
    else:
        el.append(Paragraph(
            f"✅ Net Revenue: meta de {fmt_currency(r1['meta_nr'])} atingida!",
            styles["alert_green"],
        ))

    if r1["gap_sql"] > 0:
        el.append(Paragraph(
            f"⚡ Gap de SQLs: faltam <b>{r1['gap_sql']} SQL(s)</b> para atingir a meta "
            f"(realizados: {r1['sqls_realizados']} / meta: {r1['meta_sqls']}).",
            styles["alert_red"],
        ))
    else:
        el.append(Paragraph(
            f"✅ SQLs: meta de {r1['meta_sqls']} SQL(s) atingida!",
            styles["alert_green"],
        ))

    return el


def _secao_niveis(r2: dict, styles: dict) -> list:
    el = []

    for titulo, resumo_df, cor_header in [
        ("📁 Fase 1 — Na Carteira Ativa (Base 1 BI)",   r2["resumo_carteira"],  AZUL_MEDIO),
        ("🔄 Fase 2 — Para Ativar (Base 2 BI)",          r2["resumo_ativar"],    AMARELO),
        ("⭐ Fase 3 — Closed Won / SQLs (Salesforce)",    r2["resumo_crm_won"],   VERDE),
    ]:
        el += _subsection_title(titulo, styles)
        if resumo_df is not None and not resumo_df.empty:
            vol_col = [c for c in resumo_df.columns if "Volume" in c or "R$" in c]
            vol_col = vol_col[0] if vol_col else resumo_df.columns[-1]
            rows = [
                [
                    row["Nível"],
                    str(int(row["Qtd Contas"])),
                    fmt_currency(row[vol_col]),
                ]
                for _, row in resumo_df[resumo_df["Qtd Contas"] > 0].iterrows()
            ]
            if rows:
                t = _data_table(
                    ["Nível", "Qtd Contas", "Volume Total (R$)"],
                    rows,
                    col_widths=[4*cm, 5*cm, 8*cm],
                    header_bg=cor_header,
                )
                el.append(t)
            else:
                el.append(Paragraph("Nenhuma conta nesta fase.", styles["body"]))
        else:
            el.append(Paragraph("Dados não disponíveis.", styles["body"]))
        el.append(_spacer(0.4))

    return el


def _secao_limbo(r3: dict, styles: dict) -> list:
    el = []

    count  = r3.get("total_limbo_count", 0)
    amount = r3.get("total_limbo_amount", 0.0)

    if count == 0:
        el.append(Paragraph(
            "✅ Nenhuma conta em limbo detectada. Todos os Closed Won constam no BI.",
            styles["alert_green"],
        ))
        return el

    el.append(Paragraph(
        f"🚨 ALERTA CRÍTICO: {count} conta(s) Closed Won NÃO constam no BI "
        f"(nem na Carteira Ativa, nem em Para Ativar). "
        f"Volume total em risco: {fmt_currency(amount)}.",
        styles["alert_red"],
    ))
    el.append(_spacer(0.3))

    limbo_df = r3.get("limbo_accounts")
    if limbo_df is not None and not limbo_df.empty:
        cols = list(limbo_df.columns)
        rows = []
        for _, row in limbo_df.iterrows():
            r = [str(row[c]) if c not in ("Amount (R$)",) else fmt_currency(row[c])
                 for c in cols]
            rows.append(r)

        # Larguras dinâmicas
        avail = PAGE_W - 2 * MARGIN
        if len(cols) == 4:
            widths = [2.5*cm, 5*cm, 5*cm, 5*cm]
        else:
            widths = [avail / len(cols)] * len(cols)

        t = _data_table(cols, rows, col_widths=widths, header_bg=VERMELHO)
        el.append(t)
        el.append(_spacer(0.3))
        el.append(Paragraph(
            "Ação recomendada: verificar com o time de CRM/Ops se esses clientes "
            "foram registrados corretamente no BI e acionar o processo de ativação.",
            styles["body"],
        ))

    return el


def _secao_onb(r2: dict, styles: dict) -> list:
    el = []
    insights = r2.get("insights_onb", [])

    if not insights:
        el.append(Paragraph(
            "Nenhuma conta pendente de onboarding identificada.", styles["body"]
        ))
        return el

    el.append(Paragraph(
        "Contas aguardando ativação, agrupadas por nível e CS responsável (Onb Nome):",
        styles["body"],
    ))
    el.append(_spacer(0.2))

    rows = []
    for ins in insights:
        rows.append([
            ins["nivel"],
            str(ins["qtd"]),
            ins["onb_nome"],
            fmt_currency(ins["gmv_faltante_total"]),
            fmt_currency(ins["amount_total"]),
        ])

    t = _data_table(
        ["Nível", "Qtd Contas", "CS Responsável (Onb Nome)", "GMV Faltante Total", "Amount Total"],
        rows,
        col_widths=[2*cm, 2.5*cm, 5.5*cm, 4.5*cm, 4.5*cm],
        header_bg=AMARELO,
    )
    el.append(t)
    el.append(_spacer(0.3))

    # Insights textuais obrigatórios (spec)
    for ins in insights:
        nivel    = ins["nivel"]
        onb      = ins["onb_nome"]
        qtd      = ins["qtd"]
        faltante = ins["gmv_faltante_total"]
        texto = (
            f"Você tem <b>{qtd} conta(s) {nivel}</b> aguardando ativação, "
            f"que depende(m) do CS <b>{onb}</b>. "
            f"Faltam apenas <b>{fmt_currency(faltante)}</b> de GMV para ativarem."
        )
        el.append(Paragraph(f"• {texto}", styles["body"]))

    return el


def _secao_carteira(r1: dict, styles: dict) -> list:
    el = []

    resumo = r1.get("df_resumo_por_mes")
    if resumo is not None and not resumo.empty:
        el += _subsection_title("Clientes ativos por mês de lifecycle", styles)
        labels = {0: "Mês 0 — Novo", 1: "Mês 1", 2: "Mês 2", 3: "Mês 3 (último)"}
        rows = []
        for _, row in resumo.iterrows():
            mes = int(row["Mês na Carteira"])
            rows.append([
                labels.get(mes, f"Mês {mes}"),
                str(int(row["Qtd Clientes"])),
                fmt_currency(row["NR Total (R$)"]),
            ])
        t = _data_table(
            ["Mês na Carteira", "Qtd Clientes", "NR Total (R$)"],
            rows,
            col_widths=[7*cm, 5*cm, 7*cm],
        )
        el.append(t)
        el.append(_spacer(0.3))

    saindo = r1.get("df_carteira_saindo")
    if saindo is not None and not saindo.empty:
        el += _subsection_title("⚠️  Clientes saindo do lifecycle (após Mês 3)", styles)
        el.append(Paragraph(
            f"🔴 {len(saindo)} cliente(s) saindo — não contabilizam mais NR.",
            styles["alert_red"],
        ))
        cols_show = ["Account Name", "Net Revenue", "Months from Activation"]
        cols_show = [c for c in cols_show if c in saindo.columns]
        rows = [[str(row[c]) if "Revenue" not in c else fmt_currency(row[c])
                 for c in cols_show]
                for _, row in saindo.iterrows()]
        t = _data_table(cols_show, rows, header_bg=VERMELHO)
        el.append(t)

    return el


def _rodape_perfil(ctx, r1: dict, styles: dict) -> list:
    el = []
    el.append(PageBreak())
    el.append(_spacer(0.5))
    el.append(_hr())
    el.append(_spacer(0.2))

    footer_data = [
        [
            Paragraph("<b>SDR</b>", ParagraphStyle("FH", fontSize=9, textColor=AZUL_ESCURO, fontName="Helvetica-Bold")),
            Paragraph("<b>Senioridade</b>", ParagraphStyle("FH", fontSize=9, textColor=AZUL_ESCURO, fontName="Helvetica-Bold")),
            Paragraph("<b>Mês de Referência</b>", ParagraphStyle("FH", fontSize=9, textColor=AZUL_ESCURO, fontName="Helvetica-Bold")),
            Paragraph("<b>Meta NR</b>", ParagraphStyle("FH", fontSize=9, textColor=AZUL_ESCURO, fontName="Helvetica-Bold")),
            Paragraph("<b>Meta SQLs</b>", ParagraphStyle("FH", fontSize=9, textColor=AZUL_ESCURO, fontName="Helvetica-Bold")),
            Paragraph("<b>Atingimento</b>", ParagraphStyle("FH", fontSize=9, textColor=AZUL_ESCURO, fontName="Helvetica-Bold")),
        ],
        [
            Paragraph(ctx.nome, styles["body"]),
            Paragraph(ctx.senioridade, styles["body"]),
            Paragraph(ctx.mes_referencia, styles["body"]),
            Paragraph(fmt_currency(ctx.meta_net_revenue), styles["body"]),
            Paragraph(str(ctx.meta_sqls), styles["body"]),
            Paragraph(f"{r1['ating_ponderado']*100:.1f}%", styles["body_bold"]),
        ],
    ]

    avail = PAGE_W - 2 * MARGIN
    col_w = avail / 6
    t = Table(footer_data, colWidths=[col_w] * 6, rowHeights=[18, 18])
    t.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, 0), AZUL_CLARO),
        ("GRID",        (0, 0), (-1, -1), 0.4, AZUL_MEDIO),
        ("ALIGN",       (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
    ]))
    el.append(t)
    el.append(_spacer(0.3))
    el.append(Paragraph(
        f"Relatório gerado automaticamente pelo Dashboard de Forecast SDR "
        f"em {date.today().strftime('%d/%m/%Y')}.",
        styles["caption"],
    ))
    return el
