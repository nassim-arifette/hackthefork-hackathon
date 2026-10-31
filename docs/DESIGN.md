# Design de l'application

Direction : **un atlas agricole imprimé, lu à l'écran**. La carte est le sujet ; le texte l'accompagne comme dans un dossier de presse ou une notice cartographique. Rien ne doit ressembler à un tableau de bord générique.

Références de travail : la sobriété des cartes topographiques (IGN, swisstopo), les graphiques de presse à étiquettes directes (data journalism), la mise en page d'un contrat ou d'une note technique.

## Couleurs

Thème clair unique : il passe mieux au vidéoprojecteur dans une salle éclairée.

| Jeton | Valeur | Usage |
|---|---|---|
| `--page` | `#FFFFFF` | fond du panneau de texte |
| `--land` | `#ECEEE7` | fond de carte |
| `--ink` | `#1D211C` | texte principal, boutons principaux |
| `--ink-2` | `#454B43` | texte courant |
| `--mute` | `#767C72` | légendes, sources |
| `--rule` | `#DCDFD6` | filets de séparation |
| `--wheat` | `#C8962F` | blé (sémantique) |
| `--lentil` | `#2F6A50` | lentille sous contrat (sémantique) |
| `--slate` | `#5B7385` | lentille déjà déclarée |
| `--fail` | `#B5432C` | contrat non tenu, uniquement |
| `--market` | `#DCE3EA` | bande de la référence historique 2012–2016 |

Deux couleurs portent le sens (blé, lentille). Le rouge n'apparaît que pour un contrat qui ne tient pas.

## Typographie

| Rôle | Police | Taille / interligne |
|---|---|---|
| Titre d'étape | Archivo, graisse 640, largeur 88 % | 34 / 1,08 |
| Grands chiffres | Archivo, graisse 700, largeur 80 %, chiffres tabulaires | 44 / 1 |
| Texte d'introduction | Source Serif 4, 400 | 17 / 1,55 |
| Texte courant | Source Serif 4, 400 | 15 / 1,55 |
| Interface, étiquettes | Archivo, 500 | 13 |
| Sources, notes | Archivo, 400 | 12, couleur `--mute` |

Échelle : 12, 13, 15, 17, 22, 34, 44, 88.

## Espacement

Base 8 px : 4, 8, 12, 16, 24, 32, 48, 64. Marges du panneau : 32 px. Entre deux blocs : 32 px. Dans un bloc : 8 à 16 px.

On groupe par l'espace et l'alignement, pas avec des boîtes. Un filet fin sépare deux blocs quand l'espace ne suffit pas.

## Graphiques

- Étiquettes directes au bout des courbes, pas de légende séparée quand elle peut être évitée.
- Une seule grille légère, ou aucune ; pas d'axe vertical s'il n'apporte rien.
- Chaque graphique a un titre en une phrase et une ligne de source.
- Les mêmes couleurs sémantiques que la carte.

## Étiquetage des chiffres

Chaque bloc de chiffres se termine par une ligne de source qui commence par son statut, comme un crédit de presse :
« **Mesuré.** Eurostat Comext ; Agreste SAA 2025, provisoire. » ou « **Modèle.** Backtest glissant 2019–2025. »

## Interdits

- Fond sombre avec une couleur fluo, dégradés, lueurs, flou de verre.
- Étiquettes en majuscules et en police à chasse fixe au-dessus des titres.
- Une boîte bordée autour de chaque bloc ; badges colorés sur chaque chiffre.
- Boutons en pilule, ombres portées décoratives, émojis, icônes de décoration.
- Inter, Roboto, Space Grotesk, Syne.
- Texte courant centré.
- Extrusions 3D : la carte reste plane et lisible.
