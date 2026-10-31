# Vidéo de secours de la démo

`docs/video/demo-4min.mp4` rejoue les six écrans de la démo au minutage de [docs/DEMO_SCRIPT.md](../docs/DEMO_SCRIPT.md). Si la démo en direct plante, l'orateur lance la vidéo en plein écran et parle par-dessus. Elle est muette.

## Relancer

```sh
make video                  # depuis l'arbre de travail
make video COMMIT=<sha>     # depuis un commit donné (copie temporaire via git worktree)
LOCAL=1 make video          # sans Modal, en local (~1 h avec 2 segments en parallèle sur 4 cœurs)
```

La commande construit `app/dist-single/index.html`, enregistre les segments sur Modal, assemble `docs/video/demo-4min.mp4`, écrit `docs/video/planche.jpg` et affiche le rapport de vérification. Compter une quinzaine de minutes avec Modal. Il faut `MODAL_TOKEN_ID` et `MODAL_TOKEN_SECRET` dans l'environnement, et `pip install 'modal[api-proxy-support]'` derrière un proxy.

Pour changer le minutage, modifier `video/timing.json` : `espace` liste les instants où l'on appuie sur Espace, `touches` les autres touches (par exemple `{ "a": "3:42", "touche": "f" }` pour la carte de France des prix à l'écran 6), `duree` la durée totale.

## Méthode : temps virtuel, image par image

La page ne tourne pas en temps réel. `horloge.js` est injecté avant l'application et remplace `performance.now`, `Date`, `setTimeout`/`setInterval` et `requestAnimationFrame` par une horloge qui n'avance que sur ordre. Pour chaque image, `enregistrer.cjs` :

1. avance l'horloge de 1/30 s et exécute dans l'ordre les minuteries échues (montée du prix, années de la preuve) ;
2. laisse React appliquer ses mises à jour, puis exécute les rappels `requestAnimationFrame` (deck.gl dessine la carte, les camions et les cargos avancent) ;
3. met en pause toutes les animations et transitions CSS (`document.getAnimations()`) et règle leur `currentTime` sur l'horloge virtuelle ;
4. capture la page (CDP `Page.captureScreenshot`) et l'envoie à ffmpeg.

Chaque image correspond donc exactement à 1/30 s de démo, quelle que soit la vitesse du rendu : la vidéo est fluide et reproductible, même en rendu logiciel. Avant le chrono, le script attend `document.fonts.ready` et le premier rendu de la carte, à temps figé.

La vidéo est découpée en 15 segments d'au plus 20 s, coupés à chaque touche (`decoupe.py`). Chaque segment tourne dans son propre conteneur Modal (CPU, 4 cœurs). Il refait le parcours depuis le chargement et frappe chaque touche à son image, en accéléré jusqu'à 1 s avant la dernière touche qui précède le segment, puis image par image. `assembler.sh` les met bout à bout et encode le fichier final (H.264, yuv420p, 30 i/s constants, `+faststart`, au plus 45 Mo).

Cadre : fenêtre 1920×1080 à l'échelle 1, la définition du projecteur.

## Pourquoi pas une capture en temps réel sur GPU (voie A)

Essai sur Modal avec un GPU NVIDIA L4 (`sonde_gpu.cjs`, `modal run video/modal_app.py::sonde_gpu`). Le conteneur ne donne à Chromium aucun pilote graphique NVIDIA utilisable. Avec ANGLE sur Vulkan, le renderer WebGL est `llvmpipe` (Mesa, rendu logiciel) et deck.gl ne crée pas son contexte : les 60 i/s mesurés correspondent alors à une page sans carte. Avec ANGLE sur EGL ou en EGL direct, le rendu est logiciel, à 3,4 et 3,7 i/s à l'écran 4. Un dernier essai a forcé l'ICD Vulkan NVIDIA (`sonde_libs`) : Chromium s'est bloqué. Faute d'accélération matérielle vérifiée, la voie B est retenue. Elle n'a besoin d'aucun GPU.

## Vérifier

`verifier.py` contrôle le format, mesure la plus longue image figée pendant les vols de caméra et les camions à partir des différences image à image, et produit la planche contact (une image toutes les 5 s). Les cargos de l'écran 1 sont rapportés à part : ils ralentissent en arrivant au port puis marquent une pause de 1,8 s, ce qui donne des images identiques voulues. Les messages console de chaque segment sont listés pendant l'enregistrement. Les avertissements « GL Driver Message » viennent du rendu logiciel et sont ignorés.

## Fichiers

| Fichier | Rôle |
|---|---|
| `timing.json` | minutage, cadence, taille de fenêtre |
| `horloge.js` | horloge virtuelle injectée dans la page |
| `enregistrer.cjs` | enregistre un segment `[de, a)` en temps virtuel |
| `decoupe.py` | découpe en segments |
| `modal_app.py` | exécution parallèle sur Modal, et sondes GPU de la voie A |
| `sonde_gpu.cjs` | voie A : renderer WebGL et i/s réelles |
| `assembler.sh` | assemblage et encodage final |
| `verifier.py` | contrôles et planche contact |
| `faire_video.sh` | la commande complète (`make video`) |
