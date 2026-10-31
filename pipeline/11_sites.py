"""Étape 11 : les sites existants de collecte et de stockage de grains autour de l'Île-de-France.

Le site de collecte du scénario est fictif. Pour confronter son emplacement au terrain, on liste
les établissements qui collectent déjà des grains : base Sirene de l'Insee, interrogée par l'API
Recherche d'entreprises (recherche-entreprises.api.gouv.fr). On garde les entreprises du commerce
de gros de céréales et de semences (NAF 46.21Z : coopératives et négociants) et, parmi leurs
établissements actifs, diffusibles et géolocalisés de la zone (hors entrepreneurs individuels), ceux dont l'activité est ce même
commerce (46.21Z) ou l'entreposage (52.10B, les silos). Sirene ne distingue pas un silo d'un bureau
ou d'un magasin d'approvisionnement : ce sont des sites candidats, pas un inventaire des capacités.

Pour chaque site : distance moyenne, pondérée par les tonnes, des parcelles de blé les plus proches
qu'il faut réunir pour le volume du pilote et pour celui de l'ambition (même calcul que le
« meilleur emplacement » de l'application), et coût de collecte qui en découle. Pour la zone du
Maillon : distance de chaque parcelle de légumineuses déclarée au RPG 2025 au site le plus proche.

Les réponses de l'API sont gardées dans data_raw/sirene/ ; supprimer ce dossier pour les relire.
Sorties : data/sites_collecte.json et app/src/data/sites.json.
"""
import json
import time
from datetime import date

import numpy as np
import requests

from common import APP_DATA, DATA, RAW, hypotheses, val

API = "https://recherche-entreprises.api.gouv.fr/search"
# Départements agricoles franciliens et leurs voisins : un silo juste de l'autre côté de la limite
# régionale peut collecter des parcelles franciliennes.
DEPS = ["77", "78", "91", "95", "02", "10", "27", "28", "45", "51", "60", "89"]
NAF_ENTREPRISE = "46.21Z"
NAF_SITE = {"46.21Z": "commerce de grains", "52.10B": "entreposage"}
MARGE_KM = 15  # sites retenus jusqu'à 15 km autour des parcelles franciliennes
CACHE = RAW / "sirene"
RAD = np.pi / 180


UL = ("siren", "nom_complet", "nature_juridique", "activite_principale")
ET = ("siret", "activite_principale", "etat_administratif", "statut_diffusion_etablissement",
      "latitude", "longitude", "libelle_commune", "commune", "est_siege")


def allege(d: dict) -> dict:
    """Ne garde que les champs utiles : ni dirigeants, ni adresses, ni entrepreneurs individuels dans le dépôt public."""
    return {"extrait_le": d.get("extrait_le", date.today().isoformat()),
            "total_results": d.get("total_results"), "total_pages": d.get("total_pages"),
            "results": [{k: u.get(k) for k in UL}
                        | {"matching_etablissements": [{k: e.get(k) for k in ET} for e in u.get("matching_etablissements", [])]}
                        for u in d.get("results", []) if not str(u.get("nature_juridique", "")).startswith("1")]}


def page(dep: str, k: int) -> dict:
    """Une page de résultats, depuis le cache ou l'API (avec reprises : la connexion est instable)."""
    f = CACHE / f"{dep}_{k:02d}.json"
    if f.exists():
        return json.loads(f.read_text())
    params = {"activite_principale": NAF_ENTREPRISE, "departement": dep, "etat_administratif": "A",
              "per_page": 25, "page": k, "limite_matching_etablissements": 100}
    for attempt in range(12):
        try:
            r = requests.get(API, params=params, timeout=30)
            if r.status_code == 429:
                time.sleep(2 + attempt * 2)
                continue
            r.raise_for_status()
            d = allege(r.json())
            CACHE.mkdir(parents=True, exist_ok=True)
            f.write_text(json.dumps(d, ensure_ascii=False))
            time.sleep(0.2)  # l'API accepte 7 requêtes par seconde
            return d
        except (requests.RequestException, ValueError):
            if attempt == 11:
                raise
            time.sleep(min(20, 2 ** (attempt + 1)))
    raise RuntimeError(f"API Recherche d'entreprises : échec pour {dep}, page {k}")


