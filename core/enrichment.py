import re
import pandas as pd

from core.operational import add_operational_fields

# ======================================================
# MAPPING PROVINCE
# ======================================================
PROVINCE_MAP = {
    "BERGAMO": "BG",
    "BRESCIA": "BS",
    "MILANO": "MI",
    "MONZA": "MB",
    "MONZA BRIANZA": "MB",
    "COMO": "CO",
    "LECCO": "LC",
    "CREMONA": "CR",
    "LODI": "LO",
    "SONDRIO": "SO",
    "VARESE": "VA",
}

# ======================================================
# MAPPING STATO LEAD → LIVELLO OPERATIVO
# ======================================================
STATO_MAP_OPERATIVO = {
    "Non qualificato": "Non ancora gestito",
    "Lost": "Perso",
    "Annullato": "Perso",
    "Appuntamento": "Appuntamento",
    "Attesa risposta": "In attesa che il lead risponda",
    "trattativa": "Trattativa",
    "Deal": "Vendita",
    "Forza vendita": "In gestione al venditore",
    "No Show": "Non presentatosi all'appuntamento",
    "Non esiste": "Perso",
    "Non raggiungibile": "Perso",
    "Non risponde": "In gestione",
    "Preventivo": "Preventivo",
    "Qualificato": "In gestione",
    "Test drive": "In gestione",
}

# ======================================================
# MAPPING OPERATIVO → LIVELLO DIREZIONALE
# ======================================================
STATO_MAP_DIREZIONALE = {
    "Non ancora gestito": "Da gestire",
    "In gestione": "In lavorazione",
    "In attesa che il lead risponda": "In lavorazione",
    "Preventivo": "In lavorazione",
    "Trattativa": "In lavorazione",
    "In gestione al venditore": "In lavorazione",
    "Appuntamento": "Appuntamento",
    "Non presentatosi all'appuntamento": "Perso",
    "Vendita": "Vendita",
    "Perso": "Perso",
    "Altro": "Altro",
}

# ======================================================
# NORMALIZZAZIONE PROVINCIA
# ======================================================
def normalize_provincia(val):
    if pd.isna(val):
        return "ND"

    val = str(val).strip().upper()
    return PROVINCE_MAP.get(val, val)

# ======================================================
# HELPERS TESTO
# ======================================================
def normalize_text(val):
    if pd.isna(val):
        return ""
    return str(val).strip().lower()

def is_km0_text(text: str) -> bool:
    t = normalize_text(text)
    return ("km0" in t) or ("km 0" in t) or ("km-zero" in t) or ("km zero" in t)

# ======================================================
# CARLINE NORMALIZZATA
# usa la colonna modello ma la pulisce
# ======================================================

