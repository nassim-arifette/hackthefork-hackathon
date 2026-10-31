"""Catalogue des contrats comparés.

Trois contrats existants ou proposés, aux paramètres fixes : le prix Unéal de 2023, le barème
NatUp 2023-2024 reconstitué et la proposition du dossier pilote (data/pilote_300t). Trois
contrats calibrés pour la fiabilité visée : prix unique (P*), barème par tranches dont on
recalcule la première tonne, prix de base avec prime à l'hectare. Les formules sont dans
model.py (paiement, marge_lentille, calibrer_*).
"""
import json
import math

from common import DATA
from model import calibrer_premier_palier, calibrer_prime_ha

PILOTE = DATA / "pilote_300t"
PRIX_BASE_PRIME = 900  # €/t : le prix Unéal de 2023, complété par une prime à l'hectare


def existants() -> list[dict]:
    c = json.loads((PILOTE / "contrats.json").read_text())
    cfg = json.loads((PILOTE / "config.json").read_text())
    natup, prop = c["public_natup_2023_2024"], c["synthetique_2027"]
    return [
        {"id": "uneal_2023", "nom": "Unéal, avec Vivien Paille",
         "detail": "900 €/t, lentilles valorisées en décembre 2023", "statut": "source",
         "prix": 900, "url": "https://uneal.com/cms_filiere-lentille-uneal"},
        {"id": "natup_2023", "nom": "NatUp, récoltes 2023 et 2024",
         "detail": "900 €/t la première tonne par hectare, 700 la deuxième, 600 au-delà",
         "statut": "source", "paliers": natup["paliers_marginaux_eur_t"], "url": natup["source_url"]},
        {"id": "proposition_2027", "nom": "Proposition du dossier pilote",
         "detail": "1 000 / 750 / 650 €/t par tranche, 30 €/t pour un lot pré-nettoyé",
         "statut": "suppose", "paliers": prop["paliers_marginaux_eur_t"],
         "prime_t": prop["prime_service_eur_t_nette"],
         "cout_producteur_t_brut": cfg["cout_prenettoyage_eur_t_recoltee"]},
    ]


def calibres(yL, yW, pB, h: dict, prix_unique: float) -> list[dict]:
    """Trois façons d'atteindre la fiabilité visée sur les mêmes années simulées."""
    suite = tuple(existants()[2]["paliers"][1:])
    p1 = calibrer_premier_palier(suite, yL, yW, pB, h, h["tau"])
    prime = calibrer_prime_ha(PRIX_BASE_PRIME, yL, yW, pB, h, h["tau"])
    return [
        {"id": "unique", "nom": "Prix unique", "prix": max(0, math.ceil(prix_unique))},
        {"id": "paliers", "nom": "Barème par tranches", "paliers": [p1, *suite]},
        {"id": "prime_ha", "nom": "Prix de base et prime à l'hectare", "prix": PRIX_BASE_PRIME,
         "prime_ha": math.ceil(prime)},
    ]
