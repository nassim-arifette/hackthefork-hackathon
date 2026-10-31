# Résultats de la recherche de modèles et de données

Les **36 configurations sont terminées** : 34 expériences principales et deux variantes de météo pondérée par les parcelles RPG 2015, sur cinq légumineuses et dix années. Les **1 800 blocs culture–année–configuration** produisent 212 112 lignes contractuelles. L'évaluation 2019–2025 porte sur les mêmes **1 384 cas** pour chaque candidat ; les années 2016–2018 servent au démarrage temporel.

Lire les [conclusions par culture et sous-groupe](../../docs/AUDIT_DONNEES_MODELES.md), le [rapport complet des politiques](../advanced_policies/REPORT.md) et la [revue des articles et adaptations](../../docs/RECHERCHE_DONNEES_MODELES.md). Le graphique du contrat à prix fixe est disponible en [PNG](../advanced_policies/figures/prix_fixe_cout_protection.png) et [PDF](../advanced_policies/figures/prix_fixe_cout_protection.pdf).

## Restaurer les données complètes après clonage

Depuis la racine du dépôt, avec Python et sa bibliothèque standard :

```bash
python scripts/restore_advanced_artifacts.py
python scripts/restore_advanced_artifacts.py --verify-only
```

Les quatre plus gros fichiers gzip sont versionnés en morceaux binaires d'au plus **8 Mio**, pour respecter la limite de requête de 16 Mio rencontrée lors de leur publication par l'API Git. Le script les reconstitue sans perte et vérifie **la taille et le SHA-256 de chaque morceau puis du fichier complet**, d'après [git_artifacts.json](git_artifacts.json). Il conserve un fichier déjà conforme ; `--verify-only` vérifie les fichiers reconstitués sans les recréer.

| Fichier reconstitué | Contenu |
|---|---|
| `experiments/advanced_combined/predictions.csv.gz` | Sorties contractuelles brutes des 36 configurations, avant les corrections et choix temporels des politiques. |
| `experiments/advanced_policies/policy_decisions.csv.gz` | Décisions et résultats cas par cas après calibration et sélection temporelle. |
| `experiments/advanced_policies/subgroup_comparisons.csv.gz` | Comparaisons appariées par sous-groupe. |
| `experiments/advanced_policies/summary.csv.gz` | Métriques détaillées, périodes et groupes. |

Le [tableau global](../advanced_policies/global_summary.csv), les [comparaisons avec les références](../advanced_policies/paired_baselines.csv), les [candidats rétrospectifs](../advanced_policies/retrospective_candidates.csv) et les [choix temporels](../advanced_policies/selection_decisions.csv) sont directement lisibles sans restauration. Les fichiers gzip reconstitués se lisent par exemple avec `pandas.read_csv("experiments/advanced_combined/predictions.csv.gz")` ; pandas détecte la compression.

Pour régénérer le graphique après installation des dépendances du projet :

```bash
python scripts/plot_advanced_results.py
```

## Résultats canoniques et contrôles

La série publiée provient du **recalcul intégral depuis zéro sur Colab L4**, avec 12 CPU logiques et le même profil NumPy effectif pour les expériences principales et RPG. Le profil désactive les chemins AVX512 identifiés dans le [diagnostic QRF](qrf_cpu_diagnostic.json). Les anciens calculs mêlant plusieurs profils matériels sont archivés séparément et n'alimentent pas ces résultats. Les [sources et archives des calculs](archive_index.json), la [composition des 36 configurations](../advanced_combined/COMPOSITION.md) et les [empreintes de l'analyse finale](analysis_execution.json) permettent de retrouver les versions exécutées.

La **vraie baseline M0** et le QRF saisonnier reproduisent les références déjà présentes dans `experiments/multilegumes_benchmark/predictions.csv.gz`, intégrant les prix de la PR #3 : **5 892 lignes comparées par référence, aucun verdict modifié**, écart maximal de **1,36 × 10⁻¹²** sur les colonnes numériques. Le contrôle utilise une tolérance absolue de `1e-9` ; les clés, catégories et verdicts doivent être identiques. Il ne revendique pas l'identité binaire de CSV dont l'ordre et les colonnes peuvent différer.

Le [rapport de vérification indépendante](verification_results.md) et son [JSON](verification_results.json) contrôlent également les formules économiques, cohortes, coupures temporelles, 614 496 décisions finales et scores utilisés pour la sélection. Les **198 tests Colab passent** ([journal](validation_final.txt)). Les **six tests ciblés du notebook** ont aussi été rejoués localement, ainsi que la compilation de ses quatre cellules de code ; ces périmètres se recoupent et leurs nombres ne sont pas additionnés.

Les archives complètes, checkpoints et code exécuté sont dans le [dossier Drive des expériences](https://drive.google.com/drive/folders/1_po5W-5yhaKCB8d0-NAaNU0ZfdnIqnvf). L'[index des archives finales](final_artifact_index.json) fournit les liens et empreintes des deux ZIP à extraire dans un même répertoire. Le [notebook](../../notebooks/advanced_colab.ipynb) conserve la progression, la sauvegarde Drive et la reprise avec vérification du profil numérique.
