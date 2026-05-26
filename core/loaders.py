import pandas as pd
import io
from core.validators import validate_columns, normalize_columns


# ── Utilitários ────────────────────────────────────────────────────────────────

def _read_file(file) -> pd.DataFrame:
    """Lê arquivo CSV ou Excel enviado via Streamlit file_uploader."""
    name = getattr(file, "name", "")
    content = file.read() if hasattr(file, "read") else file
    buf = io.BytesIO(content) if isinstance(content, bytes) else content

    if name.lower().endswith(".csv"):
        for sep in [",", ";", "\t"]:
            try:
                buf.seek(0)
                df = pd.read_csv(buf, sep=sep, encoding="utf-8")
                if df.shape[1] > 1:
                    return df
            except Exception:
                pass
        try:
            buf.seek(0)
            return pd.read_csv(buf, sep=",", encoding="latin-1")
        except Exception:
            buf.seek(0)
            return pd.read_csv(buf)
    else:
        buf.seek(0)
        xls = pd.ExcelFile(buf)
        return pd.read_excel(xls, sheet_name=xls.sheet_names[0])


def _to_float(df: pd.DataFrame, col: str) -> pd.DataFrame:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    return df


# ── Loaders específicos ────────────────────────────────────────────────────────

def load_carteira(file) -> pd.DataFrame:
    """
    Base 1 — Carteira Ativa (BI).
    Clientes que atingiram >= R$ 10.000 de GMV e estão nos 4 primeiros meses.
    Colunas principais: Closer, User ID, Account Name, Activation Date,
                        GMV Total, GMV RV, Net Revenue, Take Rate,
                        Months from Activation (0‒3).
    """
    df = normalize_columns(_read_file(file))
    validate_columns(df, "carteira")

    df = _to_float(df, "Net Revenue")
    df = _to_float(df, "GMV Total")
    df = _to_float(df, "GMV RV")

    if "Take Rate" in df.columns:
        df["Take Rate"] = pd.to_numeric(df["Take Rate"], errors="coerce").fillna(0.0)
        # Normaliza: se estiver em percentual (ex. 5.2 ao invés de 0.052), divide por 100
        if df["Take Rate"].max() > 1.0:
            df["Take Rate"] = df["Take Rate"] / 100.0
    else:
        df["Take Rate"] = 0.05  # take rate default 5%

    df["Months from Activation"] = (
        pd.to_numeric(df["Months from Activation"], errors="coerce")
        .fillna(0)
        .astype(int)
    )

    # Garante colunas de ID para cruzamento
    if "User ID" not in df.columns:
        df["User ID"] = ""

    return df.reset_index(drop=True)


def load_clientes_ativar(file) -> pd.DataFrame:
    """
    Base 2 — Para Ativar (BI).
    Clientes fechados que ainda não atingiram R$ 10.000 de GMV.
    Colunas: User ID, Account Name, CW Date, Amount,
             GMV Faltante, Onb Status, Onb Nome.
    """
    df = normalize_columns(_read_file(file))
    validate_columns(df, "ativar")

    df = _to_float(df, "Amount")
    df["GMV Faltante"] = pd.to_numeric(df["GMV Faltante"], errors="coerce")

    # Remove linhas onde GMV Faltante não está preenchido (fantasmas)
    df = df[df["GMV Faltante"].notna()].reset_index(drop=True)
    df["GMV Faltante"] = df["GMV Faltante"].astype(float)

    if "User ID" not in df.columns:
        df["User ID"] = ""
    if "Onb Nome" not in df.columns:
        df["Onb Nome"] = "N/D"
    if "Onb Status" not in df.columns:
        df["Onb Status"] = "N/D"

    return df


def load_crm(file) -> pd.DataFrame:
    """
    Base 3 — Oportunidades (Salesforce).
    Filtrada para Status = 'Closed Won'.
    Colunas: Opportunity Name, Account Name, Stage, Amount, Close Date.
    """
    df = normalize_columns(_read_file(file))
    validate_columns(df, "crm")

    df = _to_float(df, "Amount")

    if "Close Date" in df.columns:
        df["Close Date"] = pd.to_datetime(df["Close Date"], errors="coerce")

    if "Opportunity Name" not in df.columns:
        df["Opportunity Name"] = df["Account Name"]

    if "User ID" not in df.columns:
        df["User ID"] = ""

    # Filtra apenas Closed Won
    df_won = df[df["Stage"].apply(lambda s: str(s).strip().lower() in {
        "closed won", "won", "ganho", "fechado ganho"
    })].reset_index(drop=True)

    return df_won
