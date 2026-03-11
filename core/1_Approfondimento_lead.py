import streamlit as st
import pandas as pd

from core.loader import load_leads
from core.cleaning import clean_leads

st.set_page_config(layout="wide")
st.title("🔎 Approfondimento Lead – Gestione Operativa")


uploaded_file = st.file_uploader("Carica il CSV Lead", type="csv")
if not uploaded_file:
    st.stop()

df = clean_leads(load_leads(uploaded_file))


# ======================================================
# ESCLUDIAMO WALK-IN
# ======================================================
df = df[df["fonte"] != "Walk-in"]


# ======================================================
# FILTRI
# ======================================================
st.sidebar.header("🎯 Filtri")

df = df[
    df["fonte"].isin(
        st.sidebar.multiselect("Fonte", sorted(df["fonte"].unique()), sorted(df["fonte"].unique()))
    )
    &
    df["stato"].isin(
        st.sidebar.multiselect("Stato Lead", sorted(df["stato"].unique()), sorted(df["stato"].unique()))
    )
    &
    df["reparto"].isin(
        st.sidebar.multiselect("Reparto", sorted(df["reparto"].unique()), sorted(df["reparto"].unique()))
    )
]


# ======================================================
# KPI OPERATIVI
# ======================================================
c1, c2, c3 = st.columns(3)
c1.metric("Lead Totali", len(df))
c2.metric("Lead Chiusi", int(df["is_deal"].sum()))
c3.metric("Lead Aperti", len(df) - int(df["is_deal"].sum()))


# ======================================================
# TABELLA DETTAGLIO
# ======================================================
st.subheader("📋 Dettaglio Lead")

cols = [
    "data",
    "fonte",
    "stato",
    "reparto",
    "gestore",
    "tipo_interesse",
    "brand"
]

st.dataframe(
    df[cols].sort_values("data", ascending=False),
    width="stretch"
)


# ======================================================
# ANALISI PER REPARTO
# ======================================================
st.subheader("🏢 Performance per Reparto")

rep = df.groupby("reparto").agg(
    Lead=("stato", "count"),
    Chiusi=("is_deal", "sum")
).reset_index()

rep["Conversion %"] = (rep["Chiusi"] / rep["Lead"] * 100).round(2)

st.dataframe(rep, width="stretch")


# ======================================================
# ANALISI PER GESTORE
# ======================================================
st.subheader("👤 Performance per Gestore")

gest = df.groupby("gestore").agg(
    Lead=("stato", "count"),
    Chiusi=("is_deal", "sum")
).reset_index()

gest["Conversion %"] = (gest["Chiusi"] / gest["Lead"] * 100).round(2)

st.dataframe(gest.sort_values("Lead", ascending=False), width="stretch")