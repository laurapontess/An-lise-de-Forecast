ACTIVATION_THRESHOLD = 10_000   # GMV mínimo para ativar
MAX_LIFECYCLE_MONTH = 3         # Mês máximo de geração de receita (0, 1, 2, 3)
IDEAL_WALLET_SIZE = 17

META_WEIGHT_NR  = 0.60          # 60% peso em Net Revenue
META_WEIGHT_SQL = 0.40          # 40% peso em SQLs

# Tabela de classificação de Nível por faturamento / GMV / Amount
NIVEIS = {
    "N2": (100_000,        599_999.99),
    "N3": (600_000,        999_999.99),
    "N4": (1_000_000,    1_999_999.99),
    "N5": (2_000_000,    4_999_999.99),
    "N6": (5_000_000,    9_999_999.99),
    "N7": (10_000_000,   float("inf")),
}

NIVEIS_ORDER = ["N2", "N3", "N4", "N5", "N6", "N7"]

NIVEL_MIDPOINTS = {
    "N2":   350_000,
    "N3":   800_000,
    "N4": 1_500_000,
    "N5": 3_500_000,
    "N6": 7_500_000,
    "N7":15_000_000,
}

NIVEL_LABELS = {
    "N2": "N2 (R$100k–599k)",
    "N3": "N3 (R$600k–999k)",
    "N4": "N4 (R$1M–1,9M)",
    "N5": "N5 (R$2M–4,9M)",
    "N6": "N6 (R$5M–9,9M)",
    "N7": "N7 (R$10M+)",
}
