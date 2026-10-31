# Recalcul après PR #3

Exécution Google Colab CPU : haricot et pois, 120 configurations en 196,1 secondes. Le benchmark final est dans [`../multilegumes_benchmark`](../multilegumes_benchmark).

`executed-inputs.zip` contient exactement les sources et les données exécutées. `manifest.json` conserve les empreintes et versions ; `execution.json` décrit la commande. `predictions.csv.gz` contient toutes les observations et les trois formes contractuelles. `audit.json` décrit les entraînements et hypothèses.

Pour reproduire ce calcul historique, extraire `executed-inputs.zip` dans un dossier distinct puis installer son `requirements-research.txt` et relancer sa commande avec un nouveau dossier de sortie. Ne pas lui substituer silencieusement les hypothèses courantes.

La copie complète avec les points de reprise est sauvegardée dans le dossier Drive HackTheFork / multilegumes-2026-10-31. Les archives volumineuses redondantes ne sont pas nécessaires au recalcul depuis les sources et données versionnées.
