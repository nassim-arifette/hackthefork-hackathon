# AWS : la marche à suivre

Compte de l'équipe : région **us-east-1** (Virginie du Nord) uniquement, supprimé 72 h après le début de l'événement. Ne jamais copier de clé ou de code d'accès dans le dépôt.

## 1. Entrer dans le compte

1. Ouvrir le lien **Join event URL** reçu par mail.
2. Se connecter (code par e-mail ou identifiant AWS, selon ce que propose la page).
3. Saisir le **Team code** quand il est demandé, puis accepter les conditions.
4. Sur la page de l'événement, cliquer sur **Open AWS console**. Vérifier en haut à droite que la région est **N. Virginia (us-east-1)**.

## 2. Générer la lettre avec Bedrock

1. Dans la console, ouvrir **CloudShell** (icône `>_` en haut de la page). Les droits AWS y sont déjà configurés.
2. Récupérer le code et lister les modèles Claude disponibles :
   ```bash
   git clone https://github.com/nassim-arifette/hackthefork-hackathon
   cd hackthefork-hackathon/pipeline
   aws bedrock list-inference-profiles --region us-east-1 --query "inferenceProfileSummaries[?contains(inferenceProfileId,'anthropic')].inferenceProfileId" --output text
   ```
   Si la liste est vide : `aws bedrock list-foundation-models --region us-east-1 --by-provider anthropic --query "modelSummaries[].modelId" --output text`.
3. Choisir l'identifiant de Claude Sonnet 5 (ou Haiku 4.5) et lancer :
   ```bash
   pip3 install boto3
   BEDROCK_MODEL_ID=<identifiant copié> python3 06_lettre_llm.py
   cat ../app/src/data/lettre.json
   ```
4. Si l'appel est refusé (accès au modèle) : console **Amazon Bedrock**, menu **Model access** ou **Model catalog**, activer le modèle Anthropic (un court formulaire peut être demandé la première fois), puis relancer.
5. Rapporter le contenu de `lettre.json` dans le dépôt (le coller dans la conversation, ou le télécharger avec **Actions > Download file** de CloudShell). La lettre s'affiche alors dans l'annexe « La proposition de contrat ».

### Régénérer la lettre quand les chiffres changent

Le script ne lit que les chiffres exportés par le pipeline. Après un nouvel export (par exemple la version 4 du 31/10), l'ancienne lettre est retirée et l'annexe « La proposition de contrat » affiche la proposition sans lettre jusqu'à la régénération. Dans CloudShell, où le dépôt est déjà cloné :

```bash
cd ~/hackthefork-hackathon && git pull && cd pipeline && BEDROCK_MODEL_ID=us.anthropic.claude-sonnet-5 python3 06_lettre_llm.py && cat ../app/src/data/lettre.json
```

Le script refuse toute lettre qui contient un nombre absent des chiffres fournis.

## 3. Mettre le site en ligne avec Amplify

Choix retenu : **déploiement depuis GitHub**, pour que chaque push sur `main` redéploie le site sans manipuler d'archive.

1. Console : rechercher **Amplify**, puis **Create new app > GitHub**, choisir le dépôt et la branche `main`.
2. Le fichier `amplify.yml` du dépôt indique le dossier `app`, Node 22 et la sortie `dist` : garder les réglages détectés, puis **Save and deploy**.
3. Copier l'URL `https://….amplifyapp.com` et l'ajouter en favori pour dimanche.

Secours sans GitHub : **Create new app > Deploy without Git**, puis glisser une archive du contenu de `app/dist` (avec `index.html` à la racine).

L'URL disparaît avec le compte : la version hors ligne (`app/dist-single/index.html`) reste la démo de secours sur clé USB.
