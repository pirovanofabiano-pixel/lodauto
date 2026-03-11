import pandas as pd


def apply_common_filters(
    df: pd.DataFrame,
    mesi=None,
    segmenti=None,
    fonti=None,
    stati=None,
    reparti=None,
    brand=None,
    tipo_interesse=None,
):
    out = df.copy()

    if mesi is not None and len(mesi) > 0 and "mese" in out.columns:
        out = out[out["mese"].isin(mesi)]

    if segmenti is not None and len(segmenti) > 0 and "segmento" in out.columns:
        out = out[out["segmento"].isin(segmenti)]

    if fonti is not None and len(fonti) > 0 and "fonte" in out.columns:
        out = out[out["fonte"].isin(fonti)]

    if stati is not None and len(stati) > 0 and "stato" in out.columns:
        out = out[out["stato"].isin(stati)]

    if reparti is not None and len(reparti) > 0 and "reparto" in out.columns:
        out = out[out["reparto"].isin(reparti)]

    if brand is not None and len(brand) > 0 and "brand" in out.columns:
        out = out[out["brand"].isin(brand)]

    if tipo_interesse is not None and len(tipo_interesse) > 0 and "tipo_interesse" in out.columns:
        out = out[out["tipo_interesse"].isin(tipo_interesse)]

    return out