import streamlit as st
import numpy as np
import pandas as pd

from utils.session_loader import require_leads_df
from core.business_logic import apply_common_filters

try:
    import plotly.express as px
    HAS_PLOTLY = True
except Exception:
    HAS_PLOTLY = False

st.set_page_config(layout="wide")
st.title("🗺️ Analisi Territoriale Lead")

# =========================================================
# COORDINATE PROVINCE
# Estendi qui quando vuoi. Intanto ti lascio già molte sigle utili.
# =========================================================
PROVINCE_COORDS = {
    "AG": (37.3111, 13.5765),
    "AL": (44.9128, 8.6157),
    "AN": (43.6158, 13.5189),
    "AO": (45.7372, 7.3201),
    "AP": (42.8536, 13.5749),
    "AQ": (42.3498, 13.3995),
    "AR": (43.4633, 11.8796),
    "AT": (44.9008, 8.2064),
    "AV": (40.9149, 14.7924),
    "BA": (41.1171, 16.8719),
    "BG": (45.6983, 9.6773),
    "BI": (45.5628, 8.0583),
    "BL": (46.1408, 12.2156),
    "BN": (41.1298, 14.7826),
    "BO": (44.4949, 11.3426),
    "BR": (40.6327, 17.9418),
    "BS": (45.5416, 10.2118),
    "BT": (41.2000, 16.2000),
    "BZ": (46.4983, 11.3548),
    "CA": (39.2238, 9.1217),
    "CB": (41.5600, 14.6628),
    "CE": (41.0746, 14.3348),
    "CH": (42.3512, 14.1675),
    "CL": (37.4901, 14.0629),
    "CN": (44.3845, 7.5427),
    "CO": (45.8081, 9.0852),
    "CR": (45.1332, 10.0227),
    "CS": (39.2983, 16.2537),
    "CT": (37.5079, 15.0830),
    "CZ": (38.9098, 16.5877),
    "EN": (37.5676, 14.2794),
    "FC": (44.2227, 12.0407),
    "FE": (44.8381, 11.6198),
    "FG": (41.4622, 15.5446),
    "FI": (43.7696, 11.2558),
    "FM": (43.1606, 13.7181),
    "FR": (41.6396, 13.3426),
    "GE": (44.4056, 8.9463),
    "GO": (45.9402, 13.6202),
    "GR": (42.7635, 11.1124),
    "IM": (43.8899, 8.0392),
    "IS": (41.5892, 14.2307),
    "KR": (39.0808, 17.1220),
    "LC": (45.8566, 9.3977),
    "LE": (40.3515, 18.1750),
    "LI": (43.5485, 10.3106),
    "LO": (45.3145, 9.5035),
    "LT": (41.4676, 12.9037),
    "LU": (43.8429, 10.5027),
    "MB": (45.5845, 9.2730),
    "MC": (43.2988, 13.4534),
    "ME": (38.1938, 15.5540),
    "MI": (45.4642, 9.1900),
    "MN": (45.1564, 10.7914),
    "MO": (44.6471, 10.9252),
    "MS": (44.0354, 10.1417),
    "MT": (40.6663, 16.6043),
    "NA": (40.8518, 14.2681),
    "NO": (45.4450, 8.6222),
    "NU": (40.3211, 9.3309),
    "OR": (39.9036, 8.5920),
    "PA": (38.1157, 13.3615),
    "PC": (45.0526, 9.6930),
    "PD": (45.4064, 11.8768),
    "PE": (42.4618, 14.2161),
    "PG": (43.1107, 12.3908),
    "PI": (43.7228, 10.4017),
    "PN": (45.9564, 12.6600),
    "PO": (43.8777, 11.1022),
    "PR": (44.8015, 10.3279),
    "PT": (43.9333, 10.9167),
    "PU": (43.9100, 12.9130),
    "PV": (45.1847, 9.1582),
    "PZ": (40.6401, 15.8051),
    "RA": (44.4184, 12.2035),
    "RC": (38.1113, 15.6473),
    "RE": (44.6983, 10.6312),
    "RG": (36.9269, 14.7255),
    "RI": (42.4045, 12.8567),
    "RM": (41.9028, 12.4964),
    "RN": (44.0678, 12.5695),
    "RO": (45.0703, 11.7901),
    "SA": (40.6824, 14.7681),
    "SI": (43.3188, 11.3308),
    "SO": (46.1710, 9.8710),
    "SP": (44.1025, 9.8241),
    "SR": (37.0755, 15.2866),
    "SS": (40.7267, 8.5592),
    "SU": (39.1670, 8.5220),
    "SV": (44.3070, 8.4810),
    "TA": (40.4644, 17.2470),
    "TE": (42.6589, 13.7044),
    "TN": (46.0748, 11.1217),
    "TO": (45.0703, 7.6869),
    "TP": (38.0176, 12.5365),
    "TR": (42.5636, 12.6430),
    "TS": (45.6495, 13.7768),
    "TV": (45.6669, 12.2430),
    "UD": (46.0711, 13.2346),
    "VA": (45.8206, 8.8251),
    "VB": (45.9214, 8.5518),
    "VC": (45.3217, 8.4236),
    "VE": (45.4408, 12.3155),
    "VI": (45.5455, 11.5354),
    "VR": (45.4384, 10.9916),
    "VS": (39.7000, 8.7000),
    "VV": (38.6740, 16.1000),
}

