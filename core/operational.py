import pandas as pd

# ======================================================
# STATI DIREZIONALI
# ======================================================
PERSI_DIREZIONALI = {
    "Perso",
}

CHIUSI_DIREZIONALI = {
    "Vendita",
}

APERTI_DIREZIONALI = {
    "Da gestire",
    "In lavorazione",
    "Appuntamento",
}

# ======================================================
# DATETIME SAFE
# ======================================================
def _to_datetime(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, errors="coerce", dayfirst=True)

# ======================================================
# AGGIUNTA CAMPI OPERATIVI
# ======================================================
def add_operational_fields(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    # parsing date
    if "Data creazione" in out.columns:
        out["data_creazione_dt"] = _to_datetime(out["Data creazione"])
    elif "data" in out.columns:
        out["data_creazione_dt"] = _to_datetime(out["data"])
    else:
        out["data_creazione_dt"] = pd.NaT

    if "Data scadenza" in out.columns:
        out["data_scadenza_dt"] = _to_datetime(out["Data scadenza"])
    else:
        out["data_scadenza_dt"] = pd.NaT

    if "Data ultima attività" in out.columns:
        out["data_ultima_attivita_dt"] = _to_datetime(out["Data ultima attività"])
    else:
        out["data_ultima_attivita_dt"] = pd.NaT

    if "Data Chiusura" in out.columns:
        out["data_chiusura_dt"] = _to_datetime(out["Data Chiusura"])
    else:
        out["data_chiusura_dt"] = pd.NaT

    today = pd.Timestamp.today().normalize()

    # lead aperto / chiuso / perso
    if "stato_norm_direzionale" in out.columns:
        stato_dir = out["stato_norm_direzionale"].astype(str).str.strip()

        out["lead_chiuso"] = stato_dir.isin(CHIUSI_DIREZIONALI.union(PERSI_DIREZIONALI))
        out["lead_perso"] = stato_dir.isin(PERSI_DIREZIONALI)
        out["lead_venduto"] = stato_dir.isin(CHIUSI_DIREZIONALI)
        out["lead_aperto"] = stato_dir.isin(APERTI_DIREZIONALI)
    else:
        if "is_deal" in out.columns:
            out["lead_venduto"] = out["is_deal"].fillna(False).astype(bool)
            out["lead_perso"] = False
            out["lead_chiuso"] = out["lead_venduto"]
            out["lead_aperto"] = ~out["lead_chiuso"]
        else:
            out["lead_venduto"] = False
            out["lead_perso"] = False
            out["lead_chiuso"] = False
            out["lead_aperto"] = True

    # aging
    out["aging_giorni"] = (today - out["data_creazione_dt"]).dt.days
    out["giorni_da_ultima_attivita"] = (today - out["data_ultima_attivita_dt"]).dt.days
    out["giorni_a_scadenza"] = (out["data_scadenza_dt"] - today).dt.days

    # flag operativi
    out["scaduto"] = out["lead_aperto"] & out["data_scadenza_dt"].notna() & (out["data_scadenza_dt"] < today)
    out["in_scadenza_oggi"] = out["lead_aperto"] & out["data_scadenza_dt"].notna() & (out["data_scadenza_dt"] == today)
    out["in_scadenza_3gg"] = out["lead_aperto"] & out["data_scadenza_dt"].notna() & (out["giorni_a_scadenza"].between(0, 3))

    out["senza_ultima_attivita"] = out["lead_aperto"] & out["data_ultima_attivita_dt"].isna()

    if "Tipo prossima attività" in out.columns:
        pross = out["Tipo prossima attività"].fillna("").astype(str).str.strip()
        out["senza_prossima_attivita"] = out["lead_aperto"] & pross.eq("")
    else:
        out["senza_prossima_attivita"] = out["lead_aperto"]

    out["fermo_7gg"] = out["lead_aperto"] & out["giorni_da_ultima_attivita"].fillna(9999).gt(7)
    out["fermo_14gg"] = out["lead_aperto"] & out["giorni_da_ultima_attivita"].fillna(9999).gt(14)

    if "intestatario" in out.columns:
        intest = out["intestatario"].fillna("").astype(str).str.strip().str.lower()
        out["senza_assegnatario"] = out["lead_aperto"] & intest.isin(["", "nan", "none", "null"])
    else:
        out["senza_assegnatario"] = out["lead_aperto"]

    # priorità
    def priority(row):
        if not row.get("lead_aperto", False):
            if row.get("lead_venduto", False):
                return "💰 Chiuso"
            if row.get("lead_perso", False):
                return "❌ Perso"
            return "Chiuso"

        if row.get("scaduto", False):
            return "🔥 Scaduto"
        if row.get("in_scadenza_oggi", False):
            return "🔥 Oggi"
        if row.get("senza_assegnatario", False):
            return "⚠️ Senza assegnatario"
        if row.get("senza_ultima_attivita", False):
            return "⚠️ Nessuna attività"
        if row.get("fermo_14gg", False):
            return "🚨 Fermo >14gg"
        if row.get("fermo_7gg", False):
            return "⚠️ Fermo >7gg"
        if row.get("senza_prossima_attivita", False):
            return "🕐 Senza prossima attività"
        if row.get("in_scadenza_3gg", False):
            return "🕐 In scadenza"
        return "✅ In gestione"

    out["priorita_operativa"] = out.apply(priority, axis=1)

    return out

# ======================================================
# ALERT OPERATIVI
# ======================================================
def build_operational_alerts(df: pd.DataFrame) -> list[str]:
    alerts = []

    if "lead_aperto" not in df.columns:
        return ["⚠️ Colonna 'lead_aperto' non presente. Ricarica il CSV dalla Dashboard."]

    aperti = df[df["lead_aperto"]].copy()

    if aperti.empty:
        return ["✅ Nessun lead aperto nei filtri attivi."]

    n_open = len(aperti)
    n_scaduti = int(aperti["scaduto"].sum()) if "scaduto" in aperti.columns else 0
    n_senza_ass = int(aperti["senza_assegnatario"].sum()) if "senza_assegnatario" in aperti.columns else 0
    n_no_att = int(aperti["senza_ultima_attivita"].sum()) if "senza_ultima_attivita" in aperti.columns else 0
    n_fermi_14 = int(aperti["fermo_14gg"].sum()) if "fermo_14gg" in aperti.columns else 0
    n_no_next = int(aperti["senza_prossima_attivita"].sum()) if "senza_prossima_attivita" in aperti.columns else 0

    if n_scaduti > 0:
        alerts.append(f"⚠️ {n_scaduti} lead aperti risultano scaduti.")
    if n_senza_ass > 0:
        alerts.append(f"⚠️ {n_senza_ass} lead aperti sono senza assegnatario.")
    if n_no_att > 0:
        alerts.append(f"⚠️ {n_no_att} lead aperti non hanno attività registrate.")
    if n_no_next > 0:
        alerts.append(f"⚠️ {n_no_next} lead aperti non hanno una prossima attività.")
    if n_fermi_14 > 0:
        alerts.append(f"🚨 {n_fermi_14} lead aperti sono fermi da oltre 14 giorni.")

    if n_open > 0 and (n_scaduti / n_open) >= 0.20:
        alerts.append("📉 Oltre il 20% dei lead aperti è già scaduto.")
    if n_open > 0 and (n_senza_ass / n_open) >= 0.10:
        alerts.append("📉 Troppi lead aperti senza assegnatario.")
    if n_open > 0 and (n_no_att / n_open) >= 0.20:
        alerts.append("📉 Troppi lead aperti senza attività registrata.")
    if n_open > 0 and (n_no_next / n_open) >= 0.20:
        alerts.append("📉 Troppi lead aperti senza prossima attività.")

    if not alerts:
        alerts.append("✅ Nessun alert critico rilevato nei filtri attivi.")

    return alerts