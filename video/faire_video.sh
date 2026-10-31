#!/usr/bin/env bash
# Réenregistre la vidéo de secours en une commande, depuis l'état courant ou un commit donné.
#   bash video/faire_video.sh            # depuis l'arbre de travail
#   bash video/faire_video.sh <commit>   # depuis un commit (copie temporaire via git worktree)
#   LOCAL=1 bash video/faire_video.sh    # sans Modal : segments en local, PARALLELE à la fois (défaut 2)
# Sortie : docs/video/demo-4min.mp4 et docs/video/planche.jpg, puis le rapport de vérification.
set -euo pipefail
RACINE=$(cd "$(dirname "$0")/.." && pwd)
VIDEO="$RACINE/video"
TRAVAIL=$(mktemp -d)
trap 'rm -rf "$TRAVAIL"; [ -n "${ARBRE:-}" ] && git -C "$RACINE" worktree remove --force "$ARBRE" >/dev/null 2>&1 || true' EXIT

APP="$RACINE/app"
if [ -n "${1:-}" ]; then
  ARBRE="$TRAVAIL/arbre"
  git -C "$RACINE" worktree add --detach "$ARBRE" "$1" >/dev/null
  APP="$ARBRE/app"
fi
echo "== construction de l'application ($( [ -n "${1:-}" ] && echo "commit $1" || echo "arbre de travail"))"
(cd "$APP" && npm ci --no-audit --no-fund >/dev/null && npm run build:single >/dev/null)
HTML="$APP/dist-single/index.html"

SEGS="$TRAVAIL/segs"
mkdir -p "$SEGS"
if [ "${LOCAL:-0}" = 1 ]; then
  echo "== enregistrement local, ${PARALLELE:-2} segments à la fois"
  python3 "$VIDEO/decoupe.py" | xargs -P "${PARALLELE:-2}" -L 1 sh -c \
    'node "$0/enregistrer.cjs" --html "$1" --sortie "$2/seg_$(printf %05d "$3").mp4" --de "$3" --a "$4"' "$VIDEO" "$HTML" "$SEGS"
  cat "$SEGS"/*.erreurs.txt > "$SEGS/erreurs_console.txt" || true
else
  echo "== enregistrement sur Modal (CPU, un conteneur par segment)"
  # Les jetons Modal commencent par ak- (identifiant) et as- (secret).
  case "${MODAL_TOKEN_SECRET:-}" in as-*|"") ;; *) export MODAL_TOKEN_SECRET="as-$MODAL_TOKEN_SECRET" ;; esac
  (cd "$RACINE" && modal run video/modal_app.py::main --html "$HTML" --sortie "$SEGS")
fi
if [ -s "$SEGS/erreurs_console.txt" ]; then echo "!! messages console :"; cat "$SEGS/erreurs_console.txt"; fi

echo "== assemblage"
bash "$VIDEO/assembler.sh" "$SEGS" "$RACINE/docs/video/demo-4min.mp4"
echo "== vérification"
python3 "$VIDEO/verifier.py" "$RACINE/docs/video/demo-4min.mp4" "$RACINE/docs/video/planche.jpg"