def etablissements() -> list[dict]:
    out, vus = [], set()
    for dep in DEPS:
        k, total = 1, 1
        while k <= total:
            d = page(dep, k)
            total = d.get("total_pages", 1)
            for u in d["results"]:
                # Pas d'entrepreneurs individuels : leur dénomination est le nom d'une personne.
                if str(u.get("nature_juridique", "")).startswith("1"):
                    continue
                coop = str(u.get("nature_juridique", "")).startswith("63")
                for e in u.get("matching_etablissements", []):
                    if (e.get("etat_administratif") != "A" or e.get("activite_principale") not in NAF_SITE
                            or e.get("latitude") in (None, "") or e.get("longitude") in (None, "")
                            or e.get("statut_diffusion_etablissement", "O") != "O" or e["siret"] in vus):
                        continue
                    vus.add(e["siret"])
                    out.append({"siret": e["siret"], "entreprise": u["nom_complet"], "cooperative": coop,
                                "naf": e["activite_principale"], "commune": e.get("libelle_commune", "").title(),
                                "dep": dep, "lon": round(float(e["longitude"]), 5), "lat": round(float(e["latitude"]), 5)})
            k += 1
    return out


def km(lon1, lat1, lon2, lat2):
    a = (np.sin((lat2 - lat1) * RAD / 2) ** 2
         + np.cos(lat1 * RAD) * np.cos(lat2 * RAD) * np.sin((lon2 - lon1) * RAD / 2) ** 2)
    return 2 * 6371.0 * np.arcsin(np.sqrt(a))


def km_moyen(d: np.ndarray, t: np.ndarray, volume: float) -> float:
    """Distance moyenne pondérée par les tonnes des parcelles les plus proches réunissant `volume`."""
    o = np.argsort(d)
    cum = np.cumsum(t[o])
    j = int(np.searchsorted(cum, volume))
    prise = t[o][: j + 1].copy()
    prise[-1] -= cum[j] - volume  # dernière parcelle prise en partie
    return float((prise * d[o][: j + 1]).sum() / volume)


