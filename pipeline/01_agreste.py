"""Construit le panel de rendements blé tendre d'hiver, lentille et autres légumineuses (Agreste SAA 2010-2025).

Sortie : data/panel_rendements.csv, une ligne par département × année × culture.
Filtres documentés dans docs/MODELE.md §1 :
- surface ≥ 50 ha et rendement renseigné ;
- statut qualité 1 ou 2 (le statut 3 contient des rendements visiblement imputés) ;
- séries de rendement identiques entre départements regroupées (estimations communes).
"""
import zipfile

import numpy as np
import pandas as pd

from common import AGRESTE_URL, DATA, RAW, YEARS, download

CULTURES = {
    "01 - Blé tendre d'hiver et épeautre": "ble",
    "40 - Lentilles (y compris semences)": "lentille",
    # Autres légumineuses, pour le même moteur (pipeline/09_cultures.py).
    "43 - Pois chiches (y compris semences)": "pois_chiche",
    "39 - Haricots secs (y compris semences)": "haricot",
    "41 - Pois protéagineux": "pois",
    "38 - Féveroles et fèves": "feverole",
}
SURFACE_MIN_HA = 50


def load_cop() -> pd.DataFrame:
    z = download(AGRESTE_URL, RAW / "agreste" / "saa.zip")
    out = RAW / "agreste" / "x"
    xlsx = out / "SAA_2010-2025_provisoires_donnees_departementales.xlsx"
    if not xlsx.exists():
        with zipfile.ZipFile(z) as f:
            f.extract(xlsx.name, out)
    # L'en-tête est à la ligne 6 ; les lignes 1 à 5 sont des titres et des notes.
    return pd.read_excel(xlsx, sheet_name="COP", header=5)


def to_long(cop: pd.DataFrame) -> pd.DataFrame:
    cop = cop[cop["LIB_SAA"].isin(CULTURES)].copy()
    rows = []
    for _, r in cop.iterrows():
        dep = str(r["LIB_DEP"]).split(" - ")[0].lstrip("0").zfill(2)
        for y in YEARS:
            rows.append({
                "dep": dep,
                "dep_nom": str(r["LIB_DEP"]).split(" - ", 1)[-1],
                "region": str(r["LIB_REG2"]),
                "culture": CULTURES[r["LIB_SAA"]],
                "annee": y,
                "statut": str(r["STATUT_QUALITE"]),
                "surface_ha": pd.to_numeric(r[f"SURF_{y}"], errors="coerce"),
                "rendement_qha": pd.to_numeric(r[f"REND_{y}"], errors="coerce"),
                "production_q": pd.to_numeric(r[f"PROD_{y}"], errors="coerce"),
            })
    return pd.DataFrame(rows)


def flag_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """Repère les départements dont la série de rendement vient d'une même estimation.

    Agreste estime souvent le rendement de la lentille au niveau régional : plusieurs
    départements partagent alors exactement les mêmes valeurs. Deux séries identiques à
    0,01 q/ha près sur au moins 8 années sont regroupées (Aube et Marne : 11 années sur 16).
    Le département le plus cultivé représente le groupe ; les autres sont marqués
    « doublon » et écartés de l'entraînement, pour ne pas compter deux fois la même mesure.
    """
    df["serie_groupe"] = df["dep"]
    for cult in df["culture"].unique():
        sub = df[df.culture == cult]
        wide = sub.pivot(index="dep", columns="annee", values="rendement_qha").round(2)
        area = sub.groupby("dep").surface_ha.mean()
        deps = sorted(wide.index)
        parent = {d: d for d in deps}

        def find(d):
            while parent[d] != d:
                d = parent[d]
            return d

        for i, a in enumerate(deps):
            for b in deps[i + 1:]:
                both = wide.loc[a].notna() & wide.loc[b].notna() & (wide.loc[a] > 0)
                if int((wide.loc[a][both] == wide.loc[b][both]).sum()) >= 8:
                    parent[find(b)] = find(a)
        groups = {}
        for d in deps:
            groups.setdefault(find(d), []).append(d)
        rep = {}
        for members in groups.values():
            head = max(members, key=lambda d: area.get(d, 0))
            rep.update({d: head for d in members})
        mask = df.culture == cult
        df.loc[mask, "serie_groupe"] = df.loc[mask, "dep"].map(rep)
    return df


def main():
    df = to_long(load_cop())
    df["utilisable"] = (
        (df.surface_ha >= SURFACE_MIN_HA)
        & (df.rendement_qha > 0)
        & df.statut.isin(["1", "2"])
    )
    df = flag_duplicates(df)
    df["doublon"] = df["serie_groupe"] != df["dep"]
    DATA.mkdir(exist_ok=True)
    df.to_csv(DATA / "panel_rendements.csv", index=False)

    # Rendements nationaux pondérés par la surface (pour le replay et l'accroche).
    nat = (df.assign(p=df.surface_ha * df.rendement_qha.fillna(0))
             .groupby(["culture", "annee"])[["p", "surface_ha", "production_q"]].sum())
    nat["rendement_qha"] = nat.p / nat.surface_ha
    nat = nat.drop(columns="p").reset_index()
    nat.to_csv(DATA / "rendements_nationaux.csv", index=False)

    u = df[df.utilisable & ~df.doublon]
    for cult in CULTURES.values():
        s = u[u.culture == cult]
        print(f"{cult}: {len(s)} départements × années utilisables, "
              f"{s.dep.nunique()} départements")
    piv = nat.pivot(index="annee", columns="culture", values="rendement_qha")
    cv = (piv.std() / piv.mean()).round(2).to_dict()
    print("Coefficient de variation national :", cv)
    print("Corrélation nationale blé / lentille :",
          round(np.corrcoef(piv.ble, piv.lentille)[0, 1], 2))


if __name__ == "__main__":
    main()
