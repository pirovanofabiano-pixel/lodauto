# ======================================================
# MAPPATURA REPARTI E PERSONE – LODAUTO
# ======================================================

BDC = {
    "martina.acerbis@lodauto.it": "Martina Acerbis",
    "chiara.pennati@lodauto.it": "Chiara Pennati",
    "cristiano.nozza@lodauto.it": "Cristiano Nozza",
    "martina.lancia@lodauto.it": "Martina Lancia",
    "sharon.nozzi@lodauto.it": "Sharon Nozzi",
    "webmaster@lodauto.it": "Fabiano Pirovano",
}

VENDITORI_OMODA_JAECOO = {
    "giovanni.delptrato@lodauto.it": "Giovanni Del Prato",
    "ivan.agliardi@lodauto.it": "Ivan Agliardi",
    "francesco.bazzicalupo@lodauto.it": "Francesco Bazzicalupo",
    "walter.corona@lodauto.it": "Walter Corona",
}

VENDITORI_MERCEDES_NUOVO = {
    "luca.alborghetti@lodauto.it": "Luca Alborghetti",
    "andrea.pistillo@lodauto.it": "Andrea Pistillo",
    "roberto.gussago@lodauto.it": "Roberto Gussago",
    "marco.damiani@lodauto.it": "Marco Damiani",
    "fabio.panizzoli@lodauto.it": "Fabio Panizzoli",
    "gabriele.colombimanzi@lodauto.it": "Gabriele Colombi Manzi",
    "massimo.facchinetti@lodauto.it": "Massimo Facchinetti",
    "antonio.giordano@lodauto.it": "Antonio Giordano",
    "giulian.radice@lodauto.it": "Giulian Radice",
}

VENDITORI_USATO = {
    "guglielmo.suagher@lodauto.it": "Guglielmo Suagher",
    "francesco.pellegrino@lodauto.it": "Francesco Pellegrino",
    "giuseppe.piazzini@lodauto.it": "Giuseppe Piazzini",
}


def map_reparto(email: str):
    if not isinstance(email, str):
        return "Non Assegnato", "Non Assegnato"

    e = email.lower().strip()

    if e in BDC:
        return "BDC", BDC[e]

    if e in VENDITORI_OMODA_JAECOO:
        return "Venditori Omoda / Jaecoo", VENDITORI_OMODA_JAECOO[e]

    if e in VENDITORI_MERCEDES_NUOVO:
        return "Venditori Mercedes Nuovo", VENDITORI_MERCEDES_NUOVO[e]

    if e in VENDITORI_USATO:
        return "Venditori Usato", VENDITORI_USATO[e]

    return "Altro / Non Mappato", email