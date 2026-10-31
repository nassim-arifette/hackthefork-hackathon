"""Lettre d'accompagnement du contrat, rédigée par un LLM (Claude sur Amazon Bedrock).

Le LLM ne produit aucun chiffre : il reçoit les chiffres calculés et rédige autour.
Chaque nombre du texte renvoyé est comparé aux chiffres fournis ; un texte qui en
contient un autre est rejeté. La réponse est mise en cache dans app/src/data/lettre.json.

Usage (voir docs/AWS.md) :
  BEDROCK_MODEL_ID=<identifiant exact> python3 06_lettre_llm.py
L'identifiant se lit avec `aws bedrock list-foundation-models --region us-east-1` ;
il n'est jamais deviné. Sans identifiant ni accès AWS, le script n'écrit rien d'autre
qu'un fichier vide, et l'application n'affiche que le contrat structuré.
"""
import json
import os
import re
import time
from pathlib import Path

# Chemin calculé ici plutôt qu'importé de common.py : le script tourne seul dans
# AWS CloudShell, avec boto3 pour toute dépendance.
APP_DATA = Path(__file__).resolve().parents[1] / "app" / "src" / "data"

PROMPT = """Tu rédiges une courte lettre d'une coopérative à un agriculteur d'Île-de-France,
pour accompagner une proposition de contrat lentille payé selon un barème par tranches.
Utilise uniquement les chiffres fournis, écrits exactement comme ci-dessous ; n'en ajoute
aucun, n'en arrondis aucun. Pas de formule creuse. Cinq phrases au plus, en français, ton
direct et respectueux. Dis clairement ce que le barème garantit et ce qu'il ne garantit pas.

Sens des chiffres, à respecter :
- Le barème paie plus cher la première tonne acceptée par hectare : c'est celle qui manque
  les mauvaises années. Les tonnes suivantes sont payées moins cher.
- « 8 années sur 10 » veut dire : dans 8 années simulées sur 10, la lentille payée selon ce
  barème rapporte au moins autant par hectare que le blé. Ce n'est ni une mesure de la
  fiabilité de la coopérative, ni une garantie de revenu.
- Le prix est payé sur les tonnes acceptées au tri pour l'alimentation humaine.
- Les deux autres années sur dix, et en cas de récolte faible, la lentille peut rapporter
  moins que le blé.

Chiffres :
{chiffres}"""


def chiffres() -> dict:
    t = json.loads((APP_DATA / "thresholds.json").read_text())
    meta = json.loads((APP_DATA / "meta.json").read_text())
    contrats = json.loads((APP_DATA / "contrats.json").read_text())
    d77 = next(d for d in t["par_departement"] if d["dep"] == "77")
    p1, p2, p3 = next(c for c in contrats["calibres"] if c["id"] == "paliers")["paliers"]
    fr = lambda x: f"{x:,}".replace(",", " ").replace(".", ",")
    return {
        "barème garanti": (f"{fr(p1)} €/t jusqu'à 1 t/ha acceptée, {fr(p2)} €/t de 1 à 2 t/ha, "
                           f"{fr(p3)} €/t au-delà de 2 t/ha, départ ferme"),
        "fiabilité": "8 années sur 10",
        "durée": "3 campagnes",
        "rendement faible, une année sur dix": f"{fr(d77['rendement_lentille_q10_tha'])} t/ha",
        "volume du pilote": f"{fr(meta['hypotheses']['volume_pilote_t']['valeur'])} t",
        "tonnes payées": "tonnes acceptées au tri pour l'alimentation humaine",
        "campagne": str(meta["campagne"]),
    }


def numbers(text: str) -> set[str]:
    """Nombres d'un texte, normalisés (espaces fines retirées, virgule décimale)."""
    t = text.replace(" ", " ").replace(" ", " ")
    found = re.findall(r"\d+(?:[ ]\d{3})*(?:,\d+)?", t)
    return {f.replace(" ", "") for f in found}


def verify(text: str, allowed: dict) -> bool:
    ok = set().union(*(numbers(v) for v in allowed.values())) | {"8", "10"}
    return numbers(text) <= ok


def call_bedrock(model_id: str, prompt: str) -> str:
    import boto3  # importé seulement si Bedrock est utilisé
    client = boto3.client("bedrock-runtime", region_name="us-east-1")
    from botocore.exceptions import ClientError
    for attempt in range(4):
        try:
            # Pas de `temperature` : les modèles Claude récents la refusent.
            r = client.converse(modelId=model_id, messages=[{"role": "user", "content": [{"text": prompt}]}],
                                inferenceConfig={"maxTokens": 2000})
            # La réponse peut commencer par un bloc de raisonnement : on garde les blocs de texte.
            blocks = r["output"]["message"]["content"]
            text = "\n".join(b["text"] for b in blocks if "text" in b).strip()
            if not text:
                raise RuntimeError(f"Réponse sans texte (arrêt : {r.get('stopReason')}, blocs : {[list(b) for b in blocks]})")
            return text
        except ClientError as e:
            # On ne réessaie que les limites de débit ; une requête invalide échoue tout de suite.
            if e.response["Error"]["Code"] != "ThrottlingException" or attempt == 3:
                raise
            time.sleep(2 ** (attempt + 1))  # quota d'environ 1 requête par seconde
    return ""


def main():
    model_id = os.environ.get("BEDROCK_MODEL_ID")
    c = chiffres()
    out = {"source": "aucune", "modele": None, "texte": None, "chiffres": c}
    if model_id:
        prompt = PROMPT.format(chiffres="\n".join(f"- {k} : {v}" for k, v in c.items()))
        for _ in range(3):
            text = call_bedrock(model_id, prompt)
            if verify(text, c):
                out |= {"source": "llm", "modele": model_id, "texte": text}
                break
            time.sleep(1.2)
        else:
            print("Texte rejeté trois fois : un nombre n'était pas dans les chiffres fournis.")
    else:
        print("BEDROCK_MODEL_ID absent : aucune lettre générée.")
    (APP_DATA / "lettre.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
