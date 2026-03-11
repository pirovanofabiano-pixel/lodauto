# ======================================================
# CLASSIFICAZIONE AUTOMATICA PROVENIENZE – DEFINITIVA
# ======================================================

MARKETPLACE_SOURCES = [
    "annunci su internet",
    "automobile.it",
    "autoscout24",
    "marketplace (autoscout - subito)",
    "subito.it"
]

SOCIAL_ADS_SOURCES = [
    "campagna adv f",
    "campagna adv i",
    "facebook",
    "instagram",
    "social (instagram - facebook)"
]

GOOGLE_ADS_SOURCES = [
    "google ads",
    "lodauto.it",
    "banner"
]

DEM_SMS_SOURCES = [
    "dem",
    "lodoutlet",
    "crazy days"
]

CASA_MADRE_MERCEDES_SOURCES = [
    "datasharing mercedes benz",
    "datasharing mercedes benz mbfs",
    "mercedes paco"
]

CASA_MADRE_OMODA_JAECOO_SOURCES = [
    "omoda - 3rd party",
    "omoda - call center - call center",
    "omoda - in-store",
    "omoda - official website",
    "omoda - official website - g+",
    "omoda - official website - drivek",
    "jaecoo - official website",
    "jaecoo - official website - g+",
    "jaecoo - in-store"
]

CAMPAGNE_INTERNE_SOURCES = [
    "promo aziende",
    "cross sell officina",
    "csi",
    "csi officina",
    "estrazione usato",
    "invito evento"
]

WALK_IN_SOURCES = [
    "walk in",
    "passaparola",
    "cliente storico"
]

TRAFFICO_ORGANICO_SOURCES = [
    "glytter",
    "sito internet lodauto",
    "lead ricevuto da mail: no-reply@stockspark.io"
]


def classify_source(raw: str) -> str:
    if not isinstance(raw, str):
        return "Altro"

    v = raw.strip().lower()

    if v in MARKETPLACE_SOURCES:
        return "Marketplace"
    if v in SOCIAL_ADS_SOURCES:
        return "Social Ads"
    if v in GOOGLE_ADS_SOURCES:
        return "Google Ads"
    if v in DEM_SMS_SOURCES:
        return "DEM / SMS"
    if v in CASA_MADRE_MERCEDES_SOURCES:
        return "Casa Madre Mercedes"
    if v in CASA_MADRE_OMODA_JAECOO_SOURCES:
        return "Casa Madre Omoda / Jaecoo"
    if v in CAMPAGNE_INTERNE_SOURCES:
        return "Campagne Interne"
    if v in WALK_IN_SOURCES:
        return "Walk-in"
    if v in TRAFFICO_ORGANICO_SOURCES:
        return "Traffico Organico"

    return "Altro"# ======================================================
# CLASSIFICAZIONE AUTOMATICA PROVENIENZE – DEFINITIVA
# ======================================================

MARKETPLACE_SOURCES = [
    "annunci su internet",
    "automobile.it",
    "autoscout24",
    "marketplace (autoscout - subito)",
    "lead ricevuto da mail: noreply@iovox.com",
    "subito.it"
]

SOCIAL_ADS_SOURCES = [
    "campagna adv f",
    "campagna adv i",
    "facebook",
    "instagram",
    "social (instagram - facebook)"
]

GOOGLE_ADS_SOURCES = [
    "google ads",
    "lodauto.it",
    "banner"
]

DEM_SMS_SOURCES = [
    "dem",
    "lodoutlet",
    "crazy days"
]

CASA_MADRE_MERCEDES_SOURCES = [
    "datasharing mercedes benz",
    "datasharing mercedes benz mbfs",
    "mercedes paco"
]

CASA_MADRE_OMODA_JAECOO_SOURCES = [
    "omoda - 3rd party",
    "omoda - call center - call center",
    "omoda - in-store",
    "omoda - official website",
    "omoda - official website - g+",
    "omoda - official website - drivek",
    "jaecoo - official website",
    "jaecoo - official website - g+",
    "jaecoo - in-store"
]

CAMPAGNE_INTERNE_SOURCES = [
    "promo aziende",
    "cross sell officina",
    "csi",
    "csi officina",
    "estrazione usato",
    "invito evento"
]

WALK_IN_SOURCES = [
    "walk in",
    "passaparola",
    "cliente storico"
]

TRAFFICO_ORGANICO_SOURCES = [
    "glytter",
    "sito internet lodauto",
    "lead ricevuto da mail: noreply@iovox.com",
    "lead ricevuto da mail: no-reply@stockspark.io"
]


def classify_source(raw: str) -> str:
    if not isinstance(raw, str):
        return "Altro"

    v = raw.strip().lower()

    if v in MARKETPLACE_SOURCES:
        return "Marketplace"
    if v in SOCIAL_ADS_SOURCES:
        return "Social Ads"
    if v in GOOGLE_ADS_SOURCES:
        return "Google Ads"
    if v in DEM_SMS_SOURCES:
        return "DEM / SMS"
    if v in CASA_MADRE_MERCEDES_SOURCES:
        return "Casa Madre Mercedes"
    if v in CASA_MADRE_OMODA_JAECOO_SOURCES:
        return "Casa Madre Omoda / Jaecoo"
    if v in CAMPAGNE_INTERNE_SOURCES:
        return "Campagne Interne"
    if v in WALK_IN_SOURCES:
        return "Walk-in"
    if v in TRAFFICO_ORGANICO_SOURCES:
        return "Traffico Organico"

    return "Altro"