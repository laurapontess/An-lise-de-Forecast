import pandas as pd


REQUIRED_COLS = {
    "carteira": ["Account Name", "Net Revenue", "Months from Activation"],
    "ativar": ["Account Name", "Amount", "GMV Faltante"],
    "crm": ["Opportunity Name", "Account Name", "Stage", "Amount"],
}

OPTIONAL_COLS = {
    "carteira": ["GMV RV", "Take Rate"],
    "ativar": [],
    "crm": ["Close Date"],
}


def _normalize_col(col: str) -> str:
    return col.strip().lower().replace(" ", "_")


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [c.strip() for c in df.columns]
    return df


def validate_columns(df: pd.DataFrame, sheet_key: str) -> None:
    required = REQUIRED_COLS[sheet_key]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(
            f"Planilha '{sheet_key}' está faltando as colunas: {', '.join(missing)}"
        )
