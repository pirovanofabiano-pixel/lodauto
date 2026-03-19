import pandas as pd

from core.source_mapping import classify_source
from core.reparto_mapping import map_reparto


# ==========================================================
# COLUMN MAPPING (robusto: case-insensitive + pulizia)
# ==========================================================
COLUMN_MAP = {
    "data creazione": "data",
    "descrizione provenienza": "fonte_raw",
    "modello auto": "modello",
    "stato lead": "stato",
    "interesse": "interesse",
    "marca": "marca",
    "intestatario": "intestatario",
}


def clean_leads(df: pd.DataFrame) -> pd.DataFrame:
    # ======================================================
    # NORMALIZZA NOMI COLONNE
    # ======================================================
    df.columns = (
        df.columns
        .astype(str)
        .str.strip()
        .str.lower()
        .str.replace("\ufeff", "", regex=False)  # BOM
    )

    # ======================================================
    # RINOMINA COLONNE NOTE
    # ======================================================
    df = df.rename(columns={c: COLUMN_MAP[c] for c in df.columns if c in COLUMN_MAP})

    # ======================================================
    # CHECK COLONNE OBBLIGATORIE
    # ======================================================
    required = ["data", "fonte_raw", "stato", "interesse", "marca", "intestatario"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(
            f"Colonne mancanti nel CSV: {missing}\n"
            f"Colonne presenti: {list(df.columns)}"
        )

    # ======================================================
    # PARSING DATA (EU)
    # ======================================================
    df["data"] = pd.to_datetime(df["data"], dayfirst=True, errors="coerce")

    # ======================================================
    # FLAG VENDITA (Deal)
    # ======================================================
    df["is_deal"] = df["stato"].astype(str).str.strip().str.lower().eq("deal")

    # ======================================================
    # TIPO INTERESSE (Nuovo/Usato)
    # ======================================================
    def normalize_interest(val):
        if not isinstance(val, str):
            return "Altro"
        v = val.strip().lower()

        if v in ("nuovo", "nuovo/usato"):
            return "Nuovo"
        if v == "usato":
            return "Usato"
        return "Altro"

    df["tipo_interesse"] = df["interesse"].apply(normalize_interest)

    # ======================================================
    # BRAND (Mercedes vs Omoda/Jaecoo vs Altro)
    # ======================================================
    def normalize_brand(val):
        if not isinstance(val, str):
            return "Altro"
        v = val.strip().lower()

        if "mercedes" in v:
            return "Mercedes"
        if "omoda" in v or "jaecoo" in v:
            return "Omoda / Jaecoo"
        return "Altro"

    df["brand"] = df["marca"].apply(normalize_brand)

    # ======================================================
    # FONTE (AUTOMATICA DA PROVENIENZA RAW)
    # ======================================================
    df["fonte"] = df["fonte_raw"].apply(classify_source)

    # ======================================================
    # REPARTO + GESTORE (DA INTESTATARIO)
    # ======================================================
    df["reparto"], df["gestore"] = zip(*df["intestatario"].apply(map_reparto))

    # ======================================================
    # PERIODI
    # ======================================================
    df["mese"] = df["data"].dt.to_period("M").astype(str)
    df["settimana"] = df["data"].dt.to_period("W").astype(str)

    return df