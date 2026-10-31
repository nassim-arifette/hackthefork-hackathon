#!/usr/bin/env python3
"""Vérifie la vidéo finale et produit la planche contact.

    python3 video/verifier.py docs/video/demo-4min.mp4 docs/video/planche.jpg

- format : codec, pixels, cadence, durée, taille, faststart ;
- fluidité : différence image à image sur une copie réduite ; pendant les fenêtres où quelque
  chose doit bouger (vol de caméra des 2 s après chaque Espace, cargos de l'écran 1, prix et
  camions de l'écran 4, carte rejouée de l'écran 5), plus longue suite d'images identiques ;
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

# Copie réduite en niveaux de gris, 480x270, pour les différences image à image.
W, H = 480, 270
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", video, "-vf", f"scale={W}:{H},format=gray", "-f", "rawvideo", "-"],
                     capture_output=True, check=True).stdout
fr = np.frombuffer(raw, np.uint8).reshape(-1, H, W).astype(np.int16)
diff = np.abs(np.diff(fr, axis=0)).mean(axis=(1, 2))  # diff[i] : entre l'image i et i+1
bouge = diff > 0.02

fenetres = [(f"vol de caméra, Espace à {s // 60}:{s % 60:02d}", s, s + 1.8) for s in press]
fenetres += [
    ("écran 1, cargos", 0.5, press[0] - 0.5),
    ("écran 4, prix puis camions", press[2] + 1.6, press[2] + 12),
    ("écran 5, carte rejouée 2019-2025", press[3] + 1, press[3] + 10),
]
print("fluidité (plus longue suite d'images identiques dans chaque fenêtre) :")
pire = 0
for nom, a, b in fenetres:
    i0, i1 = int(a * fps), min(len(bouge), int(b * fps))
    run = best = 0
    for v in bouge[i0:i1]:
        run = 0 if v else run + 1
        best = max(best, run)
    ms = (best + 1) * 1000 / fps if best else 1000 / fps
    pire = max(pire, ms)
    print(f"  {nom} : {(bouge[i0:i1].mean() * 100):.0f} % des images changent, plus longue image figée {ms:.0f} ms")
print(f"pire image figée dans les fenêtres animées : {pire:.0f} ms (critère : 100 ms au plus)")

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
    draw.text((x + 6, y + 3), f"{t // 60}:{t % 60:02d}  écran {ecran}", fill="black", font=font)
    sheet.paste(img, (x, y + 26))
sheet.save(planche, quality=85)
print(f"planche : {planche} ({len(temps)} vignettes)")
