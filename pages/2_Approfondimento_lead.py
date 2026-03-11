import streamlit as st
import pandas as pd

from utils.session_loader import require_leads_df
from core.business_logic import apply_common_filters
from core.metrics import by_month_metrics, by_segment_metrics
from core.metrics import by_carline_metrics


st.set_page_config(layout="wide")
st.title("🔎 Approfondimento Lead – Gestione Operativa")

df = require_leads_df()

# ======================================================
# FILTRI
# ======================================================
st.sidebar.header("🎯 Filtri")

carline_sel = st.sidebar.multiselect(
    "Carline",
    options=sorted(df["carline"].dropna().unique()),
    default=sorted(df["carline"].dropna().unique())
)

mese_sel = st.sidebar.multiselect(
    "Mese",
    options=sorted(df["mese"].dropna().unique()),
    default=sorted(df["mese"].dropna().unique())
)

segmento_sel = st.sidebar.multiselect(
    "Tipo di interesse (segmento)",
    options=sorted(df["segmento"].dropna().unique()),
    default=sorted(df["segmento"].dropna().unique())
)

fonte_sel = st.sidebar.multiselect(
    "Fonte",
    options=sorted(df["fonte"].dropna().unique()),
    default=sorted(df["fonte"].dropna().unique())
)

stato_operativo_sel = st.sidebar.multiselect(
    "Stato operativo",
    options=sorted(df["stato_norm_operativo"].dropna().unique()),
    default=sorted(df["stato_norm_operativo"].dropna().unique())
)

stato_direzionale_sel = st.sidebar.multiselect(
    "Stato direzionale",
    options=sorted(df["stato_norm_direzionale"].dropna().unique()),
    default=sorted(df["stato_norm_direzionale"].dropna().unique())
)

reparto_sel = st.sidebar.multiselect(
    "Reparto",
    options=sorted(df["reparto"].dropna().unique()),
    default=sorted(df["reparto"].dropna().unique())
)

df = apply_common_filters(
    df,
    mesi=mese_sel,
    segmenti=segmento_sel,
    fonti=fonte_sel,
    reparti=reparto_sel,
)
df = df[df["carline"].isin(carline_sel)]

df = df[
    df["stato_norm_operativo"].isin(stato_operativo_sel)
    & df["stato_norm_direzionale"].isin(stato_direzionale_sel)
].copy()

if df.empty:
    st.warning("Con i filtri attuali non ci sono lead da analizzare. Allarga i filtri.")
    st.stop()

# ======================================================
# KPI OPERATIVI
# ======================================================
st.subheader("📌 KPI Operativi")
metrics = {
    "lead": len(df),
    "vendite": int(df["vendita"].sum()) if "vendita" in df.columns else int(df["is_deal"].sum()),
    "lead_girati_venditori": int(df["girato_venditori"].sum()) if "girato_venditori" in df.columns else 0
}

metrics["conversion_rate"] = round((metrics["vendite"] / metrics["lead"]) * 100, 2) if metrics["lead"] else 0
metrics["conversione_venditori"] = round(
    (metrics["vendite"] / metrics["lead_girati_venditori"]) * 100, 2
) if metrics["lead_girati_venditori"] else 0

aperti = int(df["lead_aperto"].sum()) if "lead_aperto" in df.columns else (metrics["lead"] - metrics["vendite"])
persi = int(df["lead_perso"].sum()) if "lead_perso" in df.columns else 0

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Lead Totali", metrics["lead"])
c2.metric("Vendite", metrics["vendite"])
c3.metric("Lead Aperti", aperti)
c4.metric("Persi", persi)
c5.metric("Lead girati ai venditori", metrics["lead_girati_venditori"])
c6.metric("Conversione Venditori %", f"{metrics['conversione_venditori']}%")
# ======================================================
# AGING LEAD APERTI
# ======================================================
st.subheader("⏱️ Aging Lead Aperti")

if "lead_aperto" in df.columns:
    aperti_df = df[df["lead_aperto"]].copy()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Aperti", len(aperti_df))
    c2.metric(">7 giorni", int(aperti_df["aging_giorni"].fillna(0).gt(7).sum()))
    c3.metric(">14 giorni", int(aperti_df["aging_giorni"].fillna(0).gt(14).sum()))
    c4.metric("Scaduti", int(aperti_df["scaduto"].sum()))

# ======================================================
# ANDAMENTO PER MESE
# ======================================================
st.subheader("📅 Andamento per Mese")
st.dataframe(by_month_metrics(df), use_container_width=True)

# ======================================================
# ANALISI PER SEGMENTO
# ======================================================
st.subheader("🚗 Performance per Segmento")
st.dataframe(by_segment_metrics(df).sort_values("Lead", ascending=False), use_container_width=True)

