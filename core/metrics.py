import pandas as pd


def overview_metrics(df: pd.DataFrame) -> dict:
    lead = len(df)
    vendite = int(df["vendita"].sum()) if "vendita" in df.columns else int(df["is_deal"].sum())

    conversion_rate = round((vendite / lead) * 100, 2) if lead else 0

    if "girato_venditori" in df.columns:
        lead_girati_venditori = int(df["girato_venditori"].sum())
    else:
        lead_girati_venditori = 0

    conversione_venditori = (
        round((vendite / lead_girati_venditori) * 100, 2)
        if lead_girati_venditori else 0
    )

    return {
        "lead": lead,
        "vendite": vendite,
        "conversion_rate": conversion_rate,
        "lead_girati_venditori": lead_girati_venditori,
        "conversione_venditori": conversione_venditori,
    }


def by_month_metrics(df: pd.DataFrame) -> pd.DataFrame:
    if "mese" not in df.columns:
        return pd.DataFrame(columns=["mese", "Lead", "Deal", "Lead girati venditori", "Conversion %", "Conversione Venditori %"])

    lead_col = "stato" if "stato" in df.columns else df.columns[0]
    deal_col = "vendita" if "vendita" in df.columns else "is_deal"

    if "girato_venditori" not in df.columns:
        df = df.copy()
        df["girato_venditori"] = False

    out = df.groupby("mese").agg(
        Lead=(lead_col, "count"),
        Deal=(deal_col, "sum"),
        Lead_girati_venditori=("girato_venditori", "sum"),
    ).reset_index()

    out["Conversion %"] = (out["Deal"] / out["Lead"] * 100).round(2)
    out["Conversione Venditori %"] = (
        out["Deal"] / out["Lead_girati_venditori"] * 100
    ).replace([float("inf"), -float("inf")], 0).fillna(0).round(2)

    out = out.rename(columns={"Lead_girati_venditori": "Lead girati venditori"})
    return out.sort_values("mese")


def by_segment_metrics(df: pd.DataFrame) -> pd.DataFrame:
    if "segmento" not in df.columns:
        return pd.DataFrame(columns=["segmento", "Lead", "Deal", "Lead girati venditori", "Conversion %", "Conversione Venditori %"])

    lead_col = "stato" if "stato" in df.columns else df.columns[0]
    deal_col = "vendita" if "vendita" in df.columns else "is_deal"

    if "girato_venditori" not in df.columns:
        df = df.copy()
        df["girato_venditori"] = False

    out = df.groupby("segmento").agg(
        Lead=(lead_col, "count"),
        Deal=(deal_col, "sum"),
        Lead_girati_venditori=("girato_venditori", "sum"),
    ).reset_index()

    out["Conversion %"] = (out["Deal"] / out["Lead"] * 100).round(2)
    out["Conversione Venditori %"] = (
        out["Deal"] / out["Lead_girati_venditori"] * 100
    ).replace([float("inf"), -float("inf")], 0).fillna(0).round(2)

    out = out.rename(columns={"Lead_girati_venditori": "Lead girati venditori"})
    return out.sort_values(["Lead", "Conversione Venditori %"], ascending=[False, False])


def by_carline_metrics(df: pd.DataFrame) -> pd.DataFrame:
    group_col = "carline" if "carline" in df.columns else "modello"

    if group_col not in df.columns:
        return pd.DataFrame(columns=["Carline", "Lead", "Deal", "Lead girati venditori", "Conversion %", "Conversione Venditori %"])

    lead_col = "stato" if "stato" in df.columns else df.columns[0]
    deal_col = "vendita" if "vendita" in df.columns else "is_deal"

    if "girato_venditori" not in df.columns:
        df = df.copy()
        df["girato_venditori"] = False

    out = df.groupby(group_col).agg(
        Lead=(lead_col, "count"),
        Deal=(deal_col, "sum"),
        Lead_girati_venditori=("girato_venditori", "sum"),
    ).reset_index()

    out["Conversion %"] = (out["Deal"] / out["Lead"] * 100).round(2)
    out["Conversione Venditori %"] = (
        out["Deal"] / out["Lead_girati_venditori"] * 100
    ).replace([float("inf"), -float("inf")], 0).fillna(0).round(2)

    out = out.rename(
        columns={
            group_col: "Carline",
            "Lead_girati_venditori": "Lead girati venditori"
        }
    )

    return out.sort_values(["Lead", "Conversione Venditori %"], ascending=[False, False])