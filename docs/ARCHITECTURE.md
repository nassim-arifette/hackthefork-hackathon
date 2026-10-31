# Architecture de la version corrigée

## Calcul hors navigateur

`01_agreste.py` conserve les observations et indicateurs de qualité. Les anciens drapeaux de regroupement du CSV ne sont pas utilisés pour apprendre ou sélectionner les séries. `02_weather.py` fournit la météo annuelle brute ; `00_prix_commerce.py` reconstruit les références de prix.

`model.py` applique la séparation temporelle, apprend les niveaux et anomalies sur l'apprentissage, entraîne les candidats, sélectionne éventuellement sur deux années réservées, puis calibre sur trois autres années. Le prédicteur est figé. Les quantiles bruts alimentent la simulation ; les bornes corrigées servent à l'évaluation des intervalles.

`03_backtest.py` calcule les décisions avec les seules données antérieures à chaque année test et compare les marges reconstituées après réalisation. Les sorties contiennent audits, observations individuelles, métriques prédictives et économiques, ainsi qu'une grille de niveaux de protection.

`05_export.py` applique la procédure à 2026, exporte prix, sensibilités, géométries, seuils par parcelle, volumes attendus, audit et hypothèses. Les géométries RPG versionnées peuvent être réutilisées, sans téléchargement, lorsque le site et le détour routier sont inchangés. `06_lettre_llm.py` est facultatif ; sans configuration AWS, il efface l'ancien texte. La proposition interactive reste calculée depuis l'état du scénario.

## Interface

React + Vite + deck.gl. Le navigateur lit les exports précalculés et gère l'offre acheteur. Le prix rendu est converti en départ ferme avec la distance de chaque parcelle ; la courbe de démonstration précise son trajet de référence. La sélection des parcelles pour le volume attendu est partagée entre carte, stress et contrat.

Les paramètres acheteur restent hypothétiques : revente par tonne vendable, pertes au tri, coûts et marge minimale par tonne entrante. Le plafond est comparé au prix rendu requis pour le volume cible. Une offre peut être incompatible même si une plage de négociation existe.

## Vérification

`pytest` vérifie les appels effectifs d'apprentissage, les frontières temporelles, l'invariance des décisions après perturbation du futur, les quantiles et les identités économiques. `npm run build` contrôle TypeScript et produit le site ; `npm run build:single` produit une page autonome.

Voir [MODELE](MODELE.md), [RECHERCHE](RECHERCHE.md), [RESULTATS](RESULTATS.md) et [LIMITES](LIMITES.md).
