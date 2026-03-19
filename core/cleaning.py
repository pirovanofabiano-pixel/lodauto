import pandas as pd


def clean_leads(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        raise ValueError("Il file caricato è vuoto o non leggibile.")

    d = df.copy()

    # -------------------------------------------------
    # normalizza i nomi colonna originali
    # -------------------------------------------------
    d.columns = [str(c).strip() for c in d.columns]

    rename_map = {
        "ID lead": "id lead",
        "Stato lead": "stato",
        "Data creazione": "data",
        "Provincia": "provincia",
        "Provenienza": "fonte",
        "Interesse": "tipo_interesse",
        "Marca": "brand",
        "Modello": "carline",
        "Azienda": "reparto",
        "Intestatario": "intestatario",
        "Causale Chiusura": "causale_chiusura",
        "Data Chiusura": "data_chiusura",
        "Sede": "sede",
        "Canale": "canale",
        "Campagna": "campagna",
        "UTM Source": "utm_source",
        "UTM Medium": "utm_medium",
        "UTM Campaign": "utm_campaign",
        "UTM Term": "utm_term",
        "UTM Content": "utm_content",
        "Città": "citta",
        "CAP": "cap",
        "Nome/Rag. soc.": "nome_rag_soc",
        "Tipo soggetto": "tipo_soggetto",
        "Descrizione provenienza": "descrizione_provenienza",
    }

    d = d.rename(columns=rename_map)

    # -------------------------------------------------
    # controlla colonne minime reali dopo il rename
    # -------------------------------------------------
    required_after_rename = [
        "id lead",
        "stato",
        "data",
        "provincia",
        "fonte",
        "tipo_interesse",
        "brand",
        "intestatario",
    ]

    missing = [c for c in required_after_rename if c not in d.columns]
    if missing:
        raise ValueError(
            f"Mancano colonne obbligatorie dopo la normalizzazione: {missing}"
        )

    # -------------------------------------------------
    # pulizia base stringhe
    # -------------------------------------------------
    for col in d.columns:
        if d[col].dtype == "object":
            d[col] = d[col].fillna("").astype(str).str.strip()

    # -------------------------------------------------
    # data e mese
    # -------------------------------------------------
    d["data"] = pd.to_datetime(d["data"], errors="coerce")
    d["mese"] = d["data"].dt.to_period("M").astype(str)

    # -------------------------------------------------
    # is_deal / vendita
    # logica basata su stato / causale chiusura
    # -------------------------------------------------
    stato_lower = d["stato"].fillna("").astype(str).str.lower()

    d["is_deal"] = stato_lower.str.contains("vend", na=False)
    d["vendita"] = d["is_deal"].astype(int)

    # -------------------------------------------------
    # lead aperto
    # -------------------------------------------------
    d["lead_aperto"] = ~d["is_deal"]

    if "causale_chiusura" not in d.columns:
        d["causale_chiusura"] = ""

    # -------------------------------------------------
    # girato_venditori
    # fallback prudente: se c'è intestatario valorizzato
    # e non è chiuso subito come non gestito, consideralo girato
    # -------------------------------------------------
    intest = d["intestatario"].fillna("").astype(str).str.strip()
    causale = d["causale_chiusura"].fillna("").astype(str).str.lower()

    d["girato_venditori"] = (
        intest.ne("")
        & ~causale.str.contains("non gestito|duplicato|spam|errato", na=False)
    )

    # -------------------------------------------------
    # gestore
    # -------------------------------------------------
    d["gestore"] = d["intestatario"]

    # -------------------------------------------------
    # reparto
    # se manca o è vuoto, usa brand
    # -------------------------------------------------
    if "reparto" not in d.columns:
        d["reparto"] = d["brand"]
    else:
        d["reparto"] = d["reparto"].replace("", pd.NA)
        d["reparto"] = d["reparto"].fillna(d["brand"])

    # -------------------------------------------------
    # normalizzazioni semplici
    # -------------------------------------------------
    d["provincia"] = d["provincia"].astype(str).str.upper().str.strip()
    d["fonte"] = d["fonte"].astype(str).str.strip()
    d["tipo_interesse"] = d["tipo_interesse"].astype(str).str.strip()
    d["brand"] = d["brand"].astype(str).str.strip()
    d["carline"] = d["carline"].astype(str).str.strip() if "carline" in d.columns else ""

    return d