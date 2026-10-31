"""Économie commune aux benchmarks des cinq légumineuses.

Les charges, l'aide, le bénéfice de rotation et la part refusée proviennent de
``data/hypotheses.yaml`` (lentille et socle blé) et ``data/cultures.yaml``.
Le besoin de paiement reste signé : les aides et la rotation peuvent suffire à
égaler la marge du blé sans paiement. Seul le coefficient contractuel est borné à 0.

Les trois formes paient les tonnes ACCEPTÉES après tri. ``fixed`` fixe un prix
en €/t à la signature ; ``indexed`` fixe un multiplicateur sans unité, appliqué
au prix du blé à la récolte. Son prix en €/t n'est donc pas fixé à la signature.
``tiers`` fixe un premier prix en €/t et les ratios marginaux 0,7 et 0,4.
Ses bornes, 0,7 et 1,4 fois le rendement accepté moyen PASSÉ, sont des hypothèses
de benchmark préspecifiées : elles ne sont pas estimées sur l'année à prédire.
"""

import numpy as np

TIER_RATIOS = (0.7, 0.4)
TIER_BOUND_FACTORS = (0.7, 1.4)
MIN_TIER_BOUND = 1e-9  # t/ha ; garde les bornes strictement positives au cas limite.


def crop_hypotheses(culture: str) -> dict:
    """Même convention que ``model.hyp_values``, adaptée à la culture demandée.

    ``charges_lentille`` est conservé pour compatibilité avec le moteur existant ;
    ``charges_culture`` est son alias explicite pour le benchmark multicultures.
    Les étiquettes/source des paramètres restent dans les deux fichiers YAML.
    """
    import yaml

    from common import DATA, hypotheses
    from model import hyp_values

    h = hyp_values(hypotheses())
    if culture != "lentille":
        cultures = yaml.safe_load((DATA / "cultures.yaml").read_text(encoding="utf-8"))
        if culture not in cultures:
            raise ValueError(f"Culture inconnue : {culture}")
        c = cultures[culture]
        h.update(charges_lentille=c["charges_eur_ha"]["valeur"],
                 aide=c["aide_eur_ha"]["valeur"],
                 rotation=c["rotation_eur_ha"]["valeur"],
                 qualite=c["part_refusee"]["valeur"])
        h["bonus"] = h["aide"] + h["rotation"]
    h["charges_culture"] = h["charges_lentille"]
    return h


def _finite(value, name):
    out = np.asarray(value, dtype=float)
    if not np.all(np.isfinite(out)):
        raise ValueError(f"{name} doit contenir des valeurs finies")
    return out


def signed_required_income(p_w, y_w, c_w, c_c, aid=0.0, rotation=0.0):
    """Besoin signé de paiement (€/ha) pour égaler la marge du blé."""
    args = [_finite(v, k) for v, k in zip(
        (p_w, y_w, c_w, c_c, aid, rotation),
        ("p_w", "y_w", "c_w", "c_c", "aid", "rotation"))]
    p_w, y_w, c_w, c_c, aid, rotation = np.broadcast_arrays(*args)
    return p_w * y_w - c_w + c_c - aid - rotation


def accepted_yield(y_raw, q):
    """Tonnes acceptées par hectare, avec q la fraction refusée au tri."""
    y_raw, q = np.broadcast_arrays(_finite(y_raw, "y_raw"), _finite(q, "q"))
    if np.any(y_raw < 0) or np.any((q < 0) | (q > 1)):
        raise ValueError("Rendement brut >= 0 et fraction refusée dans [0, 1] requis")
    return y_raw * (1.0 - q)


def tier_bounds(past_mean_accepted):
    """Bornes en t/ha à figer avant l'année test, sans rendement courant."""
    mean = _finite(past_mean_accepted, "past_mean_accepted")
    if mean.ndim != 0 or mean < 0:
        raise ValueError("past_mean_accepted doit être une moyenne scalaire >= 0")
    first = max(MIN_TIER_BOUND, TIER_BOUND_FACTORS[0] * float(mean))
    return first, 2.0 * first


