import os
import re
import unicodedata
import pandas as pd
import streamlit as st


# =========================================================
# CONFIG
# =========================================================
COMUNI_MAPPING_PATH = "data/lodanalyst_comuni_italia_province_istat_2026-02-21.csv"


# =========================================================
# NORMALIZZAZIONE TESTI
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


COMUNE_ALIASES = {
    "REGGIO EMILIA": "REGGIO NELL EMILIA",
    "BOLZANO": "BOLZANO BOZEN",
    "MONZA BRIANZA": "MONZA",
    "VERBANIA CUSIO OSSOLA": "VERBANIA",
    "FORLI CESENA": "FORLI",
    "PESARO URBINO": "PESARO",
    "MASSA CARRARA": "MASSA",
    "AOSTA VALLEE D AOSTE": "AOSTA",
}


def normalize_comune(value):
    s = normalize_text(value)
    if not s:
        return None
    return COMUNE_ALIASES.get(s, s)


def normalize_sigla_provincia(value):
    s = normalize_text(value)
    if not s:
        return None

    s = s.replace("PROVINCIA DI ", "")
    s = s.replace("CITTA METROPOLITANA DI ", "")
    s = s.strip()

    if len(s) == 2:
        return s

    return s


# =========================================================
# RICONOSCIMENTO AUTOMATICO COLONNE
# =========================================================
def find_best_column(df, candidates):
    normalized_map = {normalize_text(c): c for c in df.columns}
    for cand in candidates:
        nc = normalize_text(cand)
        if nc in normalized_map:
            return normalized_map[nc]
    return None


def detect_geo_columns(df):
    comune_candidates = [
        "Comune", "Città", "Citta", "City", "Località", "Localita",
        "Comune Residenza", "Comune Cliente", "Residenza", "Paese"
    ]

    provincia_candidates = [
        "Provincia", "Prov", "Sigla Provincia", "Provincia Cliente",
        "Provincia Residenza", "PR", "Prov."
    ]

    regione_candidates = [
        "Regione", "Region"
    ]

    comune_col = find_best_column(df, comune_candidates)
    provincia_col = find_best_column(df, provincia_candidates)
    regione_col = find_best_column(df, regione_candidates)

    return {
        "comune_col": comune_col,
        "provincia_col": provincia_col,
        "regione_col": regione_col,
    }


# =========================================================
# CARICAMENTO MAPPING COMUNI
# =========================================================
@st.cache_data(show_spinner=False)
def load_comuni_mapping(mapping_path):
    if not os.path.exists(mapping_path):
        raise FileNotFoundError(
            f"File mapping comuni non trovato: {mapping_path}"
        )

    comuni = pd.read_csv(mapping_path, dtype=str)

    required_cols = [
        "comune",
        "comune_italiano",
        "comune_normalized",
        "provincia",
        "sigla_provincia",
        "regione",
        "codice_istat_comune",
        "codice_catastale",
        "codice_uts_provincia",
        "is_capoluogo",
    ]

    missing = [c for c in required_cols if c not in comuni.columns]
    if missing:
        raise ValueError(f"Nel mapping mancano queste colonne: {missing}")

    comuni["comune_normalized"] = comuni["comune_normalized"].apply(normalize_comune)
    comuni["sigla_provincia"] = comuni["sigla_provincia"].apply(normalize_sigla_provincia)
    comuni["provincia_normalized"] = comuni["provincia"].apply(normalize_text)

    return comuni


# =========================================================
# MAPPATURA GEOGRAFICA
# =========================================================
def enrich_leads_with_geography(df, mapping_path=COMUNI_MAPPING_PATH):
    out = df.copy()

    detected = detect_geo_columns(out)
    comune_col = detected["comune_col"]
    provincia_col = detected["provincia_col"]

    if not comune_col:
        raise ValueError(
            "Non sono riuscito a trovare automaticamente la colonna del comune. "
            "Aggiungi una colonna tipo 'Comune' oppure imposta manualmente il nome."
        )

    comuni_map = load_comuni_mapping(mapping_path)

    out["comune_input_raw"] = out[comune_col]
    out["comune_normalized"] = out[comune_col].apply(normalize_comune)

    if provincia_col and provincia_col in out.columns:
        out["provincia_input_raw"] = out[provincia_col]
        out["provincia_input_normalized"] = out[provincia_col].apply(normalize_text)
        out["sigla_provincia_input_normalized"] = out[provincia_col].apply(normalize_sigla_provincia)
    else:
        out["provincia_input_raw"] = None
        out["provincia_input_normalized"] = None
        out["sigla_provincia_input_normalized"] = None

    # -----------------------------------------------------
    # MATCH BASE su comune_normalized
    # -----------------------------------------------------
    base_map = comuni_map[
        [
            "comune_normalized",
            "comune",
            "comune_italiano",
            "provincia",
            "sigla_provincia",
            "regione",
            "codice_istat_comune",
            "codice_catastale",
            "codice_uts_provincia",
            "is_capoluogo",
        ]
    ].drop_duplicates(subset=["comune_normalized"])

    out = out.merge(
        base_map,
        how="left",
        on="comune_normalized",
        suffixes=("", "_map"),
    )

    # -----------------------------------------------------
    # FALLBACK su comune + sigla provincia input
    # -----------------------------------------------------
    if provincia_col and provincia_col in out.columns:
        multi_map = comuni_map[
            [
                "comune_normalized",
                "sigla_provincia",
                "comune",
                "comune_italiano",
                "provincia",
                "regione",
                "codice_istat_comune",
                "codice_catastale",
                "codice_uts_provincia",
                "is_capoluogo",
            ]
        ].drop_duplicates()

        missing_mask = (
            out["regione"].isna()
            & out["comune_normalized"].notna()
            & out["sigla_provincia_input_normalized"].notna()
        )

        if missing_mask.any():
            fallback_source = out.loc[
                missing_mask,
                ["comune_normalized", "sigla_provincia_input_normalized"]
            ].copy()

            fallback_match = fallback_source.merge(
                multi_map,
                how="left",
                left_on=["comune_normalized", "sigla_provincia_input_normalized"],
                right_on=["comune_normalized", "sigla_provincia"],
            )

            fill_cols = [
                "comune",
                "comune_italiano",
                "provincia",
                "sigla_provincia",
                "regione",
                "codice_istat_comune",
                "codice_catastale",
                "codice_uts_provincia",
                "is_capoluogo",
            ]

            for col in fill_cols:
                out.loc[missing_mask, col] = fallback_match[col].values

    out = out.rename(columns={
        "comune": "comune_mapped",
        "comune_italiano": "comune_italiano_mapped",
        "provincia": "provincia_mapped",
        "sigla_provincia": "sigla_provincia_mapped",
        "regione": "regione_mapped",
    })

    out["match_geo_status"] = "NO_MATCH"
    out.loc[out["comune_normalized"].isna(), "match_geo_status"] = "COMUNE_VUOTO"
    out.loc[out["regione_mapped"].notna(), "match_geo_status"] = "MATCH_OK"

    out["match_geo_corrected"] = (
        out["match_geo_status"].eq("MATCH_OK")
        & out["comune_input_raw"].fillna("").astype(str).str.strip().ne(
            out["comune_mapped"].fillna("").astype(str).str.strip()
        )
    )

    return out