def normalize_carline(modello):
    if pd.isna(modello):
        return "Non definita"

    raw = str(modello).strip()
    m = raw.lower()

    # pulizia base
    m = m.replace("_", " ")
    m = m.replace("-", " ")
    m = re.sub(r"\s+", " ", m).strip()

    # --------------------------------------------------
    # EQA / EQB / EQE
    # --------------------------------------------------
    if re.search(r"\beqa\b", m):
        return "EQA"

    if re.search(r"\beqb\b", m):
        return "EQB"

    if re.search(r"\beqe\b", m):
        return "EQE"

    # --------------------------------------------------
    # GLA / GLB / GLC / GLE
    # --------------------------------------------------
    if re.search(r"\bgla\b", m):
        return "GLA"

    if re.search(r"\bglb\b", m):
        return "GLB"

    if re.search(r"\bglc\b", m):
        return "GLC"

    if re.search(r"\bgle\b", m):
        return "GLE"

    # --------------------------------------------------
    # CLASSE A
    # --------------------------------------------------
    if "mercedes-benz a-class" in m or "mercedes benz a class" in m:
        return "Classe A"

    if "a-class" in m or "a class" in m:
        return "Classe A"

    if "classe a berlina" in m:
        return "Classe A"

    if "classe a" in m:
        return "Classe A"

    if ("(w177)" in m or "(v177)" in m) and "classe a" in m:
        return "Classe A"

    if re.search(r"^a\s*\d{3}", m):
        return "Classe A"

    if re.search(r"\ba\s*\d{3}\b", m):
        return "Classe A"

    # --------------------------------------------------
    # CLASSE B
    # --------------------------------------------------
    if "mercedes-benz b-class" in m or "mercedes benz b class" in m:
        return "Classe B"

    if "b-class" in m or "b class" in m:
        return "Classe B"

    if "classe b" in m:
        return "Classe B"

    if re.search(r"^b\s*\d{3}", m):
        return "Classe B"

    if re.search(r"\bb\s*\d{3}\b", m):
        return "Classe B"

    # --------------------------------------------------
    # CLASSE C
    # --------------------------------------------------
    if "mercedes-benz c-class" in m or "mercedes benz c class" in m:
        return "Classe C"

    if "c-class" in m or "c class" in m:
        return "Classe C"

    if "classe c" in m:
        return "Classe C"

    if re.search(r"^c\s*\d{3}", m):
        return "Classe C"

    if re.search(r"\bc\s*\d{3}\b", m):
        return "Classe C"

    # --------------------------------------------------
    # CLASSE E
    # --------------------------------------------------
    if "mercedes-benz e-class" in m or "mercedes benz e class" in m:
        return "Classe E"

    if "e-class" in m or "e class" in m:
        return "Classe E"

    if "classe e" in m:
        return "Classe E"

    if re.search(r"^e\s*\d{3}", m):
        return "Classe E"

    if re.search(r"\be\s*\d{3}\b", m):
        return "Classe E"

    # --------------------------------------------------
    # CLA
    # IMPORTANTE: dopo Classe A, e con regex precisa
    # --------------------------------------------------
    if re.search(r"\bcla\b", m):
        return "CLA"

    # --------------------------------------------------
    # CLE
    # --------------------------------------------------
    if re.search(r"\bcle\b", m):
        return "CLE"

    # --------------------------------------------------
    # fallback
    # --------------------------------------------------
    return raw if raw else "Non definita"

# ======================================================
# CATEGORIA COMMERCIALE
# qui separiamo Nuovo / Km0 / Usato
# ======================================================
def build_categoria_commerciale(row):
    tipo_interesse = str(row.get("tipo_interesse", "")).strip()
    modello = str(row.get("modello", "")).strip()
    interesse_prodotto = str(row.get("interesse prodotto", "")).strip()

    testo = f"{modello} {interesse_prodotto}"

    if is_km0_text(testo):
        return "Km0"

    if tipo_interesse == "Usato":
        return "Usato"

    if tipo_interesse == "Nuovo":
        return "Nuovo"

    return "Altro"

# ======================================================
# SEGMENTO
# adesso usa anche Km0
# ======================================================
def build_segment(row):
    categoria = str(row.get("categoria_commerciale", "")).strip()
    brand = str(row.get("brand", "")).strip()

    if categoria == "Usato":
        return "Usato"

    if categoria == "Km0":
        if brand == "Mercedes":
            return "Km0 Mercedes"
        if brand == "Omoda / Jaecoo":
            return "Km0 Omoda / Jaecoo"
        return "Km0 Altro"

    if categoria == "Nuovo":
        if brand == "Mercedes":
            return "Nuovo Mercedes"
        if brand == "Omoda / Jaecoo":
            return "Nuovo Omoda / Jaecoo"
        return "Nuovo Altro"

    return "Altro"

# ======================================================
# NORMALIZZAZIONE STATO → OPERATIVO
# ======================================================
def normalize_stato_operativo(stato):
    if pd.isna(stato):
        return "Altro"

    s = str(stato).strip().lower()

    for raw_value, normalized in STATO_MAP_OPERATIVO.items():
        if str(raw_value).strip().lower() == s:
            return normalized

    for raw_value, normalized in STATO_MAP_OPERATIVO.items():
        if str(raw_value).strip().lower() in s:
            return normalized

    return "Altro"

