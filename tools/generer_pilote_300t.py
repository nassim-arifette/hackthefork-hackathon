#!/usr/bin/env python3
"""Jeu de démonstration, stdlib uniquement ; aucune observation de ferme réelle."""

import argparse
import csv
import hashlib
import json
import random
import tempfile
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path


RACINE = Path(__file__).resolve().parents[1]
DOSSIER = RACINE / "data" / "pilote_300t"
D = lambda x: Decimal(str(x))
ZERO = D(0)
CENT = D("0.01")
MICRO = D("0.000001")


def q(x, precision=CENT):
    return D(x).quantize(precision, rounding=ROUND_HALF_UP)


def tonnes(x):
    return q(x, MICRO)


def borne(x, minimum, maximum):
    return min(max(D(x), D(minimum)), D(maximum))


def verifier(condition, message):
    if not condition:
        raise ValueError(message)


def lire_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def ecrire_csv(path, lignes):
    with path.open("w", encoding="utf-8", newline="") as flux:
        writer = csv.DictWriter(flux, fieldnames=list(lignes[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(lignes)


def somme(lignes, champ):
    return sum((D(ligne[champ]) for ligne in lignes), ZERO)


def ventilation_paliers(surface, net):
    """Le plafond est celui d'une exploitation-campagne, jamais celui d'un camion."""
    premier = min(surface, net)
    deuxieme = min(surface, max(ZERO, net - surface))
    troisieme = max(ZERO, net - 2 * surface)
    return premier, deuxieme, troisieme


def recette_bareme(surface, net, prix):
    paliers = ventilation_paliers(surface, net)
    return q(sum((masse * D(tarif) for masse, tarif in zip(paliers, prix)), ZERO))


def fabriquer_lots(config, contrats):
    rng = random.Random(config["graine_aleatoire"])
    conditions = contrats["synthetique_2027"]
    qualite = conditions["qualite_apres_tri"]
    refus = {(r["annee"], r["ferme_numero"]): r["motif"] for r in config["refus_imposes_scenario"]}
    fermes = []
    for numero, surface in enumerate(config["surfaces_fermes_ha"], 1):
        fermes.append({
            "numero": numero, "surface": D(surface),
            "facteur_rendement": D(rng.uniform(0.84, 1.16)),
            "distance": q(rng.uniform(8, 75)),
            "prenettoye": numero % 3 != 0,
        })
    lignes = []
    for campagne in config["campagnes"]:
        annee = campagne["annee"]
        for ferme in fermes:
            numero, surface = ferme["numero"], ferme["surface"]
            ferme_id = f"SYN_F{numero:02d}"
            bruit_rendement = D(rng.gauss(1, 0.19))
            rendement = tonnes(borne(D(campagne["rendement_brut_central_t_ha"]) * ferme["facteur_rendement"] * bruit_rendement, 0.35, 3.4))
            brut = tonnes(surface * rendement)
            humidite = q(borne(D(campagne["humidite_centrale_pct"]) + D(rng.gauss(0, 1.3)), 8.5, 19))
            impuretes_recolte = q(borne(D(campagne["impuretes_recolte_centrales_pct"]) + D(rng.gauss(0, 1.8)), 1, 15))
            bruches = q(borne(D(campagne["grains_bruches_centraux_pct"]) * D(rng.uniform(0.45, 1.7)), 1, 55))
            germes = q(borne(D(campagne["grains_germes_centraux_pct"]) * D(rng.uniform(0.5, 1.6)), 0, 30))
            # Pré-nettoyage : retrait de 70 % des impuretés massiques seulement.
            ecarts_pre = tonnes(brut * impuretes_recolte / 100 * D("0.70")) if ferme["prenettoye"] else tonnes(0)
            recu = brut - ecarts_pre
            impuretes_recues_t = tonnes(brut * impuretes_recolte / 100) - ecarts_pre
            impuretes_recues_pct = q(100 * impuretes_recues_t / recu)
            sechage = humidite > D(config["humidite_seuil_sechage_pct"])
            humidite_sortie = D(config["humidite_cible_sechage_pct"]) if sechage else humidite
            # Conservation de la matière sèche ; aucune réhumidification des lots secs.
            eau = tonnes(recu * (humidite - humidite_sortie) / (100 - humidite_sortie)) if sechage else tonnes(0)
            apres_eau = recu - eau
            ecarts_impuretes = tonnes(apres_eau * impuretes_recues_pct / 100)
            apres_impuretes = apres_eau - ecarts_impuretes
            masse_relative = q(rng.uniform(config["masse_relative_grain_defectueux_min"], config["masse_relative_grain_defectueux_max"]))
            # Comptages pouvant se recouvrir : union sous hypothèse d'indépendance.
            fraction_union = bruches / 100 + germes / 100 - bruches * germes / 10000
            fraction_defauts_masse = fraction_union * masse_relative / (1 - fraction_union + fraction_union * masse_relative)
            masse_defauts_avant = tonnes(apres_impuretes * fraction_defauts_masse)
            cible_defauts_sortie = q(rng.uniform(0.25, 1.85))
            insectes_vivants = 0
            moisissure = "non"
            motif = refus.get((annee, numero), "aucun")
            if motif == "defauts_residuels_superieurs_2_pct":
                cible_defauts_sortie = q(rng.uniform(2.4, 4.8))
            elif motif == "insectes_vivants_apres_tri":
                insectes_vivants = 1
            elif motif == "moisissure_detectee":
                moisissure = "oui"
            cible_fraction = cible_defauts_sortie / 100
            # Retrait des seuls grains défectueux, avec résidu matériel explicite.
            ecarts_defauts = tonnes(max(ZERO, (masse_defauts_avant - cible_fraction * apres_impuretes) / (1 - cible_fraction)))
            ecarts_tri = ecarts_impuretes + ecarts_defauts
            net_potentiel = recu - eau - ecarts_tri
            masse_defauts_restants = masse_defauts_avant - ecarts_defauts
            defauts_sortie = q(100 * masse_defauts_restants / net_potentiel)
            taux_perte_defauts = q(100 * ecarts_defauts / apres_impuretes)
            accepte = (
                humidite_sortie <= D(qualite["humidite_max_pct"])
                and defauts_sortie <= D(qualite["defauts_max_pct"])
                and insectes_vivants <= qualite["insectes_vivants_max_nombre"]
                and moisissure == "non"
            )
            net = net_potentiel if accepte else tonnes(0)
            refuse = tonnes(0) if accepte else net_potentiel
            prix_base = D(campagne["prix_base_hypothese_eur_t"])
            ajustement = D(-20 if defauts_sortie > D("1.5") else (10 if defauts_sortie < D("0.7") else 0)) if accepte else ZERO
            prix_paye = prix_base + ajustement if accepte else ZERO
            prime_t = D(config["prime_historique_prenettoyage_eur_t_nette"]) if ferme["prenettoye"] and accepte else ZERO
            paiement_avant = q(net * prix_paye)
            prime = q(net * prime_t)
            paiement = paiement_avant + prime
            intrants_ha = q(borne(D(campagne["charges_intrants_centrales_eur_ha"]) + D(rng.uniform(-35, 35)), 350, 600))
            intrants = q(surface * intrants_ha)
            cout_pre = q(brut * D(config["cout_prenettoyage_eur_t_recoltee"])) if ferme["prenettoye"] else q(0)
            cout_tri = q(recu * D(conditions["tri_eur_t_brute_recue"]))
            taux_collecte = D(conditions["transport"]["fixe_eur_t_brute_recue"]) + D(conditions["transport"]["variable_eur_t_brute_recue_km_route"]) * ferme["distance"]
            cout_collecte = q(recu * taux_collecte)
            cout_sechage = q(recu * (humidite - humidite_sortie) * D(config["cout_sechage_eur_t_recue_point_humidite"]))
            bloc = 1 + (annee - 2019 + numero - 1) % config["nombre_blocs_rotation"]
            lignes.append({
                "statut_donnees": "synthetique", "cooperative_id": config["cooperative_id"],
                "ferme_id": ferme_id, "lot_id": f"{ferme_id}_{annee}", "campagne": annee,
                "scenario": campagne["scenario"], "bloc_rotation_id": f"{ferme_id}_B{bloc}",
                "surface_lentille_ha": q(surface), "surface_rotation_ha": q(surface * config["nombre_blocs_rotation"]),
                "rendement_brut_t_ha": rendement, "recolte_brute_t": brut,
                "prenettoye": "oui" if ferme["prenettoye"] else "non",
                "impuretes_recolte_pct_masse": impuretes_recolte, "ecarts_prenettoyage_t": ecarts_pre,
                "brut_recu_t": recu, "humidite_reception_pct": humidite,
                "impuretes_reception_pct_masse": impuretes_recues_pct,
                "grains_bruches_reception_pct_nombre": bruches, "grains_germes_reception_pct_nombre": germes,
                "grains_defectueux_union_pct_nombre": q(100 * fraction_union),
                "ratio_masse_grain_defectueux_sain": masse_relative,
                "defauts_avant_tri_pct_masse": q(100 * fraction_defauts_masse),
                "masse_defauts_avant_tri_t": masse_defauts_avant,
                "taux_perte_massique_defauts_scenario_pct": taux_perte_defauts,
                "eau_retiree_t": eau, "ecarts_impuretes_tri_t": ecarts_impuretes,
                "ecarts_defauts_tri_t": ecarts_defauts, "ecarts_tri_t": ecarts_tri,
                "masse_defauts_restants_apres_tri_t": masse_defauts_restants,
                "net_apres_tri_avant_agreage_t": net_potentiel,
                "humidite_apres_tri_pct": q(humidite_sortie), "defauts_apres_tri_pct": defauts_sortie,
                "insectes_vivants_apres_tri_nombre_echantillon": insectes_vivants,
                "moisissure_detectee": moisissure, "statut_lot": "accepte" if accepte else "refuse_total",
                "motif_refus": motif, "refus_qualite_t": refuse, "net_alimentaire_paye_t": net,
                "prix_base_annuel_hypothese_eur_t": q(prix_base), "ajustement_qualite_eur_t": q(ajustement),
                "prix_paye_avant_prime_eur_t_nette": q(prix_paye), "prime_service_eur_t_nette": q(prime_t),
                "prix_paye_apres_prime_eur_t_nette": q(prix_paye + prime_t),
                "paiement_avant_prime_eur": paiement_avant, "prime_service_eur": prime,
                "paiement_final_producteur_eur": paiement, "charges_intrants_hors_meca_eur_ha": intrants_ha,
                "charges_intrants_hors_meca_eur": intrants, "cout_prenettoyage_producteur_eur": cout_pre,
                "solde_producteur_hors_meca_eur": paiement - intrants - cout_pre,
                "solde_producteur_hors_meca_eur_ha": q((paiement - intrants - cout_pre) / surface),
                "distance_route_km": ferme["distance"], "tri_effectue": "oui", "payeur_tri": "acheteur",
                "cout_tri_acheteur_eur": cout_tri, "cout_collecte_acheteur_eur": cout_collecte,
                "cout_sechage_acheteur_eur": cout_sechage,
                "budget_achat_collecte_tri_sechage_eur": paiement + cout_tri + cout_collecte + cout_sechage,
            })
    return lignes


def resumer(lignes, config):
    resultats = []
    for campagne in config["campagnes"]:
        annee = campagne["annee"]
        groupe = [l for l in lignes if l["campagne"] == annee]
        surface = somme(groupe, "surface_lentille_ha")
        net = somme(groupe, "net_alimentaire_paye_t")
        paiement = somme(groupe, "paiement_final_producteur_eur")
        resultats.append({
            "statut_donnees": "synthetique", "campagne": annee, "scenario": campagne["scenario"],
            "nombre_lots": len(groupe), "nombre_lots_refuses": sum(l["statut_lot"] == "refuse_total" for l in groupe),
            "surface_lentille_ha": surface, "recolte_brute_t": somme(groupe, "recolte_brute_t"),
            "ecarts_prenettoyage_t": somme(groupe, "ecarts_prenettoyage_t"), "brut_recu_t": somme(groupe, "brut_recu_t"),
            "eau_retiree_t": somme(groupe, "eau_retiree_t"), "ecarts_tri_t": somme(groupe, "ecarts_tri_t"),
            "refus_qualite_t": somme(groupe, "refus_qualite_t"), "net_alimentaire_paye_t": net,
            "rendement_brut_t_ha": tonnes(somme(groupe, "recolte_brute_t") / surface),
            "rendement_net_t_ha": tonnes(net / surface), "objectif_pilote_t_net": config["objectif_pilote_t_net"],
            "ecart_objectif_t": net - D(config["objectif_pilote_t_net"]),
            "prix_moyen_avant_prime_eur_t_nette": q(somme(groupe, "paiement_avant_prime_eur") / net),
            "prix_moyen_apres_prime_eur_t_nette": q(paiement / net),
            "paiement_final_producteurs_eur": paiement,
            "charges_intrants_hors_meca_eur": somme(groupe, "charges_intrants_hors_meca_eur"),
            "cout_prenettoyage_producteurs_eur": somme(groupe, "cout_prenettoyage_producteur_eur"),
            "recette_producteurs_eur_ha": q(paiement / surface),
            "solde_producteurs_hors_meca_eur_ha": q(somme(groupe, "solde_producteur_hors_meca_eur") / surface),
            "cout_tri_acheteur_eur": somme(groupe, "cout_tri_acheteur_eur"),
            "cout_collecte_acheteur_eur": somme(groupe, "cout_collecte_acheteur_eur"),
            "cout_sechage_acheteur_eur": somme(groupe, "cout_sechage_acheteur_eur"),
            "budget_achat_collecte_tri_sechage_eur": somme(groupe, "budget_achat_collecte_tri_sechage_eur"),
        })
    return resultats


def comparer(lignes, config, contrats):
    comparaison = []
    identifiants = ["public_natup_2023_2024", "synthetique_2027", "uniforme_900"]
    periodes = [c["annee"] for c in config["campagnes"]] + ["2019-2025"]
    for periode in periodes:
        groupe = [l for l in lignes if periode == "2019-2025" or l["campagne"] == periode]
        # Les futures livraisons fractionnées devront partager la même surface.
        exploitations = defaultdict(list)
        for lot in groupe:
            exploitations[(lot["ferme_id"], lot["campagne"])].append(lot)
        surface = sum((D(ls[0]["surface_lentille_ha"]) for ls in exploitations.values()), ZERO)
        net = somme(groupe, "net_alimentaire_paye_t")
        cout_agri = somme(groupe, "charges_intrants_hors_meca_eur") + somme(groupe, "cout_prenettoyage_producteur_eur")
        cout_tri = somme(groupe, "cout_tri_acheteur_eur")
        cout_collecte = somme(groupe, "cout_collecte_acheteur_eur")
        cout_sechage = somme(groupe, "cout_sechage_acheteur_eur")
        prime = sum((q(l["net_alimentaire_paye_t"] * D(contrats["synthetique_2027"]["prime_service_eur_t_nette"])) for l in groupe if l["prenettoye"] == "oui"), ZERO)
        for identifiant in identifiants:
            tarifs = contrats[identifiant]["paliers_marginaux_eur_t"]
            paiement_base = ZERO
            masses = [ZERO, ZERO, ZERO]
            for lots in exploitations.values():
                aire = D(lots[0]["surface_lentille_ha"])
                volume = somme(lots, "net_alimentaire_paye_t")
                parts = ventilation_paliers(aire, volume)
                verifier(parts[0] <= aire and parts[1] <= aire and sum(parts) == volume, "Plafond exploitation-campagne")
                paiement_base += recette_bareme(aire, volume, tarifs)
                masses = [a + b for a, b in zip(masses, parts)]
            paiement = paiement_base + prime
            budget = paiement + cout_tri + cout_collecte + cout_sechage
            comparaison.append({
                "statut_donnees": "synthetique", "periode": periode, "bareme_id": identifiant,
                "cadre_commun": "conditions_synthetique_2027", "nombre_exploitations_campagnes": len(exploitations),
                "surface_cumulee_ha_campagne": surface, "brut_recu_t": somme(groupe, "brut_recu_t"),
                "net_alimentaire_paye_t": net, "palier_1_t": masses[0], "palier_2_t": masses[1], "palier_3_t": masses[2],
                "paiement_hors_prime_eur": paiement_base, "prime_service_eur": prime,
                "paiement_producteurs_eur": paiement, "prix_moyen_apres_prime_eur_t_nette": q(paiement / net),
                "recette_producteurs_eur_ha": q(paiement / surface),
                "solde_producteurs_hors_meca_eur_ha": q((paiement - cout_agri) / surface),
                "cout_tri_acheteur_eur": cout_tri, "cout_collecte_acheteur_eur": cout_collecte,
                "cout_sechage_acheteur_eur": cout_sechage, "budget_achat_collecte_tri_sechage_eur": budget,
                "budget_eur_t_nette_acceptee": q(budget / net),
            })
    return comparaison


def references_publiques():
    natup = "https://natup.coop/download/5775/"
    q2023 = "https://www.terresunivia.fr/fichiers/publications/qg-lentille-2023.pdf"
    q2024 = "https://www.terresinovia.fr/documents/20126/162983/fiche_Terres_Inovia_Terres_Univia_qual_graines_lentille-2024.pdf/35e91999-3cd8-a885-7ce7-2bf4de1c9e4c?t=1743435326312"
    q2025 = "https://www.terresinovia.fr/sites/default/files/2026-02/fiche-qualite-graines-lentille_2025.pdf"
    bareme = "https://www.union-agricole.fr/natup-souhaite-augmenter-les-surfaces-de-lentilles"
    donnees = [
        ("NATUP_COLLECTE_2023", 2023, "collecte", 89, "t", "NatUp", "filiere_lentille_NatUp", "base_brute_ou_nette_non_precisee", "Communique 18 septembre 2025", natup),
        ("NATUP_SURFACE_2023", 2023, "surface", 65, "ha", "NatUp", "filiere_lentille_NatUp", "ne_pas_deduire_un_taux_de_tri_du_ratio", "Communique 18 septembre 2025", natup),
        ("NATUP_COLLECTE_2024", 2024, "collecte", 273, "t", "NatUp", "filiere_lentille_NatUp", "base_brute_ou_nette_non_precisee", "Communique 18 septembre 2025", natup),
        ("NATUP_SURFACE_2024", 2024, "surface", 130, "ha", "NatUp", "filiere_lentille_NatUp", "273_divise_130_differe_du_rendement_2.25_cite_ne_pas_inferer_une_perte", "Communique 18 septembre 2025", natup),
        ("NATUP_COLLECTE_2025", 2025, "collecte", 558, "t", "NatUp", "filiere_lentille_NatUp", "base_brute_ou_nette_non_precisee", "Communique 18 septembre 2025", natup),
        ("NATUP_SURFACE_2025", 2025, "surface", "", "ha", "NatUp", "filiere_lentille_NatUp", "non_documentee_dans_cette_source_valeur_manquante_pas_zero", "Communique 18 septembre 2025", natup),
        ("QUALITE_2023_HUMIDITE", 2023, "humidite_moyenne", 13.1, "%", "Terres Inovia / Terres Univia", "34_echantillons_France", "moyenne_echantillons_non_historique_cooperative", "Fiche qualite lentille recolte 2023", q2023),
        ("QUALITE_2023_BRUCHE", 2023, "grains_bruches_moyenne", 10.2, "%_nombre_grains", "Terres Inovia / Terres Univia", "34_echantillons_France", "pas_un_taux_de_perte_massique_ni_de_refus_lots", "Fiche qualite lentille recolte 2023", q2023),
        ("QUALITE_2023_PROTEINES", 2023, "proteines_moyenne", 28.7, "%_matiere_seche", "Terres Inovia / Terres Univia", "34_echantillons_France", "pas_un_taux_sur_grain_humide", "Fiche qualite lentille recolte 2023", q2023),
        ("QUALITE_2024_HUMIDITE", 2024, "humidite_moyenne", 12.6, "%", "Terres Inovia / Terres Univia", "54_echantillons_France", "moyenne_echantillons_non_historique_cooperative", "Fiche qualite lentille recolte 2024", q2024),
        ("QUALITE_2024_BRUCHE", 2024, "grains_bruches_moyenne", 14.5, "%_nombre_grains", "Terres Inovia / Terres Univia", "54_echantillons_France", "pas_un_taux_de_perte_massique_ni_de_refus_lots", "Fiche qualite lentille recolte 2024", q2024),
        ("QUALITE_2024_PROTEINES", 2024, "proteines_moyenne", 28.4, "%_matiere_seche", "Terres Inovia / Terres Univia", "54_echantillons_France", "pas_un_taux_sur_grain_humide", "Fiche qualite lentille recolte 2024", q2024),
        ("QUALITE_2025_HUMIDITE", 2025, "humidite_moyenne", 11.8, "%", "Terres Inovia / Terres Univia", "60_echantillons_France", "moyenne_echantillons_non_historique_cooperative", "Fiche qualite lentille recolte 2025", q2025),
        ("QUALITE_2025_BRUCHE", 2025, "grains_bruches_moyenne", 24.4, "%_nombre_grains", "Terres Inovia / Terres Univia", "40_echantillons_analyses_bruche", "pas_un_taux_de_perte_massique_ni_de_refus_lots", "Fiche qualite lentille recolte 2025", q2025),
        ("QUALITE_2025_PROTEINES", 2025, "proteines_moyenne", 29.9, "%_matiere_seche", "Terres Inovia / Terres Univia", "60_echantillons_France", "pas_un_taux_sur_grain_humide", "Fiche qualite lentille recolte 2025", q2025),
        ("NATUP_BAREME_PREMIERE_T", "2023-2024", "prix_premiere_tonne_ha", 900, "EUR_t", "L'Union agricole / entretien NatUp", "lentille_NatUp_2023_reconduit_2024", "article_public_pas_contrat_signe_assiette_nette_convention_de_simulation", "Article 18 septembre 2023", bareme),
        ("NATUP_BAREME_DEUXIEME_T", "2023-2024", "prix_deuxieme_tonne_ha", 700, "EUR_t", "L'Union agricole / entretien NatUp", "lentille_NatUp_2023_reconduit_2024", "lecture_marginale_reconstituee", "Article 18 septembre 2023", bareme),
        ("NATUP_BAREME_SUIVANTES", "2023-2024", "prix_au_dela_2_t_ha", 600, "EUR_t", "L'Union agricole / entretien NatUp", "lentille_NatUp_2023_reconduit_2024", "formulation_article_ambigue_lecture_marginale_reconstituee", "Article 18 septembre 2023", bareme),
    ]
    champs = ["reference_id", "campagne", "indicateur", "valeur", "unite", "organisme", "perimetre", "precision", "provenance", "url"]
    return [{"statut_donnees": "reference_publique", **dict(zip(champs, ligne))} for ligne in donnees]


def controler(lignes, resumes, comparaison, config, contrats):
    verifier(len(lignes) == 140, "140 exploitations-campagnes attendues")
    verifier(len({l["lot_id"] for l in lignes}) == 140, "Identifiants de lots uniques")
    verifier(len({l["ferme_id"] for l in lignes}) == 20, "20 fermes attendues")
    rotation = defaultdict(list)
    for ligne in lignes:
        verifier(ligne["statut_donnees"] == "synthetique", "Statut synthétique obligatoire")
        verifier(ligne["recolte_brute_t"] == ligne["brut_recu_t"] + ligne["ecarts_prenettoyage_t"], "Bilan pré-nettoyage")
        verifier(ligne["brut_recu_t"] == ligne["eau_retiree_t"] + ligne["ecarts_tri_t"] + ligne["refus_qualite_t"] + ligne["net_alimentaire_paye_t"], "Bilan matières exact à six décimales")
        verifier(ligne["ecarts_tri_t"] == ligne["ecarts_impuretes_tri_t"] + ligne["ecarts_defauts_tri_t"], "Écarts de tri")
        verifier(ligne["masse_defauts_avant_tri_t"] == ligne["ecarts_defauts_tri_t"] + ligne["masse_defauts_restants_apres_tri_t"], "Conservation de la matière défectueuse")
        verifier(ligne["defauts_apres_tri_pct"] == q(100 * ligne["masse_defauts_restants_apres_tri_t"] / ligne["net_apres_tri_avant_agreage_t"]), "Défauts résiduels compatibles avec les masses")
        verifier(ligne["recolte_brute_t"] == tonnes(ligne["surface_lentille_ha"] * ligne["rendement_brut_t_ha"]), "Surface × rendement")
        verifier(ligne["eau_retiree_t"] >= 0, "Aucune masse ajoutée au séchage")
        verifier(ligne["humidite_apres_tri_pct"] <= ligne["humidite_reception_pct"], "Pas de réhumidification")
        verifier(ligne["paiement_final_producteur_eur"] == ligne["paiement_avant_prime_eur"] + ligne["prime_service_eur"], "Prime comptée une fois")
        verifier(ligne["paiement_avant_prime_eur"] == q(ligne["net_alimentaire_paye_t"] * ligne["prix_paye_avant_prime_eur_t_nette"]), "Paiement des tonnes nettes seulement")
        verifier(ligne["solde_producteur_hors_meca_eur"] == ligne["paiement_final_producteur_eur"] - ligne["charges_intrants_hors_meca_eur"] - ligne["cout_prenettoyage_producteur_eur"], "Charges producteur distinctes du tri acheteur")
        verifier(ligne["budget_achat_collecte_tri_sechage_eur"] == ligne["paiement_final_producteur_eur"] + ligne["cout_tri_acheteur_eur"] + ligne["cout_collecte_acheteur_eur"] + ligne["cout_sechage_acheteur_eur"], "Budget acheteur")
        verifier(D(350) <= ligne["charges_intrants_hors_meca_eur_ha"] <= D(600), "Bornes intrants")
        if ligne["statut_lot"] == "refuse_total":
            verifier(ligne["net_alimentaire_paye_t"] == 0 and ligne["paiement_final_producteur_eur"] == 0 and ligne["refus_qualite_t"] > 0, "Refus sans recette ou valorisation")
            verifier(ligne["cout_tri_acheteur_eur"] > 0, "Tri déjà effectué facturé même si refus")
        else:
            ql = contrats["synthetique_2027"]["qualite_apres_tri"]
            verifier(ligne["humidite_apres_tri_pct"] <= D(ql["humidite_max_pct"]) and ligne["defauts_apres_tri_pct"] <= D(ql["defauts_max_pct"]) and ligne["insectes_vivants_apres_tri_nombre_echantillon"] == 0 and ligne["moisissure_detectee"] == "non", "Qualité des lots acceptés")
        rotation[ligne["bloc_rotation_id"]].append(ligne["campagne"])
    for annees in rotation.values():
        verifier(all(b - a >= 6 for a, b in zip(sorted(annees), sorted(annees)[1:])), "Retour de lentille avant six ans")
    for resume in resumes:
        verifier(resume["surface_lentille_ha"] == 220, "Surface annuelle 220 ha")
        verifier(resume["recolte_brute_t"] == resume["ecarts_prenettoyage_t"] + resume["eau_retiree_t"] + resume["ecarts_tri_t"] + resume["refus_qualite_t"] + resume["net_alimentaire_paye_t"], "Bilan annuel")
    for periode in {l["periode"] for l in comparaison}:
        cas = [l for l in comparaison if l["periode"] == periode]
        for champ in ["net_alimentaire_paye_t", "cout_tri_acheteur_eur", "cout_collecte_acheteur_eur", "cout_sechage_acheteur_eur", "prime_service_eur"]:
            verifier(len({l[champ] for l in cas}) == 1, f"Comparaison à conditions identiques : {champ}")
        for cas_ligne in cas:
            verifier(cas_ligne["palier_1_t"] <= cas_ligne["surface_cumulee_ha_campagne"] and cas_ligne["palier_2_t"] <= cas_ligne["surface_cumulee_ha_campagne"], "Plafonds agrégés")
            verifier(cas_ligne["paiement_producteurs_eur"] == cas_ligne["paiement_hors_prime_eur"] + cas_ligne["prime_service_eur"], "Paiement comparaison")
    # Aux bornes 1 et 2 t/ha : continuité et aucune tarification rétroactive.
    verifier(recette_bareme(D(10), D(16), [1000, 750, 650]) == D(14500), "Exemple marginal 10 ha / 16 t")
    verifier(recette_bareme(D(10), D(20), [1000, 750, 650]) == D(17500), "Plafond deuxième palier")
    verifier(recette_bareme(D(10), D(21), [1000, 750, 650]) == D(18150), "Début troisième palier")
    nombre_refus = sum(l["statut_lot"] == "refuse_total" for l in lignes)
    verifier(D("0.02") <= D(nombre_refus) / len(lignes) <= D("0.05"), "Refus entre 2 et 5 % des lots")
    return {"statut_donnees": "synthetique", "controles": "valides", "nombre_lots": len(lignes), "nombre_fermes": 20, "nombre_campagnes": 7, "surface_annuelle_ha": 220, "nombre_refus_totaux": nombre_refus, "refus_pct_lots": str(q(100 * D(nombre_refus) / len(lignes))), "precision_bilan_matieres_t": "0.000001", "precision_monnaie_eur": "0.01", "rotation_minimum_ans": 6, "aucune_validation_statistique_du_pilote": True}


def generer(dossier, config, contrats):
    dossier.mkdir(parents=True, exist_ok=True)
    lignes = fabriquer_lots(config, contrats)
    resumes = resumer(lignes, config)
    comparaison = comparer(lignes, config, contrats)
    bilan = controler(lignes, resumes, comparaison, config, contrats)
    ecrire_csv(dossier / "historique_lots_synthetiques.csv", lignes)
    ecrire_csv(dossier / "resume_campagnes_synthetiques.csv", resumes)
    ecrire_csv(dossier / "comparaison_baremes_synthetiques.csv", comparaison)
    ecrire_csv(dossier / "references_publiques.csv", references_publiques())
    return bilan


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DOSSIER / "config.json")
    parser.add_argument("--contrats", type=Path, default=DOSSIER / "contrats.json")
    parser.add_argument("--sortie", type=Path, default=DOSSIER)
    parser.add_argument("--verifier-reproductibilite", action="store_true")
    args = parser.parse_args()
    config, contrats = lire_json(args.config), lire_json(args.contrats)
    verifier(config["cout_sechage_eur_t_recue_point_humidite"] == contrats["synthetique_2027"]["sechage"]["eur_t_recue_point_humidite"], "Configuration séchage cohérente avec contrat")
    verifier(config["humidite_seuil_sechage_pct"] == contrats["synthetique_2027"]["sechage"]["seuil_declenchement_pct"], "Seuil séchage cohérent avec contrat")
    verifier(config["humidite_cible_sechage_pct"] == contrats["synthetique_2027"]["sechage"]["cible_pct"], "Cible séchage cohérente avec contrat")
    bilan = generer(args.sortie, config, contrats)
    if args.verifier_reproductibilite:
        with tempfile.TemporaryDirectory(prefix="pilote_300t_") as temporaire:
            autre = Path(temporaire)
            generer(autre, config, contrats)
            empreintes = {}
            for path in sorted(autre.glob("*.csv")):
                verifier(path.read_bytes() == (args.sortie / path.name).read_bytes(), f"Reproductibilité : {path.name}")
                empreintes[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
            bilan["double_generation_identique"] = True
            bilan["sha256_csv"] = empreintes
    print(json.dumps(bilan, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
