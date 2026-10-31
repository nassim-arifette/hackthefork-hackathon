> Document de contexte antérieur à la correction de validation. Les chiffres et engagements ci-dessous ne décrivent pas le scénario courant. Références à jour : [RESULTATS](RESULTATS.md), [MODELE](MODELE.md) et [DEMO_SCRIPT](DEMO_SCRIPT.md).

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
   pip3 install --user boto3
   BEDROCK_MODEL_ID=<identifiant copié> python3 06_lettre_llm.py
   cat ../app/src/data/lettre.json
   ```
4. Si l'appel est refusé (accès au modèle) : console **Amazon Bedrock**, menu **Model access** ou **Model catalog**, activer le modèle Anthropic (un court formulaire peut être demandé la première fois), puis relancer.
5. Rapporter le contenu de `lettre.json` dans le dépôt (le coller dans la conversation, ou le télécharger avec **Actions > Download file** de CloudShell). La lettre s'affiche alors à l'étape 5.

## 3. Mettre le site en ligne avec Amplify

Le plus rapide, sans connecter GitHub :

1. Console : rechercher **Amplify**, puis **Create new app** et **Deploy without Git**.
2. Nommer l'application, glisser l'archive du site (`site-amplify.zip` : le contenu de `app/dist`, avec `index.html` à la racine), puis **Save and deploy**.
3. Copier l'URL `https://….amplifyapp.com` et l'ajouter en favori pour dimanche.

Variante avec GitHub (redéploiement à chaque push) : **Create new app > GitHub**, choisir le dépôt et la branche `main` ; le fichier `amplify.yml` du dépôt indique le dossier `app` et la sortie `dist`.

L'URL disparaît avec le compte : la version hors ligne (`app/dist-single/index.html`) reste la démo de secours sur clé USB.
