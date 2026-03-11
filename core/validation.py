import pandas as pd


REQUIRED_COLUMNS = [
    "id lead",
    "stato",
    "data",
    "provincia",
    "fonte",
    "tipo_interesse",
    "brand",
    "reparto",
    "gestore",
    "intestatario",
    "is_deal",
    "mese",
]


def validate_required_columns(df: pd.DataFrame) -> list[str]:
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    return missing