ACTIVATION_THRESHOLD = 10_000
MAX_MONTHS_IN_WALLET = 3
IDEAL_WALLET_SIZE = 17
META_WEIGHT_NR = 0.6
META_WEIGHT_SQL = 0.4

NIVEIS = {
    "N1": (0, 99_999.99),
    "N2": (100_000, 599_999.99),
    "N3": (600_000, 999_999.99),
    "N4": (1_000_000, 1_999_999.99),
    "N5": (2_000_000, 4_999_999.99),
    "N6": (5_000_000, 9_999_999.99),
    "N7": (10_000_000, float("inf")),
}

NIVEL_MIDPOINTS = {
    "N1": 50_000,
    "N2": 350_000,
    "N3": 800_000,
    "N4": 1_500_000,
    "N5": 3_500_000,
    "N6": 7_500_000,
    "N7": 15_000_000,
}

STAGES_PIPELINE = {"Qualifying", "Proposal", "Negotiation", "SQL", "Prospecção", "Proposta", "Negociação"}
STAGES_WON = {"Closed Won"}
STAGES_LOST = {"Closed Lost"}

PROB_ATIVACAO_MAP = [
    (0, 0.95),
    (2_000, 0.70),
    (5_000, 0.45),
    (10_000, 0.20),
    (float("inf"), 0.05),
]