def contract_basis(shape, accepted, p_w=None, past_mean_accepted=None,
                   r2=TIER_RATIOS[0], r3=TIER_RATIOS[1]):
    """Base de paiement : coefficient × base = €/ha, selon la forme du contrat.

    Pour ``indexed``, p_w est le prix du blé du scénario ou de la récolte évaluée,
    et le coefficient calibré avant l'année est un multiplicateur sans unité.
    Pour ``tiers``, past_mean_accepted vient exclusivement des années antérieures.
    """
    accepted = _finite(accepted, "accepted")
    if np.any(accepted < 0):
        raise ValueError("Le rendement accepté doit être >= 0")
    if shape == "fixed":
        return accepted.copy()
    if shape == "indexed":
        if p_w is None:
            raise ValueError("Le contrat indexé exige le prix du blé à la récolte")
        p_w = _finite(p_w, "p_w")
        if np.any(p_w < 0):
            raise ValueError("Le prix du blé doit être >= 0")
        return accepted * p_w
    if shape in ("tiers", "tiered"):
        if past_mean_accepted is None:
            raise ValueError("Les tranches exigent le rendement accepté moyen passé")
        ratios = _finite([r2, r3], "ratios")
        if not 0 <= ratios[1] <= ratios[0] <= 1:
            raise ValueError("Les ratios doivent satisfaire 0 <= r3 <= r2 <= 1")
        b1, b2 = tier_bounds(past_mean_accepted)
        return (np.minimum(accepted, b1) + r2 * np.clip(accepted - b1, 0, b2 - b1)
                + r3 * np.maximum(accepted - b2, 0))
    raise ValueError(f"Forme contractuelle inconnue : {shape}")


def required_coefficient(need, basis):
    """Seuil signé par scénario, sans rejet ni logarithme des besoins négatifs.

    Une base nulle ne peut satisfaire un besoin positif (+inf), et satisfait déjà
    un besoin nul ou négatif (-inf), quel que soit le coefficient non négatif.
    """
    need, basis = np.broadcast_arrays(_finite(need, "need"), _finite(basis, "basis"))
    if np.any(basis < 0):
        raise ValueError("La base contractuelle doit être >= 0")
    out = np.where(need > 0, np.inf, -np.inf)
    return np.divide(need, basis, out=out, where=basis > 0)


def calibrate_coefficient(need, basis, coverage=0.8):
    """Coefficient minimal >= 0 couvrant la part visée, égalités comprises.

    Quantile empirique ``inverted_cdf`` : aucune interpolation entre scénarios.
    Une couverture inatteignable à coefficient fini est signalée explicitement.
    """
    if not 0 < coverage <= 1:
        raise ValueError("La couverture doit appartenir à ]0, 1]")
    required = required_coefficient(need, basis)
    if not required.size:
        raise ValueError("Au moins un scénario de calibration est requis")
    coefficient = max(0.0, float(np.quantile(required, coverage, method="inverted_cdf")))
    if not np.isfinite(coefficient):
        raise ValueError("Couverture impossible avec un coefficient contractuel fini")
    return coefficient


def evaluate(coefficient, basis, need, accepted):
    """Paiement, marge tenue, déficit (€/ha) et prix effectif (€/t acceptée).

    La comparaison au seuil inversé conserve les égalités à un arrondi machine
    près lorsque ``(need / basis) * basis`` retombe juste sous ``need``.
    Aucun prix effectif n'est défini sans tonne acceptée : il vaut alors NaN.
    """
    coefficient, basis, need, accepted = np.broadcast_arrays(
        _finite(coefficient, "coefficient"), _finite(basis, "basis"),
        _finite(need, "need"), _finite(accepted, "accepted"))
    if np.any(coefficient < 0) or np.any(accepted < 0):
        raise ValueError("Coefficient et rendement accepté doivent être >= 0")
    required = required_coefficient(need, basis)
    paid = coefficient * basis
    held = coefficient >= required
    effective = np.divide(paid, accepted, out=np.full_like(paid, np.nan), where=accepted > 0)
    return {"paid_eur_ha": paid, "held": held,
            "shortfall_eur_ha": np.where(held, 0.0, np.maximum(need - paid, 0.0)),
            "effective_price_eur_t": effective}


def expected_unit_cost(coefficient, basis, accepted):
    """Coût moyen par tonne : E[paiement €/ha] / E[tonnes acceptées/ha].

    Ce ratio de moyennes pondère correctement les tonnes ; ce n'est pas la
    moyenne des prix effectifs des scénarios. Sans tonne, le coût vaut NaN.
    """
    coefficient, basis, accepted = np.broadcast_arrays(
        _finite(coefficient, "coefficient"), _finite(basis, "basis"),
        _finite(accepted, "accepted"))
    if np.any(coefficient < 0) or np.any(basis < 0) or np.any(accepted < 0):
        raise ValueError("Coefficient, base et rendement accepté doivent être >= 0")
    if not accepted.size:
        raise ValueError("Au moins un scénario est requis")
    mean_accepted = float(np.mean(accepted))
    return float(np.mean(coefficient * basis) / mean_accepted) if mean_accepted > 0 else float("nan")
