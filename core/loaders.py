import pandas as pd
import io
from core.validators import validate_columns, normalize_columns


def _read_file(file) -> pd.DataFrame:
    name = getattr(file, "name", "")
    content = file.read() if hasattr(file, "read") else file
    if isinstance(content, bytes):
        buf = io.BytesIO(content)
    else:
        buf = content

    if name.endswith(".csv"):
        for sep in [",", ";", "\t"]:
            try:
                buf.seek(0)
                df = pd.read_csv(buf, sep=sep)
                if df.shape[1] > 1:
                    return df
            except Exception:
                continue
        buf.seek(0)
        return pd.read_csv(buf)
    else:
        buf.seek(0)
        xls = pd.ExcelFile(buf)
        sheet = xls.sheet_names[0]
        return pd.read_excel(xls, sheet_name=sheet)


def load_carteira(file) -> pd.DataFrame:
    df = _read_file(file)
    df = normalize_columns(df)
    validate_columns(df, "carteira")

    df["Net Revenue"] = pd.to_numeric(df["Net Revenue"], errors="coerce").fillna(0)
    df["Months from Activation"] = pd.to_numeric(df["Months from Activation"], errors="coerce").fillna(0).astype(int)

    if "GMV RV" in df.columns:
        df["GMV RV"] = pd.to_numeric(df["GMV RV"], errors="coerce").fillna(0)
    if "Take Rate" in df.columns:
        df["Take Rate"] = pd.to_numeric(df["Take Rate"], errors="coerce").fillna(0)

    return df.reset_index(drop=True)


def load_clientes_ativar(file) -> pd.DataFrame:
    df = _read_file(file)
    df = normalize_columns(df)
    validate_columns(df, "ativar")

    df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce").fillna(0)
    df["GMV Faltante"] = pd.to_numeric(df["GMV Faltante"], errors="coerce")

    # Ghosting: remover linhas com GMV Faltante vazio
    df = df[df["GMV Faltante"].notna()].reset_index(drop=True)

    return df


def load_crm(file) -> pd.DataFrame:
    df = _read_file(file)
    df = normalize_columns(df)
    validate_columns(df, "crm")

    df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce").fillna(0)

    if "Close Date" in df.columns:
        df["Close Date"] = pd.to_datetime(df["Close Date"], errors="coerce")

    return df.reset_index(drop=True)
