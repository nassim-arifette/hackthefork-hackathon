#!/usr/bin/env bash
# Met bout à bout les segments (seg_*.mp4, ordre des numéros d'image) et encode la vidéo finale :
# H.264, yuv420p, 30 i/s constants, +faststart, au plus 45 Mo (sinon second encodage en deux passes).
set -euo pipefail
SEGS=${1:?dossier des segments}
OUT=${2:?fichier de sortie}
MAX_MO=${MAX_MO:-45}
mkdir -p "$(dirname "$OUT")"
LISTE="$SEGS/liste.txt"
ls "$SEGS"/seg_*.mp4 | sort | sed "s#^#file '#; s#\$#'#" > "$LISTE"
FPS=$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['fps'])" "$(dirname "$0")/timing.json")
COMMUN=(-pix_fmt yuv420p -r "$FPS" -fps_mode cfr -profile:v high -g $((FPS * 2)) -movflags +faststart -an)

ffmpeg -y -loglevel error -f concat -safe 0 -i "$LISTE" -c:v libx264 -preset slow -crf 18 -tune stillimage "${COMMUN[@]}" "$OUT"
TAILLE=$(stat -c %s "$OUT")
if [ "$TAILLE" -gt $((MAX_MO * 1000 * 1000)) ]; then
  DUREE=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT")
  KBPS=$(python3 -c "print(int($MAX_MO * 8000 * 0.96 / $DUREE))")
  echo "$((TAILLE / 1000000)) Mo : second encodage en deux passes à ${KBPS} kb/s"
  P=$(mktemp -d)
  ffmpeg -y -loglevel error -f concat -safe 0 -i "$LISTE" -c:v libx264 -preset slow -b:v "${KBPS}k" -pass 1 -passlogfile "$P/x" "${COMMUN[@]}" -f mp4 /dev/null
  ffmpeg -y -loglevel error -f concat -safe 0 -i "$LISTE" -c:v libx264 -preset slow -b:v "${KBPS}k" -pass 2 -passlogfile "$P/x" "${COMMUN[@]}" "$OUT"
  rm -rf "$P"
fi
echo "$OUT : $(($(stat -c %s "$OUT") / 1000)) ko"