# =========================================================
# TABELLE AGGREGATE
# =========================================================
def build_geo_summary_tables(df_geo):
    matched = df_geo[df_geo["match_geo_status"] == "MATCH_OK"].copy()

    province_table = (
        matched.groupby(
            ["sigla_provincia_mapped", "provincia_mapped", "regione_mapped"],
            dropna=False
        )
        .size()
        .reset_index(name="lead")
        .sort_values(["lead", "provincia_mapped"], ascending=[False, True])
    )

    regioni_table = (
        matched.groupby("regione_mapped", dropna=False)
        .size()
        .reset_index(name="lead")
        .sort_values(["lead", "regione_mapped"], ascending=[False, True])
    )

    non_trovati = (
        df_geo[df_geo["match_geo_status"] != "MATCH_OK"][
            ["comune_input_raw", "provincia_input_raw", "comune_normalized", "match_geo_status"]
        ]
        .drop_duplicates()
        .sort_values(["match_geo_status", "comune_input_raw"], ascending=[True, True])
    )

    return province_table, regioni_table, non_trovati


# =========================================================
# UI STREAMLIT GEO
# =========================================================
def render_geo_mapping_section(df):
    st.markdown("## Mappatura geografica comuni → province → regioni")

    try:
        df_geo = enrich_leads_with_geography(df, COMUNI_MAPPING_PATH)
    except Exception as e:
        st.error(f"Errore nella mappatura geografica: {e}")
        return df

    total_rows = len(df_geo)
    matched_rows = int((df_geo["match_geo_status"] == "MATCH_OK").sum())
    no_match_rows = int((df_geo["match_geo_status"] == "NO_MATCH").sum())
    empty_rows = int((df_geo["match_geo_status"] == "COMUNE_VUOTO").sum())
    match_rate = (matched_rows / total_rows * 100) if total_rows else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Lead totali", f"{total_rows:,}".replace(",", "."))
    c2.metric("Match OK", f"{matched_rows:,}".replace(",", "."))
    c3.metric("Non trovati", f"{no_match_rows:,}".replace(",", "."))
    c4.metric("Match rate", f"{match_rate:.1f}%")

    if empty_rows > 0:
        st.info(f"Righe con comune vuoto: {empty_rows:,}".replace(",", "."))

    province_table, regioni_table, non_trovati = build_geo_summary_tables(df_geo)

    tab1, tab2, tab3, tab4 = st.tabs([
        "Lead per provincia",
        "Lead per regione",
        "Non mappati",
        "Dataset arricchito"
    ])

    with tab1:
        st.dataframe(province_table, use_container_width=True, hide_index=True)

        csv_province = province_table.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "Scarica CSV lead per provincia",
            data=csv_province,
            file_name="lead_per_provincia.csv",
            mime="text/csv",
            key="download_lead_per_provincia"
        )

    with tab2:
        st.dataframe(regioni_table, use_container_width=True, hide_index=True)

        csv_regioni = regioni_table.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "Scarica CSV lead per regione",
            data=csv_regioni,
            file_name="lead_per_regione.csv",
            mime="text/csv",
            key="download_lead_per_regione"
        )

    with tab3:
        st.dataframe(non_trovati, use_container_width=True, hide_index=True)

        csv_non_trovati = non_trovati.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "Scarica CSV non mappati",
            data=csv_non_trovati,
            file_name="lead_non_mappati.csv",
            mime="text/csv",
            key="download_non_mappati"
        )

    with tab4:
        cols_to_show = [
            c for c in [
                "comune_input_raw",
                "provincia_input_raw",
                "comune_normalized",
                "comune_mapped",
                "provincia_mapped",
                "sigla_provincia_mapped",
                "regione_mapped",
                "codice_istat_comune",
                "codice_catastale",
                "match_geo_status",
                "match_geo_corrected"
            ] if c in df_geo.columns
        ]
        st.dataframe(df_geo[cols_to_show], use_container_width=True, hide_index=True)

    return df_geo

st.set_page_config(page_title="Lodanalyst", layout="wide")
st.title("Lodanalyst")
st.write("Seleziona una pagina dal menu laterale.")