# ======================================================
# PERFORMANCE PER CARLINE
# ======================================================
st.subheader("🚘 Performance per Carline")

carline_df = by_carline_metrics(df)
st.dataframe(carline_df, use_container_width=True)

# ======================================================
# MESE x CARLINE
# ======================================================
st.subheader("🧩 Mese × Carline")

if "modello" in df.columns:
    pivot_mc = pd.pivot_table(
        df,
        index="mese",
        columns="modello",
        values="stato",
        aggfunc="count",
        fill_value=0
    )

    st.dataframe(pivot_mc, use_container_width=True)
else:
    st.info("Colonna 'modello' non presente nel dataset.")

# ======================================================
# MATRICE MESE x SEGMENTO
# ======================================================
st.subheader("🧩 Mese × Segmento")

pivot_ms = pd.pivot_table(
    df,
    index="mese",
    columns="segmento",
    values="stato",
    aggfunc="count",
    fill_value=0
)
st.dataframe(pivot_ms, use_container_width=True)

# ======================================================
# STATO OPERATIVO
# ======================================================
st.subheader("📊 Stato Operativo")

stato_op = (
    df.groupby("stato_norm_operativo")
    .size()
    .reset_index(name="Lead")
    .sort_values("Lead", ascending=False)
)
st.dataframe(stato_op, use_container_width=True)

# ======================================================
# STATO DIREZIONALE
# ======================================================
st.subheader("📊 Stato Direzionale")

stato_dir = (
    df.groupby("stato_norm_direzionale")
    .size()
    .reset_index(name="Lead")
    .sort_values("Lead", ascending=False)
)
st.dataframe(stato_dir, use_container_width=True)

# ======================================================
# FUNNEL OPERATIVO
# ======================================================
st.subheader("🧭 Funnel Operativo")

funnel = (
    df.groupby("fase_funnel")
    .size()
    .reset_index(name="Lead")
    .sort_values("Lead", ascending=False)
)
st.dataframe(funnel, use_container_width=True)

# ======================================================
# STATO LEAD PER MESE
# ======================================================
st.subheader("📊 Stato Direzionale per Mese")

stato_mese = (
    df.groupby(["mese", "stato_norm_direzionale"])
    .size()
    .reset_index(name="Lead")
    .sort_values(["mese", "Lead"], ascending=[True, False])
)
st.dataframe(stato_mese, use_container_width=True)

# ======================================================
# REPARTO
# ======================================================
st.subheader("🏢 Performance per Reparto")

rep = df.groupby("reparto").agg(
    Lead=("stato", "count"),
    Deal=("is_deal", "sum")
).reset_index()
rep["Conversion %"] = (rep["Deal"] / rep["Lead"] * 100).round(2)
st.dataframe(rep.sort_values("Lead", ascending=False), use_container_width=True)

# ======================================================
# GESTORE
# ======================================================
st.subheader("👤 Performance per Gestore")

gest = df.groupby(["gestore", "reparto"]).agg(
    Lead=("stato", "count"),
    Deal=("is_deal", "sum")
).reset_index()
gest["Conversion %"] = (gest["Deal"] / gest["Lead"] * 100).round(2)
st.dataframe(gest.sort_values("Lead", ascending=False), use_container_width=True)

# ======================================================
# PRIORITÀ OPERATIVA
# ======================================================
st.subheader("🎯 Priorità Operativa")

prio = (
    df.groupby("priorita_operativa")
    .size()
    .reset_index(name="Lead")
    .sort_values("Lead", ascending=False)
)
st.dataframe(prio, use_container_width=True)

# ======================================================
# DETTAGLIO
# ======================================================
st.subheader("📋 Dettaglio Lead")

cols = [
    "data",
    "mese",
    "fonte",
    "segmento",
    "stato",
    "stato_norm_operativo",
    "stato_norm_direzionale",
    "fase_funnel",
    "priorita_operativa",
    "reparto",
    "gestore",
    "intestatario",
    "tipo_interesse",
    "brand",
    "modello",
    "aging_giorni",
    "giorni_da_ultima_attivita",
    "giorni_a_scadenza",
]

cols = [c for c in cols if c in df.columns]

if "data" in cols:
    st.dataframe(df[cols].sort_values("data", ascending=False), use_container_width=True)
else:
    st.dataframe(df[cols], use_container_width=True)

# ======================================================
# EXPORT
# ======================================================
st.subheader("📤 Export")
st.download_button(
    "Scarica Lead filtrati (CSV)",
    df.to_csv(index=False),
    file_name="lead_approfondimento_filtrati.csv",
    mime="text/csv"
)