# ======================================================
# OPERATIVO → DIREZIONALE
# ======================================================
def normalize_stato_direzionale(stato_operativo):
    if pd.isna(stato_operativo):
        return "Altro"

    s = str(stato_operativo).strip()
    return STATO_MAP_DIREZIONALE.get(s, "Altro")

# ======================================================
# STATO DIREZIONALE → FUNNEL
# ======================================================
def stato_direzionale_to_funnel(stato_direzionale):
    mapping = {
        "Da gestire": "📥 Da gestire",
        "In lavorazione": "🔄 In lavorazione",
        "Appuntamento": "📅 Appuntamento",
        "Vendita": "💰 Chiuso (Deal)",
        "Perso": "❌ Perso",
        "Altro": "🚨 Non assegnato / Bloccato",
    }
    return mapping.get(stato_direzionale, "🚨 Non assegnato / Bloccato")

# ======================================================
# FUNNEL BACKUP
# ======================================================
def classify_funnel(row):
    stato_dir = str(row.get("stato_norm_direzionale", "")).strip()
    if stato_dir:
        return stato_direzionale_to_funnel(stato_dir)

    stato = str(row.get("stato", "")).lower()
    reparto = str(row.get("reparto", "")).strip()

    if bool(row.get("is_deal", False)):
        return "💰 Chiuso (Deal)"

    if reparto == "BDC":
        return "📥 Da gestire"

    if reparto and reparto != "BDC" and reparto != "Altro / Non Mappato":
        return "🔄 In lavorazione"

    if any(k in stato for k in ["perso", "chiuso", "non interessato", "annullato", "lost"]):
        return "❌ Perso"

    return "🚨 Non assegnato / Bloccato"

# ======================================================
# ENRICHMENT COMPLETO
# ======================================================
def enrich_leads(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    # provincia
    if "provincia" in out.columns:
        out["provincia_norm"] = out["provincia"].apply(normalize_provincia)
    else:
        out["provincia_norm"] = "ND"

    # vendita
    if "is_deal" in out.columns:
        out["vendita"] = out["is_deal"].fillna(False).astype(bool).astype(int)
    else:
        out["vendita"] = 0

    # carline normalizzata da modello
    if "modello" in out.columns:
        out["carline"] = out["modello"].apply(normalize_carline)
    else:
        out["carline"] = "Non definita"

    # categoria commerciale
    out["categoria_commerciale"] = out.apply(build_categoria_commerciale, axis=1)

    # segmento
    out["segmento"] = out.apply(build_segment, axis=1)

    # stato operativo
    if "stato" in out.columns:
        out["stato_norm_operativo"] = out["stato"].apply(normalize_stato_operativo)
    else:
        out["stato_norm_operativo"] = "Altro"

    # stato direzionale
    out["stato_norm_direzionale"] = out["stato_norm_operativo"].apply(normalize_stato_direzionale)

    # compatibilità con vecchie pagine
    out["stato_norm"] = out["stato_norm_operativo"]

    # funnel
    out["fase_funnel"] = out.apply(classify_funnel, axis=1)

    # escludi walk-in
    if "fonte" in out.columns:
        out = out[out["fonte"].astype(str).str.strip().str.lower() != "walk-in"].copy()

    # lead girato ai venditori
    if "reparto" in out.columns:
        reparto_norm = out["reparto"].fillna("").astype(str).str.strip().str.lower()

        out["girato_venditori"] = (
            (reparto_norm != "")
            & (reparto_norm != "bdc")
            & (reparto_norm != "altro / non mappato")
        )
    else:
        out["girato_venditori"] = False

    # una vendita è per definizione passata dai venditori
    if "vendita" in out.columns:
        out.loc[out["vendita"] == 1, "girato_venditori"] = True    
    
    # campi operativi
    out = add_operational_fields(out)

    return out