# =========================================================
# HELPERS
# =========================================================
def pick_geo_columns(df: pd.DataFrame):
    """
    Se il dataframe è già arricchito usa le colonne mapped.
    Altrimenti fallback su provincia_norm.
    """
    sigla_col = None
    provincia_col = None
    regione_col = None

    if "sigla_provincia_mapped" in df.columns:
        sigla_col = "sigla_provincia_mapped"
    elif "provincia_norm" in df.columns:
        sigla_col = "provincia_norm"

    if "provincia_mapped" in df.columns:
        provincia_col = "provincia_mapped"
    elif "provincia_norm" in df.columns:
        provincia_col = "provincia_norm"

    if "regione_mapped" in df.columns:
        regione_col = "regione_mapped"
    elif "regione" in df.columns:
        regione_col = "regione"

    return sigla_col, provincia_col, regione_col


def pick_lead_id_column(df: pd.DataFrame):
    for c in ["id lead", "id_lead", "lead_id", "ID Lead", "Id Lead"]:
        if c in df.columns:
            return c
    return None


def pick_vendita_column(df: pd.DataFrame):
    for c in ["vendita", "Vendita", "is_vendita", "sale_flag"]:
        if c in df.columns:
            return c
    return None


def safe_numeric_sale(series: pd.Series):
    if series.dtype == bool:
        return series.astype(int)

    s = series.copy()

    # converte eventuali stringhe tipo SI/NO, TRUE/FALSE, 1/0
    if s.dtype == object:
        s = s.astype(str).str.strip().str.upper().replace({
            "SI": 1,
            "SÌ": 1,
            "YES": 1,
            "TRUE": 1,
            "1": 1,
            "NO": 0,
            "FALSE": 0,
            "0": 0,
            "NAN": np.nan,
            "NONE": np.nan,
            "": np.nan,
        })

    s = pd.to_numeric(s, errors="coerce").fillna(0)
    return s


# =========================================================
# LOAD DATA
# =========================================================
df = require_leads_df()

st.sidebar.header("Filtri")

mese_options = sorted(df["mese"].dropna().unique()) if "mese" in df.columns else []
segmento_options = sorted(df["segmento"].dropna().unique()) if "segmento" in df.columns else []

mese_sel = st.sidebar.multiselect(
    "Mese",
    options=mese_options,
    default=mese_options
)

segmento_sel = st.sidebar.multiselect(
    "Segmento",
    options=segmento_options,
    default=segmento_options
)

# Filtro opzionale regione se presente
sigla_col, provincia_col, regione_col = pick_geo_columns(df)

if regione_col and regione_col in df.columns:
    regioni_options = sorted(df[regione_col].dropna().unique())
    regione_sel = st.sidebar.multiselect(
        "Regione",
        options=regioni_options,
        default=regioni_options
    )
else:
    regione_sel = []

df_f = apply_common_filters(df, mesi=mese_sel, segmenti=segmento_sel)

if regione_sel and regione_col and regione_col in df_f.columns:
    df_f = df_f[df_f[regione_col].isin(regione_sel)]

# =========================================================
# VALIDAZIONE COLONNE
# =========================================================
lead_id_col = pick_lead_id_column(df_f)
vendita_col = pick_vendita_column(df_f)

if sigla_col is None:
    st.error(
        "Non trovo una colonna provincia utilizzabile. "
        "Serve almeno 'provincia_norm' oppure 'sigla_provincia_mapped'."
    )
    st.stop()

if lead_id_col is None:
    st.error(
        "Non trovo una colonna ID lead. Attese ad esempio: "
        "'id lead', 'id_lead', 'lead_id'."
    )
    st.stop()

if vendita_col is None:
    st.error(
        "Non trovo una colonna vendita. Attese ad esempio: "
        "'vendita', 'Vendita', 'is_vendita'."
    )
    st.stop()

# normalizzo vendita
df_f = df_f.copy()
df_f["_vendita_num"] = safe_numeric_sale(df_f[vendita_col])

# =========================================================
# AGGREGAZIONE PROVINCE
# =========================================================
group_cols = [sigla_col]
if provincia_col and provincia_col in df_f.columns and provincia_col != sigla_col:
    group_cols.append(provincia_col)
if regione_col and regione_col in df_f.columns:
    group_cols.append(regione_col)

prov_stats = (
    df_f.groupby(group_cols, dropna=False)
    .agg(
        lead=(lead_id_col, "count"),
        vendite=("_vendita_num", "sum")
    )
    .reset_index()
)

