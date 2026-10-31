# Composition de l'expérience météo RPG

Le benchmark principal est conservé intégralement. Deux expériences supplémentaires utilisent le même code et les mêmes réglages avec des variables SIM pondérées par les parcelles RPG2015 ; le repli CLC est documenté dans la provenance source.

Les alias techniques `qrf_agri_sparse` et `qrf_agri_dense` du second calcul sont renommés `qrf_rpg_weather_sparse` et `qrf_rpg_weather_dense`. Aucun prix, rendement simulé, paiement ou verdict n'est recalculé par l'assemblage. Les spécifications exécutées et archives restent séparées dans `manifest.json`, avec contrôle de chaque entrée archivée, des cohortes, de l'économie observée et de l'identité des valeurs après export.
