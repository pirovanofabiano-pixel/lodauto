import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

from core.loader import load_leads
from core.cleaning import clean_leads
from core.validation import validate_required_columns
from core.enrichment import enrich_leads
from core.metrics import overview_metrics, by_carline_metrics
from core.forecasting import forecast
from core.whatif import what_if_simulation
from utils.session_loader import require_leads_df


st.set_page_config(page_title="Lead Analyst – Lodauto", layout="wide")
st.title("📊 Lead Analyst Dashboard")


# ======================================================
# HELPER KPI PER FONTE
# ======================================================
def build_kpi_per_fonte(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()

    # --------------------------------------------------
    # vendita
    # --------------------------------------------------
    if "vendita" in d.columns:
        d["vendita_calc"] = d["vendita"].fillna(0).astype(int)
    elif "is_deal" in d.columns:
        d["vendita_calc"] = d["is_deal"].fillna(False).astype(bool).astype(int)
    else:
        d["vendita_calc"] = 0

    # --------------------------------------------------
    # lead chiuso
    # --------------------------------------------------
    if "lead_aperto" in d.columns:
        d["lead_chiuso_calc"] = ~d["lead_aperto"].fillna(False).astype(bool)
    elif "stato_norm_direzionale" in d.columns:
        d["lead_chiuso_calc"] = d["stato_norm_direzionale"].fillna("").isin(
            ["Vendita", "Perso", "Altro"]
        )
    else:
        d["lead_chiuso_calc"] = False

    # --------------------------------------------------
    # girato ai venditori
    # --------------------------------------------------
    if "girato_venditori" in d.columns:
        d["girato_venditori_calc"] = d["girato_venditori"].fillna(False).astype(bool)
    else:
        d["girato_venditori_calc"] = False

    # --------------------------------------------------
    # classificazioni
    # --------------------------------------------------
    d["perso_dal_bdc"] = (
        d["lead_chiuso_calc"]
        & (~d["girato_venditori_calc"])
        & (d["vendita_calc"] == 0)
    )

    d["perso_dai_venditori"] = (
        d["lead_chiuso_calc"]
        & d["girato_venditori_calc"]
        & (d["vendita_calc"] == 0)
    )

    d["vendita_flag"] = d["vendita_calc"] == 1

    # --------------------------------------------------
    # aggregazione
    # --------------------------------------------------
    kpi = (
        d.groupby("fonte")
        .agg(
            Lead_ricevuti=("fonte", "count"),
            Persi_dal_BDC=("perso_dal_bdc", "sum"),
            Girati_ai_venditori=("girato_venditori_calc", "sum"),
            Persi_dai_venditori=("perso_dai_venditori", "sum"),
            Vendite=("vendita_flag", "sum"),
        )
        .reset_index()
        .rename(columns={
            "fonte": "Fonte",
            "Lead_ricevuti": "Lead ricevuti",
            "Persi_dal_BDC": "Persi dal BDC",
            "Girati_ai_venditori": "Girati ai venditori",
            "Persi_dai_venditori": "Persi dai venditori",
        })
    )

    # --------------------------------------------------
    # percentuali numeriche
    # --------------------------------------------------
    kpi["pct_girati_ai_venditori_num"] = (
        kpi["Girati ai venditori"] / kpi["Lead ricevuti"].replace(0, pd.NA) * 100
    ).round(1).fillna(0)

    kpi["pct_chiusura_bdc_num"] = (
        kpi["Persi dal BDC"] / kpi["Lead ricevuti"].replace(0, pd.NA) * 100
    ).round(1).fillna(0)

    kpi["pct_conversione_venditori_sui_girati_num"] = (
        kpi["Vendite"] / kpi["Girati ai venditori"].replace(0, pd.NA) * 100
    ).round(1).fillna(0)

    kpi["pct_conversione_totale_num"] = (
        kpi["Vendite"] / kpi["Lead ricevuti"].replace(0, pd.NA) * 100
    ).round(1).fillna(0)

    # --------------------------------------------------
    # diagnosi fonte
    # --------------------------------------------------
    def diagnose_row(row):
        pct_girati = row["pct_girati_ai_venditori_num"]
        pct_bdc = row["pct_chiusura_bdc_num"]
        pct_conv_vend = row["pct_conversione_venditori_sui_girati_num"]
        pct_conv_tot = row["pct_conversione_totale_num"]

        if pct_conv_tot >= 5 and pct_bdc < 35 and pct_girati >= 50:
            return "🟢 Fonte sana"

        if pct_bdc > 45:
            return "🔴 BDC filtra troppo / lead poco qualificati"

        if pct_girati < 40:
            return "🔴 Pochi lead passati ai venditori"

        if pct_girati >= 40 and pct_conv_vend < 40:
            return "🟡 Buon filtro BDC, ma poca resa venditori"

        return "🟡 Da monitorare"

    kpi["Diagnosi Fonte"] = kpi.apply(diagnose_row, axis=1)

    # --------------------------------------------------
    # percentuali formattate
    # --------------------------------------------------
    kpi["% girati ai venditori"] = kpi["pct_girati_ai_venditori_num"].astype(str) + "%"
    kpi["% chiusura BDC"] = kpi["pct_chiusura_bdc_num"].astype(str) + "%"
    kpi["% conversione venditori sui girati"] = (
        kpi["pct_conversione_venditori_sui_girati_num"].astype(str) + "%"
    )
    kpi["% conversione totale"] = kpi["pct_conversione_totale_num"].astype(str) + "%"

    # --------------------------------------------------
    # ordine colonne finale
    # --------------------------------------------------
    kpi = kpi[
        [
            "Fonte",
            "Lead ricevuti",
            "Persi dal BDC",
            "Girati ai venditori",
            "Persi dai venditori",
            "Vendite",
            "% girati ai venditori",
            "% chiusura BDC",
            "% conversione venditori sui girati",
            "% conversione totale",
            "Diagnosi Fonte",
            "pct_girati_ai_venditori_num",
            "pct_chiusura_bdc_num",
            "pct_conversione_venditori_sui_girati_num",
            "pct_conversione_totale_num",
        ]
    ]

    return kpi.sort_values("Lead ricevuti", ascending=False)


# ======================================================
# COLORI KPI
# ======================================================
def color_percent_positive(val):
    if pd.isna(val):
        return ""

    try:
        num = float(str(val).replace("%", "").replace(",", "."))
    except Exception:
        return ""

    if num >= 50:
        return "background-color:#d4edda; color:#155724;"
    elif num >= 40:
        return "background-color:#fff3cd; color:#856404;"
    else:
        return "background-color:#f8d7da; color:#721c24;"


def color_percent_conversion(val):
    if pd.isna(val):
        return ""

    try:
        num = float(str(val).replace("%", "").replace(",", "."))
    except Exception:
        return ""

    if num >= 5:
        return "background-color:#d4edda; color:#155724;"
    elif num >= 3:
        return "background-color:#fff3cd; color:#856404;"
    else:
        return "background-color:#f8d7da; color:#721c24;"


def color_percent_bdc(val):
    if pd.isna(val):
        return ""

    try:
        num = float(str(val).replace("%", "").replace(",", "."))
    except Exception:
        return ""

    if num < 35:
        return "background-color:#d4edda; color:#155724;"
    elif num <= 45:
        return "background-color:#fff3cd; color:#856404;"
    else:
        return "background-color:#f8d7da; color:#721c24;"


def color_diagnosi(val):
    text = str(val)

    if "🟢" in text:
        return "background-color:#d4edda; color:#155724; font-weight:bold;"
    if "🟡" in text:
        return "background-color:#fff3cd; color:#856404; font-weight:bold;"
    if "🔴" in text:
        return "background-color:#f8d7da; color:#721c24; font-weight:bold;"

    return ""


# ======================================================
# UPLOAD CSV (SOLO QUI)
# ======================================================
uploaded_file = st.file_uploader("Carica il CSV Lead", type="csv")

if uploaded_file is not None:
    raw_df = load_leads(uploaded_file)
    clean_df = clean_leads(raw_df)

    missing = validate_required_columns(clean_df)
    if missing:
        st.error("❌ Nel CSV mancano queste colonne obbligatorie:")
        st.write(missing)
        st.stop()

    enriched_df = enrich_leads(clean_df)
    st.session_state["df_leads"] = enriched_df
    st.success(f"CSV caricato correttamente ({len(enriched_df)} lead)")

df = require_leads_df()

# ======================================================
# FILTRI
# ======================================================
st.sidebar.header("🎯 Filtri")

mese_sel = st.sidebar.multiselect(
    "Mese",
    options=sorted(df["mese"].dropna().unique()),
    default=sorted(df["mese"].dropna().unique())
)

tipo_interesse_sel = st.sidebar.multiselect(
    "Tipo Interesse",
    options=sorted(df["tipo_interesse"].dropna().unique()),
    default=sorted(df["tipo_interesse"].dropna().unique())
)

brand_sel = st.sidebar.multiselect(
    "Brand",
    options=sorted(df["brand"].dropna().unique()),
    default=sorted(df["brand"].dropna().unique())
)

carline_sel = st.sidebar.multiselect(
    "Carline",
    options=sorted(df["carline"].dropna().unique()),
    default=sorted(df["carline"].dropna().unique())
)

stato_dir_sel = st.sidebar.multiselect(
    "Stato direzionale",
    options=sorted(df["stato_norm_direzionale"].dropna().unique()),
    default=sorted(df["stato_norm_direzionale"].dropna().unique())
)

df_f = df[
    df["mese"].isin(mese_sel)
    & df["tipo_interesse"].isin(tipo_interesse_sel)
    & df["brand"].isin(brand_sel)
    & df["carline"].isin(carline_sel)
    & df["stato_norm_direzionale"].isin(stato_dir_sel)
].copy()

if df_f.empty:
    st.warning("⚠️ Nessun dato con i filtri selezionati.")
    st.stop()

# ======================================================
# KPI
# ======================================================
metrics = overview_metrics(df_f)

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Lead", metrics["lead"])
c2.metric("Vendite", metrics["vendite"])
c3.metric("Conversion % Totale", f"{metrics['conversion_rate']}%")
c4.metric("Lead girati ai venditori", metrics["lead_girati_venditori"])
c5.metric("Conversione Venditori %", f"{metrics['conversione_venditori']}%")

# ======================================================
# CONFRONTO MESE SU MESE
# ======================================================
st.subheader("📅 Confronto Mese su Mese")

monthly_cmp = df_f.groupby("mese").agg(
    Lead=("stato", "count"),
    Deal=("is_deal", "sum")
).reset_index()

monthly_cmp["Conversion %"] = (
    monthly_cmp["Deal"] / monthly_cmp["Lead"].replace(0, pd.NA) * 100
).round(2).fillna(0)

st.dataframe(monthly_cmp.sort_values("mese"), use_container_width=True)

# ======================================================
# BUDGET PER WHAT-IF
# ======================================================
st.sidebar.markdown("## 💰 Budget per Fonte")

budget = {
    f: st.sidebar.number_input(
        f"Budget {f}",
        min_value=0,
        value=3000,
        step=500
    )
    for f in sorted(df_f["fonte"].dropna().unique())
}

# ======================================================
# KPI PER FONTE
# ======================================================
st.subheader("📌 KPI per Fonte")

kpi_fonte = build_kpi_per_fonte(df_f)

display_cols = [
    "Fonte",
    "Lead ricevuti",
    "Persi dal BDC",
    "Girati ai venditori",
    "Persi dai venditori",
    "Vendite",
    "% girati ai venditori",
    "% chiusura BDC",
    "% conversione venditori sui girati",
    "% conversione totale",
    "Diagnosi Fonte",
]

styled_kpi_fonte = (
    kpi_fonte[display_cols]
    .style
    .map(
        color_percent_positive,
        subset=[
            "% girati ai venditori",
            "% conversione venditori sui girati",
        ],
    )
    .map(
        color_percent_conversion,
        subset=[
            "% conversione totale",
        ],
    )
    .map(
        color_percent_bdc,
        subset=[
            "% chiusura BDC",
        ],
    )
    .map(
        color_diagnosi,
        subset=[
            "Diagnosi Fonte",
        ],
    )
)

st.write(styled_kpi_fonte)

# ======================================================
# FUNNEL DIREZIONALE
# ======================================================
st.subheader("🧭 Funnel Direzionale")

funnel = (
    df_f.groupby("fase_funnel")
    .size()
    .reset_index(name="Lead")
    .sort_values("Lead", ascending=False)
)
st.dataframe(funnel, use_container_width=True)

# ======================================================
# STATO DIREZIONALE
# ======================================================
st.subheader("📊 Stato Direzionale")

stato_dir = (
    df_f.groupby("stato_norm_direzionale")
    .size()
    .reset_index(name="Lead")
    .sort_values("Lead", ascending=False)
)
st.dataframe(stato_dir, use_container_width=True)

# ======================================================
# PERFORMANCE PER CARLINE
# ======================================================
st.subheader("🚘 Performance per Carline")

carline_df = by_carline_metrics(df_f)
st.dataframe(carline_df, use_container_width=True)

# ======================================================
# FORECAST
# ======================================================
st.subheader("🔮 Forecast Lead")

monthly = df_f.groupby("mese").size()
pred = forecast(monthly)

if pred is None:
    st.info("Dati insufficienti per forecast.")
else:
    fig, ax = plt.subplots()
    monthly.plot(ax=ax, marker="o", label="Storico")
    ax.plot(range(len(monthly), len(monthly) + len(pred)), pred, "--o", label="Forecast")
    ax.legend()
    ax.set_xlabel("Mese")
    ax.set_ylabel("Lead")
    st.pyplot(fig)

# ======================================================
# WHAT-IF
# ======================================================
st.subheader("🧠 What-if Budget")
st.dataframe(
    what_if_simulation(df_f, budget, baseline_budget=3000),
    use_container_width=True
)

# ======================================================
# DEBUG UTILE
# ======================================================
with st.expander("🔍 Verifica colonne arricchite"):
    check_cols = [
        "stato",
        "stato_norm_operativo",
        "stato_norm_direzionale",
        "fase_funnel",
        "lead_aperto",
        "priorita_operativa",
        "is_deal",
        "vendita",
        "girato_venditori",
        "fonte",
        "reparto",
    ]
    check_cols = [c for c in check_cols if c in df_f.columns]
    st.dataframe(df_f[check_cols].head(20), use_container_width=True)

# ======================================================
# EXPORT
# ======================================================
st.subheader("📤 Export")

st.download_button(
    "Scarica CSV Analizzato",
    df_f.to_csv(index=False),
    file_name="lead_analizzati.csv",
    mime="text/csv"
)