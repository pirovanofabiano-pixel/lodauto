import streamlit as st
import pandas as pd


def require_leads_df(key: str = "df_leads") -> pd.DataFrame:
    if key not in st.session_state or st.session_state[key] is None:
        st.warning("⚠️ Carica prima il file CSV dalla Dashboard.")
        st.stop()
    return st.session_state[key].copy()