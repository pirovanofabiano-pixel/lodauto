import streamlit as st
import pandas as pd

from utils.session_loader import require_leads_df
from core.business_logic import apply_common_filters
from core.operational import build_operational_alerts

st.set_page_config(layout="wide")
st.title("🛠️ Lead Operativi")

df = require_leads_df()

if "lead_aperto" in df.columns:
    df = df[df["lead_aperto"]].copy()

st.sidebar.header("🎯 Filtri")

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

carline_sel = st.sidebar.multiselect(
    "Carline",
    options=sorted(df["carline"].dropna().unique()),
    default=sorted(df["carline"].dropna().unique())
)

reparto_sel = st.sidebar.multiselect(
    "Reparto",
    options=sorted(df["reparto"].dropna().unique()),
    default=sorted(df["reparto"].dropna().unique())
)

gestore_sel = st.sidebar.multiselect(
    "Gestore",
    options=sorted(df["gestore"].dropna().unique()),
    default=sorted(df["gestore"].dropna().unique())
)

stato_op_sel = st.sidebar.multiselect(
    "Stato operativo",
    options=sorted(df["stato_norm_operativo"].dropna().unique()),
    default=sorted(df["stato_norm_operativo"].dropna().unique())
)

priorita_sel = st.sidebar.multiselect(
    "Priorità operativa",
    options=sorted(df["priorita_operativa"].dropna().unique()),
    default=sorted(df["priorita_operativa"].dropna().unique())
)

df = apply_common_filters(
    df,
    mesi=mese_sel,
    segmenti=segmento_sel,
    reparti=reparto_sel,
)

df = df[df["carline"].isin(carline_sel)]

if gestore_sel:
    df = df[df["gestore"].isin(gestore_sel)]

if stato_op_sel:
    df = df[df["stato_norm_operativo"].isin(stato_op_sel)]

if priorita_sel:
    df = df[df["priorita_operativa"].isin(priorita_sel)]

if df.empty:
    st.warning("Nessun lead operativo con i filtri selezionati.")
    st.stop()

# ======================================================
# KPI
# ======================================================
st.subheader("📌 KPI Operativi")

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Lead aperti", len(df))
c2.metric("Scaduti", int(df["scaduto"].sum()))
c3.metric("Senza assegnatario", int(df["senza_assegnatario"].sum()))
c4.metric("Senza attività", int(df["senza_ultima_attivita"].sum()))
c5.metric("Fermi >14gg", int(df["fermo_14gg"].sum()))

# ======================================================
# ALERT
# ======================================================
st.subheader("🚨 Alert")
for msg in build_operational_alerts(df):
    if msg.startswith("✅"):
        st.success(msg)
    else:
        st.warning(msg)

# ======================================================
# DISTRIBUZIONE PRIORITÀ
# ======================================================
st.subheader("🎯 Distribuzione Priorità")
prio = (
    df.groupby("priorita_operativa")
    .size()
    .reset_index(name="Lead")
    .sort_values("Lead", ascending=False)
)
st.dataframe(prio, use_container_width=True)

# ======================================================
# STATO OPERATIVO
# ======================================================
st.subheader("📊 Stato Operativo dei Lead Aperti")
stato_op = (
    df.groupby("stato_norm_operativo")
    .size()
    .reset_index(name="Lead")
    .sort_values("Lead", ascending=False)
)
st.dataframe(stato_op, use_container_width=True)

# ======================================================
# COLLO DI BOTTIGLIA REPARTO
# ======================================================
st.subheader("🏢 Collo di bottiglia per Reparto")
rep = df.groupby("reparto").agg(
    Lead=("stato", "count"),
    Scaduti=("scaduto", "sum"),
    Fermi_14gg=("fermo_14gg", "sum"),
    Senza_Attivita=("senza_ultima_attivita", "sum"),
).reset_index()
st.dataframe(rep.sort_values("Lead", ascending=False), use_container_width=True)

# ======================================================
# GESTORI
# ======================================================
st.subheader("👤 Carico Operativo per Gestore")
gest = df.groupby(["gestore", "reparto"]).agg(
    Lead=("stato", "count"),
    Scaduti=("scaduto", "sum"),
    Fermi_14gg=("fermo_14gg", "sum"),
    Senza_Attivita=("senza_ultima_attivita", "sum"),
).reset_index()
st.dataframe(gest.sort_values(["Lead", "Scaduti"], ascending=[False, False]), use_container_width=True)

# ======================================================
# DETTAGLIO OPERATIVO
# ======================================================
st.subheader("📋 Lead da lavorare")

cols = [
    "Data creazione",
    "Data scadenza",
    "Tipo prossima attività",
    "Data ultima attività",
    "Tipo ultima attività",
    "stato",
    "stato_norm_operativo",
    "stato_norm_direzionale",
    "priorita_operativa",
    "aging_giorni",
    "giorni_da_ultima_attivita",
    "giorni_a_scadenza",
    "reparto",
    "gestore",
    "intestatario",
    "fonte",
    "segmento",
    "brand",
    "modello",
    "nome/rag. soc.",
    "telefono",
]

cols = [c for c in cols if c in df.columns]

sort_cols = [c for c in ["priorita_operativa", "Data scadenza", "aging_giorni"] if c in df.columns]

if sort_cols:
    ascending = []
    for c in sort_cols:
        if c == "aging_giorni":
            ascending.append(False)
        else:
            ascending.append(True)
    show_df = df[cols].sort_values(by=sort_cols, ascending=ascending)
else:
    show_df = df[cols]

st.dataframe(show_df, use_container_width=True)

st.download_button(
    "Scarica Lead Operativi (CSV)",
    df.to_csv(index=False),
    file_name="lead_operativi.csv",
    mime="text/csv"
)