def main():
    H = hypotheses()
    detour, forfait, kappa = val(H, "facteur_detour_route"), val(H, "forfait_collecte_eur_t"), val(H, "cout_transport_eur_t_km")
    volumes = {"pilote": val(H, "volume_pilote_t"), "ambition": val(H, "volume_vise_t")}
    scenario = val(H, "site_acheteur")

    parc = json.loads((APP_DATA / "parcels.json").read_text())
    ble = [p for p in parc if p[2] == "ble"]
    lon = np.array([p[8] for p in ble]); lat = np.array([p[9] for p in ble]); t = np.array([p[6] for p in ble])
    tout_lon = np.array([p[8] for p in parc]); tout_lat = np.array([p[9] for p in parc])

    sites = etablissements()
    print(f"Établissements Sirene retenus dans les {len(DEPS)} départements : {len(sites)}")
    # Garder les sites à moins de MARGE_KM (à vol d'oiseau) d'une parcelle francilienne.
    proches = []
    for s in sites:
        if km(tout_lon, tout_lat, s["lon"], s["lat"]).min() <= MARGE_KM:
            proches.append(s)
    sites = proches
    print(f"Dont à moins de {MARGE_KM} km d'une parcelle francilienne : {len(sites)}")

    def evalue(site_lon, site_lat):
        d = km(lon, lat, site_lon, site_lat) * detour
        return {k: round(km_moyen(d, t, v), 1) for k, v in volumes.items()}

    for s in sites:
        s["km_moyen"] = evalue(s["lon"], s["lat"])
    ref = evalue(*scenario)
    meilleurs = {k: min(range(len(sites)), key=lambda i: sites[i]["km_moyen"][k]) for k in volumes}
    for k, i in meilleurs.items():
        s = sites[i]
        print(f"Meilleur site existant ({k}, {volumes[k]:.0f} t) : {s['commune']} ({s['entreprise']}), "
              f"{s['km_moyen'][k]} km en moyenne contre {ref[k]} km au site du scénario")

    # Zone du Maillon : légumineuses déclarées au RPG 2025, distance au site existant le plus proche.
    m = json.loads((APP_DATA / "maillon.json").read_text())
    leg = [p for p in m["parcelles"] if p[1]]
    cx = np.array([np.mean(p[6][0::2]) for p in leg]); cy = np.array([np.mean(p[6][1::2]) for p in leg])
    surf = np.array([p[5] for p in leg])
    slon = np.array([s["lon"] for s in sites]); slat = np.array([s["lat"] for s in sites])
    dmin = np.array([(km(slon, slat, x, y) * detour).min() for x, y in zip(cx, cy)])
    maillon = {"n_parcelles": len(leg), "surface_ha": round(float(surf.sum()), 1),
               "km_moyen_pondere_surface": round(float((dmin * surf).sum() / surf.sum()), 1),
               "km_max": round(float(dmin.max()), 1),
               "part_surface_moins_10_km": round(float(surf[dmin <= 10].sum() / surf.sum()), 3)}
    print("Maillon, légumineuses 2025 → site existant le plus proche :", maillon)

    n_coop = sum(s["cooperative"] for s in sites)
    meta = {
        "source": "Base Sirene (Insee), API Recherche d'entreprises (recherche-entreprises.api.gouv.fr)",
        "url": "https://recherche-entreprises.api.gouv.fr/docs/",
        "date_extraction": min(json.loads(f.read_text())["extrait_le"] for f in CACHE.glob("*.json")),
        "etiquette": "mesure",
        "selection": (f"Entreprises NAF {NAF_ENTREPRISE} actives, hors entrepreneurs individuels ; établissements actifs, diffusibles, géolocalisés, "
                      f"NAF 46.21Z ou 52.10B, à moins de {MARGE_KM} km d'une parcelle francilienne"),
        "limite": "Sirene ne distingue pas un silo d'un bureau ou d'un magasin : sites candidats, capacités inconnues",
        "departements": DEPS, "n_sites": len(sites), "n_cooperatives": n_coop,
        "volumes_t": volumes, "detour": detour, "forfait_eur_t": forfait, "kappa_eur_t_km": kappa,
        "scenario": {"site": scenario, "km_moyen": ref},
        "meilleur": {k: {"index": i, "commune": sites[i]["commune"], "entreprise": sites[i]["entreprise"],
                         "km_moyen": sites[i]["km_moyen"][k],
                         "gain_collecte_eur_t": round(kappa * (ref[k] - sites[i]["km_moyen"][k]), 1)}
                     for k, i in meilleurs.items()},
        "maillon": maillon,
    }
    (DATA / "sites_collecte.json").write_text(json.dumps(meta | {"sites": sites}, ensure_ascii=False, indent=1))
    # Pour l'application : [lon, lat, commune, entreprise, naf, coopérative, km pilote, km ambition].
    app = meta | {"sites": [[s["lon"], s["lat"], s["commune"], s["entreprise"], s["naf"], int(s["cooperative"]),
                             s["km_moyen"]["pilote"], s["km_moyen"]["ambition"]] for s in sites]}
    (APP_DATA / "sites.json").write_text(json.dumps(app, ensure_ascii=False, separators=(",", ":")))
    print(f"{len(sites)} sites ({n_coop} de coopératives) → data/sites_collecte.json, app/src/data/sites.json")


if __name__ == "__main__":
    main()
