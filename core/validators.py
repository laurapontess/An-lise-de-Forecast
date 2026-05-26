import pandas as pd


# Colunas obrigatórias por base
REQUIRED_COLS = {
    "carteira": [
        "Account Name",
        "Net Revenue",
        "Months from Activation",
    ],
    "ativar": [
        "Account Name",
        "Amount",
        "GMV Faltante",
    ],
    "crm": [
        "Account Name",
        "Stage",
        "Amount",
    ],
}

# Colunas opcionais (enriquecimento)
OPTIONAL_COLS = {
    "carteira": ["User ID", "Closer", "GMV Total", "GMV RV", "Take Rate", "Activation Date"],
    "ativar":   ["User ID", "CW Date", "Onb Status", "Onb Nome"],
    "crm":      ["Opportunity Name", "Close Date", "User ID"],
}


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Remove espaços extras dos nomes de colunas."""
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    return df


def validate_columns(df: pd.DataFrame, sheet_key: str) -> None:
    """Levanta ValueError se faltar coluna obrigatória."""
    required = REQUIRED_COLS[sheet_key]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(
            f"Planilha '{sheet_key}' está faltando as colunas: {', '.join(missing)}. "
            f"Colunas encontradas: {', '.join(df.columns.tolist())}"
        )
