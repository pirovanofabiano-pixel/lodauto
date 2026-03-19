import os
import re
import unicodedata
import pandas as pd


COMUNI_MAPPING_PATH = "data/lodanalyst_comuni_italia_province_istat_2026-02-21.csv"

# Se in futuro vuoi aggiungere un mapping CAP -> provincia dedicato,
# salva un CSV qui dentro con almeno:
# cap,sigla_provincia,provincia
CAP_MAPPING_PATH = "data/lodanalyst_cap_province.csv"


# =========================================================
# NORMALIZZAZIONE
# =========================================================
def normalize_text(value):
    if pd.isna(value):
        return None

    s = str(value).strip().upper()
    if not s:
        return None

    s = s.replace("’", "'").replace("`", "'").replace("´", "'")

    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))

    s = s.replace("-", " ").replace("/", " ").replace("\\", " ")
    s = s.replace("'", " ")

    s = re.sub(r"[^A-Z0-9\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()

    return s or None


def normalize_cap(value):
    if pd.isna(value):
        return None

    s = str(value).strip()
    if not s:
        return None

    s = re.sub(r"\D", "", s)
    if len(s) == 5:
        return s

    return None


def normalize_sigla_provincia(value):
    if pd.isna(value):
        return None

    raw = str(value).strip()
    if not raw:
        return None

    s = normalize_text(raw)
    if not s:
        return None

    nd_values = {
        "N D", "ND", "N D.", "N.D", "N.D.", "NON DISPONIBILE",
        "SCONOSCIUTO", "NONE", "NULL", "NAN"
    }
    if s in nd_values:
        return None

    s = s.replace("PROVINCIA DI ", "").replace("CITTA METROPOLITANA DI ", "").strip()

    if len(s) == 2:
        return s

    # mapping nomi estesi -> sigla
    province_name_to_sigla = {
        "BERGAMO": "BG",
        "BRESCIA": "BS",
        "MILANO": "MI",
        "MONZA E DELLA BRIANZA": "MB",
        "MONZA BRIANZA": "MB",
        "COMO": "CO",
        "LECCO": "LC",
        "CREMONA": "CR",
        "LODI": "LO",
        "SONDRIO": "SO",
        "VARESE": "VA",
        "ROMA": "RM",
        "TORINO": "TO",
        "NAPOLI": "NA",
        "VERONA": "VR",
        "VICENZA": "VI",
        "PADOVA": "PD",
        "TREVISO": "TV",
        "VENEZIA": "VE",
        "BOLOGNA": "BO",
        "MODENA": "MO",
        "REGGIO NELL EMILIA": "RE",
        "REGGIO EMILIA": "RE",
        "PARMA": "PR",
        "RAVENNA": "RA",
        "RIMINI": "RN",
        "FORLI CESENA": "FC",
        "FIRENZE": "FI",
        "PISA": "PI",
        "LIVORNO": "LI",
        "LUCCA": "LU",
        "SIENA": "SI",
        "AREZZO": "AR",
        "PAVIA": "PV",
        "NOVARA": "NO",
        "CUNEO": "CN",
        "GENOVA": "GE",
        "IMPERIA": "IM",
        "SAVONA": "SV",
        "LA SPEZIA": "SP",
        "TRENTO": "TN",
        "BOLZANO": "BZ",
        "BOLZANO BOZEN": "BZ",
        "AOSTA": "AO",
        "PESARO E URBINO": "PU",
        "PESARO URBINO": "PU",
        "PERUGIA": "PG",
        "TERNI": "TR",
        "ANCONA": "AN",
        "MACERATA": "MC",
        "ASCOLI PICENO": "AP",
        "FERMO": "FM",
        "LATINA": "LT",
        "FROSINONE": "FR",
        "SALERNO": "SA",
        "BARI": "BA",
        "LECCE": "LE",
        "FOGGIA": "FG",
        "TARANTO": "TA",
        "BRINDISI": "BR",
        "COSENZA": "CS",
        "CATANZARO": "CZ",
        "REGGIO CALABRIA": "RC",
        "PALERMO": "PA",
        "CATANIA": "CT",
        "MESSINA": "ME",
        "TRAPANI": "TP",
        "CAGLIARI": "CA",
        "SASSARI": "SS",
    }

    return province_name_to_sigla.get(s, None)


# =========================================================
# DETECTION COLONNE
# =========================================================
def _normalized_columns_map(df):
    return {normalize_text(col): col for col in df.columns}


def find_best_column(df, candidates):
    norm_map = _normalized_columns_map(df)
    for cand in candidates:
        nc = normalize_text(cand)
        if nc in norm_map:
            return norm_map[nc]
    return None


def detect_geo_input_columns(df):
    provincia_candidates = [
        "provincia",
        "provincia lead",
        "provincia cliente",
        "provincia provenienza",
        "provincia di provenienza",
        "sigla provincia",
        "prov",
        "prov."
    ]

    citta_candidates = [
        "città",
        "citta",
        "city",
        "comune",
        "comune cliente",
        "comune lead",
        "località",
        "localita",
        "paese"
    ]

    cap_candidates = [
        "cap",
        "cap cliente",
        "cap lead",
        "zip",
        "postal code",
        "postcode"
    ]

    return {
        "provincia_col": find_best_column(df, provincia_candidates),
        "citta_col": find_best_column(df, citta_candidates),
        "cap_col": find_best_column(df, cap_candidates),
    }


# =========================================================
# LOAD MAPPING
# =========================================================
def load_comuni_mapping(mapping_path=COMUNI_MAPPING_PATH):
    if not os.path.exists(mapping_path):
        raise FileNotFoundError(f"File mapping comuni non trovato: {mapping_path}")

    comuni = pd.read_csv(mapping_path, dtype=str)

    required_cols = ["comune_normalized", "provincia", "sigla_provincia"]
    missing = [c for c in required_cols if c not in comuni.columns]
    if missing:
        raise ValueError(f"Nel mapping comuni mancano queste colonne: {missing}")

    comuni["comune_normalized"] = comuni["comune_normalized"].apply(normalize_text)
    comuni["sigla_provincia"] = comuni["sigla_provincia"].apply(normalize_sigla_provincia)
    comuni["provincia"] = comuni["provincia"].astype(str).str.strip()

    return comuni


def load_cap_mapping(cap_mapping_path=CAP_MAPPING_PATH):
    if not os.path.exists(cap_mapping_path):
        return None

    cap_map = pd.read_csv(cap_mapping_path, dtype=str)

    required_cols = ["cap", "sigla_provincia", "provincia"]
    missing = [c for c in required_cols if c not in cap_map.columns]
    if missing:
        return None

    cap_map["cap"] = cap_map["cap"].apply(normalize_cap)
    cap_map["sigla_provincia"] = cap_map["sigla_provincia"].apply(normalize_sigla_provincia)
    cap_map["provincia"] = cap_map["provincia"].astype(str).str.strip()

    cap_map = cap_map.dropna(subset=["cap", "sigla_provincia"])
    cap_map = cap_map.drop_duplicates(subset=["cap"])

    return cap_map


# =========================================================
# ENRICHMENT
# =========================================================
def enrich_province_from_geo_fields(
    df,
    comuni_mapping_path=COMUNI_MAPPING_PATH,
    cap_mapping_path=CAP_MAPPING_PATH,
):
    """
    Priorità:
    1) provincia input valida
    2) CAP, se esiste mapping CAP
    3) città/comune
    4) N.D.
    """
    out = df.copy()

    detected = detect_geo_input_columns(out)
    provincia_col = detected["provincia_col"]
    citta_col = detected["citta_col"]
    cap_col = detected["cap_col"]

    # colonne raw
    out["provincia_input_raw"] = out[provincia_col] if provincia_col in out.columns else None
    out["citta_input_raw"] = out[citta_col] if citta_col in out.columns else None
    out["cap_input_raw"] = out[cap_col] if cap_col in out.columns else None

    # colonne normalizzate
    out["provincia_input_norm"] = out["provincia_input_raw"].apply(normalize_sigla_provincia)
    out["citta_norm"] = out["citta_input_raw"].apply(normalize_text)
    out["cap_norm"] = out["cap_input_raw"].apply(normalize_cap)

    # base output
    out["provincia_norm"] = out["provincia_input_norm"]
    out["provincia_fill_source"] = "input"

    # -----------------------------------------------------
    # fallback CAP
    # -----------------------------------------------------
    cap_map = load_cap_mapping(cap_mapping_path)
    if cap_map is not None:
        cap_map = cap_map.rename(columns={
            "sigla_provincia": "_sigla_provincia_da_cap",
            "provincia": "_provincia_nome_da_cap",
        })

        out = out.merge(
            cap_map[["cap", "_sigla_provincia_da_cap", "_provincia_nome_da_cap"]],
            how="left",
            left_on="cap_norm",
            right_on="cap"
        )

        mask = out["provincia_norm"].isna() & out["_sigla_provincia_da_cap"].notna()
        out.loc[mask, "provincia_norm"] = out.loc[mask, "_sigla_provincia_da_cap"]
        out.loc[mask, "provincia_fill_source"] = "cap"
    else:
        out["_sigla_provincia_da_cap"] = None
        out["_provincia_nome_da_cap"] = None

    # -----------------------------------------------------
    # fallback CITTA
    # -----------------------------------------------------
    comuni_map = load_comuni_mapping(comuni_mapping_path)

    city_map = (
        comuni_map[["comune_normalized", "sigla_provincia", "provincia"]]
        .dropna(subset=["comune_normalized", "sigla_provincia"])
        .drop_duplicates(subset=["comune_normalized"])
        .rename(columns={
            "sigla_provincia": "_sigla_provincia_da_citta",
            "provincia": "_provincia_nome_da_citta",
        })
    )

    out = out.merge(
        city_map,
        how="left",
        left_on="citta_norm",
        right_on="comune_normalized"
    )

    mask = out["provincia_norm"].isna() & out["_sigla_provincia_da_citta"].notna()
    out.loc[mask, "provincia_norm"] = out.loc[mask, "_sigla_provincia_da_citta"]
    out.loc[mask, "provincia_fill_source"] = "citta"

    # -----------------------------------------------------
    # default finale
    # -----------------------------------------------------
    out.loc[out["provincia_norm"].isna(), "provincia_norm"] = "N.D."
    out.loc[out["provincia_norm"].eq("N.D."), "provincia_fill_source"] = "nd"

    # nome provincia finale
    out["provincia_nome"] = None

    if "_provincia_nome_da_cap" in out.columns:
        mask_cap = out["provincia_fill_source"].eq("cap")
        out.loc[mask_cap, "provincia_nome"] = out.loc[mask_cap, "_provincia_nome_da_cap"]

    mask_city = out["provincia_fill_source"].eq("citta")
    out.loc[mask_city, "provincia_nome"] = out.loc[mask_city, "_provincia_nome_da_citta"]

    # se la provincia arrivava già in input, provo a ricavare il nome da comuni_map
    sigla_to_name = (
        comuni_map[["sigla_provincia", "provincia"]]
        .dropna()
        .drop_duplicates(subset=["sigla_provincia"])
        .set_index("sigla_provincia")["provincia"]
        .to_dict()
    )

    mask_input = out["provincia_fill_source"].eq("input")
    out.loc[mask_input, "provincia_nome"] = out.loc[mask_input, "provincia_norm"].map(sigla_to_name)

    return out


# =========================================================
# FUNZIONE UNICA DA USARE IN LODANALYST
# =========================================================
def prepare_leads_df_for_lodanalyst(df):
    """
    Funzione unica: la lanci dopo il pd.read_csv(...)
    e ti restituisce il dataframe con provincia_norm valorizzata meglio.
    """
    out = df.copy()
    out = enrich_province_from_geo_fields(out)

    # colonna finale di compatibilità con il progetto
    out["provincia_norm"] = out["provincia_norm"].fillna("N.D.")

    return out