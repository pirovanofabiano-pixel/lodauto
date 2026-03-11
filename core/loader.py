import pandas as pd

def load_leads(file):
    """
    Loader CSV robusto:
    - autodetect separatore
    - supporta CSV italiani
    - evita crash su righe sporche
    """

    try:
        # Primo tentativo: separatore automatico
        return pd.read_csv(
            file,
            sep=None,            # autodetect
            engine="python",     # più robusto
            encoding="utf-8",
            on_bad_lines="skip"  # salta righe rotte
        )
    except Exception:
        # Fallback classico CSV italiano
        return pd.read_csv(
            file,
            sep=";",
            engine="python",
            encoding="latin1",
            on_bad_lines="skip"
        )