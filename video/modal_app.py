"""Enregistrement parallèle de la vidéo de démo sur Modal.

    modal run video/modal_app.py::main --html app/dist-single/index.html --sortie <dossier>
    modal run video/modal_app.py::sonde_gpu --html app/dist-single/index.html    (voie A, voir README)

Chaque conteneur (CPU, rendu logiciel SwiftShader) enregistre un segment d'environ 20 s en
temps virtuel avec video/enregistrer.cjs ; les segments reviennent en local, où
video/assembler.sh les met bout à bout. Les identifiants Modal sont lus dans
MODAL_TOKEN_ID / MODAL_TOKEN_SECRET et ne sont jamais écrits dans le dépôt.
"""
import json
import pathlib
import subprocess

import modal

ICI = pathlib.Path(__file__).parent
PLAYWRIGHT = "1.63.0"

image = (
    modal.Image.from_registry("node:22-bookworm-slim", add_python="3.12")
    .apt_install("ffmpeg")
    .run_commands(
        "mkdir -p /w && cd /w && npm init -y >/dev/null"
        f" && npm i playwright@{PLAYWRIGHT} && npx playwright install --with-deps chromium"
    )
    .env({"NODE_PATH": "/w/node_modules"})
    .add_local_file(ICI / "enregistrer.cjs", "/video/enregistrer.cjs")
    .add_local_file(ICI / "horloge.js", "/video/horloge.js")
    .add_local_file(ICI / "sonde_gpu.cjs", "/video/sonde_gpu.cjs")
)

app = modal.App("contrat-qui-tient-video", image=image)


def _segment(html: bytes, timing: str, de: int, a: int, gpu: bool = False) -> tuple[bytes, str]:
    pathlib.Path("/tmp/index.html").write_bytes(html)
    pathlib.Path("/tmp/timing.json").write_text(timing)
    out = f"/tmp/seg_{de:05d}.mp4"
    subprocess.run(
        ["node", "/video/enregistrer.cjs", "--html", "/tmp/index.html", "--config", "/tmp/timing.json",
         "--sortie", out, "--de", str(de), "--a", str(a), "--gpu", "1" if gpu else "0"],
        check=True,
    )
    return pathlib.Path(out).read_bytes(), pathlib.Path(out + ".erreurs.txt").read_text()


@app.function(cpu=4.0, memory=4096, timeout=40 * 60, retries=1)
def segment_cpu(html: bytes, timing: str, de: int, a: int) -> tuple[bytes, str]:
    return _segment(html, timing, de, a, gpu=False)


@app.function(gpu="L4", cpu=4.0, memory=8192, timeout=10 * 60)
def gpu(html: bytes) -> str:
    pathlib.Path("/tmp/index.html").write_bytes(html)
    r = subprocess.run(["node", "/video/sonde_gpu.cjs", "/tmp/index.html"], capture_output=True, text=True, timeout=240)
    smi = subprocess.run(["nvidia-smi", "-L"], capture_output=True, text=True, timeout=240)
    return smi.stdout + r.stdout + r.stderr


@app.local_entrypoint()
def main(html: str, sortie: str, config: str = str(ICI / "timing.json"), taille: int = 600):
    timing_txt = pathlib.Path(config).read_text()
    data = pathlib.Path(html).read_bytes()
    import sys
    sys.path.insert(0, str(ICI))
    from decoupe import plan

    segs = plan(json.loads(timing_txt), taille)
    dossier = pathlib.Path(sortie)
    dossier.mkdir(parents=True, exist_ok=True)
    print(f"{len(segs)} segments : {segs}")
    erreurs = []
    for (de, a), (mp4, err) in zip(segs, segment_cpu.starmap([(data, timing_txt, de, a) for de, a in segs])):
        (dossier / f"seg_{de:05d}.mp4").write_bytes(mp4)
        if err.strip():
            erreurs.append(f"segment {de}-{a} :\n{err}")
    (dossier / "erreurs_console.txt").write_text("\n".join(erreurs))
    print("erreurs console :", "aucune" if not erreurs else "\n".join(erreurs))


@app.local_entrypoint()
def sonde_gpu(html: str):
    print(gpu.remote(pathlib.Path(html).read_bytes()))


@app.local_entrypoint()
def essai(html: str, sortie: str, de: int = 2550, a: int = 2850):
    """Un seul segment, pour mesurer le coût par image (par défaut l'écran 4, camions)."""
    timing_txt = (ICI / "timing.json").read_text()
    mp4, err = segment_cpu.remote(pathlib.Path(html).read_bytes(), timing_txt, de, a)
    pathlib.Path(sortie).write_bytes(mp4)
    print("erreurs console :", err or "aucune")


@app.function(gpu="L4", cpu=2.0, timeout=6 * 60)
def libs_nvidia(html: bytes) -> str:
    """Bibliothèques NVIDIA visibles dans le conteneur ; déclare l'ICD Vulkan si libGLX_nvidia est là."""
    import glob, os
    out = []
    libs = sorted({os.path.basename(p) for d in ["/usr/lib/x86_64-linux-gnu", "/usr/lib64", "/usr/local/nvidia/lib64", "/usr/lib"]
                   for p in glob.glob(d + "/lib*nvidia*")})
    out.append("libs : " + " ".join(libs))
    out.append("icd : " + " ".join(glob.glob("/usr/share/vulkan/icd.d/*") + glob.glob("/etc/vulkan/icd.d/*")))
    glx = [p for d in ["/usr/lib/x86_64-linux-gnu", "/usr/lib64", "/usr/local/nvidia/lib64"] for p in glob.glob(d + "/libGLX_nvidia.so*")]
    egl = [p for d in ["/usr/lib/x86_64-linux-gnu", "/usr/lib64", "/usr/local/nvidia/lib64"] for p in glob.glob(d + "/libEGL_nvidia.so*")]
    icds = glob.glob("/usr/share/vulkan/icd.d/*nvidia*") + glob.glob("/etc/vulkan/icd.d/*nvidia*")
    for f in icds:
        out.append(f"{f} : {pathlib.Path(f).read_text()[:300]}")
    env = dict(os.environ)
    if icds:
        env["VK_ICD_FILENAMES"] = icds[0]
    elif glx:
        pathlib.Path("/tmp/nvidia_icd.json").write_text(json.dumps(
            {"file_format_version": "1.0.0", "ICD": {"library_path": glx[0], "api_version": "1.3.0"}}))
        env["VK_ICD_FILENAMES"] = "/tmp/nvidia_icd.json"
    out.append("VK_ICD_FILENAMES=" + env.get("VK_ICD_FILENAMES", ""))
    pathlib.Path("/tmp/index.html").write_bytes(html)
    r = subprocess.run(["node", "/video/sonde_gpu.cjs", "/tmp/index.html"], capture_output=True, text=True, env=env, timeout=240)
    return "\n".join(out) + "\n" + r.stdout + r.stderr[-2000:]


@app.local_entrypoint()
def sonde_libs(html: str):
    print(libs_nvidia.remote(pathlib.Path(html).read_bytes()))