prov_stats["conversione"] = (
    prov_stats["vendite"] / prov_stats["lead"] * 100
).replace([np.inf, -np.inf], 0).fillna(0).round(1)

# colonne display pulite
# =========================================================
# COLONNE DISPLAY PULITE - VERSIONE SICURA
# =========================================================
rename_map = {}

if sigla_col and sigla_col in prov_stats.columns:
    rename_map[sigla_col] = "sigla_provincia"

# rinomina provincia solo se è una colonna diversa da sigla_col
if provincia_col and provincia_col in prov_stats.columns and provincia_col != sigla_col:
    rename_map[provincia_col] = "provincia"

# rinomina regione solo se esiste davvero ed è diversa dalle altre
if (
    regione_col
    and regione_col in prov_stats.columns
    and regione_col != sigla_col
    and regione_col != provincia_col
):
    rename_map[regione_col] = "regione"

prov_stats = prov_stats.rename(columns=rename_map)

# fallback sicuri
if "sigla_provincia" not in prov_stats.columns:
    prov_stats["sigla_provincia"] = None

if "provincia" not in prov_stats.columns:
    prov_stats["provincia"] = prov_stats["sigla_provincia"]

if "regione" not in prov_stats.columns:
    prov_stats["regione"] = None

# coordinate
prov_stats["lat"] = prov_stats["sigla_provincia"].map(
    lambda x: PROVINCE_COORDS.get(x, (None, None))[0]
)
prov_stats["lon"] = prov_stats["sigla_provincia"].map(
    lambda x: PROVINCE_COORDS.get(x, (None, None))[1]
)

# =========================================================
# KPI
# =========================================================
tot_lead = int(prov_stats["lead"].sum())
tot_vendite = int(prov_stats["vendite"].sum())
conv_media = round((tot_vendite / tot_lead * 100), 1) if tot_lead > 0 else 0.0
prov_attive = int(prov_stats["sigla_provincia"].nunique())

c1, c2, c3, c4 = st.columns(4)
c1.metric("Lead totali", f"{tot_lead:,}".replace(",", "."))
c2.metric("Vendite", f"{tot_vendite:,}".replace(",", "."))
c3.metric("Conversione media", f"{conv_media:.1f}%")
c4.metric("Province attive", f"{prov_attive:,}".replace(",", "."))

# =========================================================
# TABELLE
# =========================================================
tab1, tab2, tab3 = st.tabs([
    "📌 Ranking province",
    "🗺️ Mappa province",
    "🌍 Ranking regioni"
])

with tab1:
    ranking_province = prov_stats.sort_values(
        ["lead", "conversione"],
        ascending=[False, False]
    ).reset_index(drop=True)

    st.dataframe(
        ranking_province[
            ["sigla_provincia", "provincia", "regione", "lead", "vendite", "conversione"]
        ],
        use_container_width=True,
        hide_index=True
    )

with tab2:
    st.subheader("📍 Mappa Italia per provincia")

    mappa_df = prov_stats.dropna(subset=["lat", "lon"]).copy()

    if mappa_df.empty:
        st.warning("Non ci sono coordinate disponibili per le province filtrate.")
    elif HAS_PLOTLY:
        fig = px.scatter_mapbox(
            mappa_df,
            lat="lat",
            lon="lon",
            size="lead",
            color="conversione",
            hover_name="provincia",
            hover_data={
                "sigla_provincia": True,
                "regione": True,
                "lead": True,
                "vendite": True,
                "conversione": True,
                "lat": False,
                "lon": False,
            },
            color_continuous_scale="RdYlGn",
            zoom=5,
            height=620
        )
        fig.update_layout(
            mapbox_style="carto-positron",
            margin=dict(l=0, r=0, t=0, b=0)
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Plotly non installato: installa con `pip install plotly` per vedere la mappa.")

    missing_coords = prov_stats[prov_stats["lat"].isna() | prov_stats["lon"].isna()]
    if not missing_coords.empty:
        st.info("Alcune province non hanno coordinate nel dizionario e non compaiono sulla mappa.")
        st.dataframe(
            missing_coords[["sigla_provincia", "provincia", "regione", "lead"]],
            use_container_width=True,
            hide_index=True
        )

with tab3:
    if "regione" in prov_stats.columns and prov_stats["regione"].notna().any():
        reg_stats = (
            prov_stats.groupby("regione", dropna=False)
            .agg(
                lead=("lead", "sum"),
                vendite=("vendite", "sum")
            )
            .reset_index()
        )
        reg_stats["conversione"] = (
            reg_stats["vendite"] / reg_stats["lead"] * 100
        ).replace([np.inf, -np.inf], 0).fillna(0).round(1)

        reg_stats = reg_stats.sort_values(
            ["lead", "conversione"],
            ascending=[False, False]
        ).reset_index(drop=True)

        st.dataframe(
            reg_stats,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("La colonna regione non è disponibile nel dataset corrente.")