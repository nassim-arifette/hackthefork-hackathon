#!/usr/bin/env python3
"""Vérifie la vidéo finale et produit la planche contact.

    python3 video/verifier.py docs/video/demo-4min.mp4 docs/video/planche.jpg

- format : codec, pixels, cadence, durée, taille, faststart ;
- fluidité : différence image à image sur une copie réduite ; pendant les vols de caméra et les
  camions, plus longue suite d'images identiques ;
- planche contact : une image toutes les 5 s, avec son horodatage.
"""
import json
import pathlib
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ICI = pathlib.Path(__file__).parent
video, planche = sys.argv[1], sys.argv[2]
cfg = json.loads((ICI / "timing.json").read_text())
sec = lambda s: int(s.split(":")[0]) * 60 + int(s.split(":")[1])
fps = cfg["fps"]
press = [sec(s) for s in cfg["espace"]]
debuts = [0] + press

probe = json.loads(subprocess.run(
    ["ffprobe", "-v", "error", "-show_entries", "stream=codec_name,profile,pix_fmt,width,height,r_frame_rate,avg_frame_rate,nb_frames"
     ":format=duration,size", "-of", "json", video], capture_output=True, text=True, check=True).stdout)
st, fm = probe["streams"][0], probe["format"]
tete = pathlib.Path(video).read_bytes()[:4096]
faststart = tete.find(b"moov") != -1 and (tete.find(b"mdat") == -1 or tete.find(b"moov") < tete.find(b"mdat"))
print(f"format : {st['codec_name']} {st['profile']} {st['pix_fmt']} {st['width']}x{st['height']}, "
      f"{st['r_frame_rate']} (moyenne {st['avg_frame_rate']}), {st['nb_frames']} images, "
      f"{float(fm['duration']):.3f} s, {int(fm['size']) / 1e6:.1f} Mo, faststart {'oui' if faststart else 'non'}")

# Copie réduite en niveaux de gris, 480x270 : nombre de pixels qui changent d'une image à la suivante.
W, H = 480, 270
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", video, "-vf", f"scale={W}:{H},format=gray", "-f", "rawvideo", "-"],
                     capture_output=True, check=True).stdout
fr = np.frombuffer(raw, np.uint8).reshape(-1, H, W).astype(np.int16)
change = (np.abs(np.diff(fr, axis=0)) > 6).sum(axis=(1, 2))  # change[i] : entre l'image i et i+1
bouge = change >= 5

# Fenêtres où la carte doit bouger à chaque image : vols de caméra (1,8 s) et camions.
# À l'écran 5, la première année se colore 350 ms après l'entrée, pendant le vol.
e2, e3, e4, e5, e6 = press  # entrée dans les écrans 2 à 6
autres = sorted(sec(k["a"]) for k in cfg.get("touches", []))
fin_camions = autres[0] if autres else float(fm["duration"]) - 0.5
fenetres = [
    ("écran 2, vol de caméra", e2, e2 + 1.8),
    ("écran 3, descente vers le silo", e3, e3 + 1.8),
    ("écran 4, vol de caméra", e4, e4 + 1.8),
    ("écran 4, camions", e4 + 6, e4 + 16),
    ("écran 5, vol de caméra (carte colorée)", e5 + 0.4, e5 + 1.8),
    ("écran 6, vol de caméra", e6, e6 + 1.8),
    ("écran 6, camions", e6 + 2, fin_camions - 0.1),
] + [(f"touche {k['touche']} à {k['a']}, vol de caméra", sec(k["a"]), sec(k["a"]) + 1.8) for k in cfg.get("touches", [])]
def plus_longue(a, b):
    i0, i1 = int(a * fps), min(len(bouge), int(b * fps))
    run = best = 0
    for v in bouge[i0:i1]:
        run = 0 if v else run + 1
        best = max(best, run)
    return (best + 1) * 1000 / fps, bouge[i0:i1].mean() * 100

print("fluidité (une image tenue N ms = N/33 images identiques de suite) :")
pire = 0
for nom, a, b in fenetres:
    ms, part = plus_longue(a, b)
    pire = max(pire, ms)
    print(f"  {nom} : {part:.0f} % des images changent, image la plus longtemps tenue {ms:.0f} ms")
print(f"pire image tenue pendant les vols et les camions : {pire:.0f} ms (critère : 100 ms au plus)")
ms, part = plus_longue(0.5, e2 - 0.5)
print(f"  pour information, écran 1 (cargos) : {part:.0f} % des images changent, {ms:.0f} ms au plus ; "
      "les cargos ralentissent en arrivant au port puis marquent une pause de 1,8 s (animation de l'application)")

# Planche contact : une image toutes les 5 s.
cols, w, h = 6, 480, 270
temps = list(range(0, int(float(fm["duration"])), 5))
rows = -(-len(temps) // cols)
sheet = Image.new("RGB", (cols * w, rows * (h + 26)), "white")
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
draw = ImageDraw.Draw(sheet)
for k, t in enumerate(temps):
    img = Image.fromarray(np.frombuffer(subprocess.run(
        ["ffmpeg", "-v", "error", "-ss", str(t), "-i", video, "-frames:v", "1", "-vf", f"scale={w}:{h}", "-f", "rawvideo",
         "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout, np.uint8).reshape(h, w, 3))
    x, y = (k % cols) * w, (k // cols) * (h + 26)
    ecran = sum(1 for d in debuts if d <= t)
    tch = "".join(f" +{k['touche'].upper()}" for k in cfg.get("touches", []) if sec(k["a"]) <= t and ecran == sum(1 for d in debuts if d <= sec(k["a"])))
    draw.text((x + 6, y + 3), f"{t // 60}:{t % 60:02d}  écran {ecran}{tch}", fill="black", font=font)
    sheet.paste(img, (x, y + 26))
sheet.save(planche, quality=85)
print(f"planche : {planche} ({len(temps)} vignettes)")
