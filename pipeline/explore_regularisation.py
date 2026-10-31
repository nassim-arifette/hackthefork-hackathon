"""Ancienne exploration retirée : elle réutilisait la calibration puis réentraînait.

Le protocole canonique compare désormais M0, M1, M2, M3 et la sélection temporelle
sans réentraînement après calibration. Les anciens scores de ce script ne sont
pas des résultats du protocole actuel. Voir docs/RECHERCHE.md.
"""


def main():
    print("Exploration historique retirée : ses résultats ne sont plus valides.")
    print("Utiliser le protocole corrigé : python pipeline/03_backtest.py")
    print("Les candidats et paramètres sont figés avant de lire ses résultats.")


if __name__ == "__main__":
    main()
