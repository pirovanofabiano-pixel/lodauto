import streamlit as st
import numpy as np

from utils.session_loader import require_leads_df
from core.business_logic import apply_common_filters

try:
    import plotly.express as px
    HAS_PLOTLY = True
except Exception:
    HAS_PLOTLY = False

st.set_page_config(layout="wide")
st.title("🗺️ Analisi Territoriale Lead")

PROVINCE_COORDS = {
    "BG": (45.6983, 9.6773),
    "BS": (45.5416, 10.2118),
    "MI": (45.4642, 9.1900),
    "MB": (45.5845, 9.2730),
    "CO": (45.8081, 9.0852),
    "LC": (45.8566, 9.3977),
    "CR": (45.1332, 10.0227),
    "LO": (45.3145, 9.5035),
    "SO": (46.1710, 9.8710),
    "VA": (45.8206, 8.8251),
}

df = require_leads_df()

st.sidebar.header("Filtri")

mese_sel = st.sidebar.multiselect(
    "Mese",
    options=sorted(df["mese"].dropna().unique()),
    default=sorted(df["mese"].dropna().unique())
)

segmento_sel = st.sidebar.multiselect(
    "Segmento",
    options=sorted(df["segmento"].dropna().unique()),
    default=sorted(df["segmento"].dropna().unique())
)

df_f = apply_common_filters(df, mesi=mese_sel, segmenti=segmento_sel)

prov_stats = (
    df_f.groupby("provincia_norm")
    .agg(lead=("id lead", "count"), vendite=("vendita", "sum"))
    .reset_index()
)
prov_stats["conversione"] = (
    prov_stats["vendite"] / prov_stats["lead"] * 100
).replace([np.inf, -np.inf], 0).fillna(0).round(1)

st.subheader("📌 Ranking province")
st.dataframe(prov_stats.sort_values("lead", ascending=False), use_container_width=True)

st.subheader("📍 Mappa Lombardia")
prov_stats["lat"] = prov_stats["provincia_norm"].map(lambda x: PROVINCE_COORDS.get(x, (None, None))[0])
prov_stats["lon"] = prov_stats["provincia_norm"].map(lambda x: PROVINCE_COORDS.get(x, (None, None))[1])

if HAS_PLOTLY:
    fig = px.scatter_mapbox(
        prov_stats.dropna(subset=["lat", "lon"]),
        lat="lat",
        lon="lon",
        size="lead",
        color="conversione",
        hover_name="provincia_norm",
        hover_data=["lead", "vendite", "conversione"],
        color_continuous_scale="RdYlGn",
        zoom=7,
        height=520
    )
    fig.update_layout(mapbox_style="carto-positron")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("Plotly non installato: installa con `pip install plotly` per vedere la mappa.")