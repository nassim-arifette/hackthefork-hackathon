"""Découpage de la vidéo en segments, coupés aux changements d'écran (utilisé par modal_app.py et faire_video.sh)."""
import json
import pathlib
import sys


def plan(timing: dict, taille: int = 600) -> list[tuple[int, int]]:
    """Segments [de, a) d'au plus `taille` images ; aucun ne chevauche un appui sur Espace."""
    sec = lambda s: int(s.split(":")[0]) * 60 + int(s.split(":")[1])
    fps = timing["fps"]
    bornes = [0] + [round(sec(s) * fps) for s in timing["espace"]] + [round(sec(timing["duree"]) * fps)]
    segs = []
    for d, f in zip(bornes, bornes[1:]):
        n = -(-(f - d) // taille)
        pas = -(-(f - d) // n)
        segs += [(x, min(f, x + pas)) for x in range(d, f, pas)]
    return segs


if __name__ == "__main__":
    cfg = json.loads(pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else pathlib.Path(__file__).parent / "timing.json").read_text())
    for de, a in plan(cfg):
        print(de, a)
