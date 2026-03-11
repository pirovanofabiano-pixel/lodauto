import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

from core.loader import load_leads
from core.cleaning import clean_leads
from core.validation import validate_required_columns
from core.enrichment import enrich_leads
from core.metrics import overview_metrics
from core.forecasting import forecast
from core.whatif import what_if_simulation
from utils.session_loader import require_leads_df


st.set_page_config(page_title="Lead Analytics – Lodauto", layout="wide")
st.title("📊 Lead Analytics Dashboard")

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

df_f = df[
    df["mese"].isin(mese_sel)
    & df["tipo_interesse"].isin(tipo_interesse_sel)
    & df["brand"].isin(brand_sel)
].copy()

if df_f.empty:
    st.warning("⚠️ Nessun dato con i filtri selezionati.")
    st.stop()

metrics = overview_metrics(df_f)
c1, c2, c3 = st.columns(3)
c1.metric("Lead", metrics["lead"])
c2.metric("Vendite", metrics["vendite"])
c3.metric("Conversion %", f"{metrics['conversion_rate']}%")

st.sidebar.markdown("## 💰 Budget per Fonte")
budget = {
    f: st.sidebar.number_input(f, min_value=0, value=3000, step=500)
    for f in sorted(df_f["fonte"].dropna().unique())
}

st.subheader("💸 KPI per Fonte")

econ = []
for fonte, b in budget.items():
    d = df_f[df_f["fonte"] == fonte]
    lead = len(d)
    vendite = int(d["is_deal"].sum())

    econ.append({
        "Fonte": fonte,
        "Lead": lead,
        "Vendite": vendite,
        "Budget": b,
        "CPL": round(b / lead, 2) if lead else None,
        "CPA": round(b / vendite, 2) if vendite else None
    })

st.dataframe(pd.DataFrame(econ).sort_values("Lead", ascending=False), use_container_width=True)

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

st.subheader("🧠 What-if Budget")
st.dataframe(what_if_simulation(df_f, budget, baseline_budget=3000), use_container_width=True)

st.subheader("📤 Export")
st.download_button(
    "Scarica CSV Analizzato",
    df_f.to_csv(index=False),
    file_name="lead_analizzati.csv",
    mime="text/csv"
)