import pandas as pd
from utils.constants import NIVEIS, NIVEL_MIDPOINTS, PROB_ATIVACAO_MAP


def classificar_nivel(amount: float) -> str:
    if pd.isna(amount) or amount < 0:
        return "N1"
    for nivel, (low, high) in reversed(list(NIVEIS.items())):
        if low <= amount <= high:
            return nivel
    return "N1"


def calcular_prob_ativacao(gmv_faltante: float) -> float:
    for threshold, prob in PROB_ATIVACAO_MAP:
        if gmv_faltante <= threshold:
            return prob
    return 0.05


def is_won(stage: str) -> bool:
    return str(stage).strip().lower() in {"closed won", "won", "ganho"}


def is_lost(stage: str) -> bool:
    return str(stage).strip().lower() in {"closed lost", "lost", "perdido"}


def is_pipeline(stage: str) -> bool:
    return not is_won(stage) and not is_lost(stage)
