"""Convertit app/dist-single/index.html en page publiable (sans doctype ni balises html/head/body)."""
import re
import sys
from pathlib import Path

src, dst = Path(sys.argv[1]), Path(sys.argv[2])
html = src.read_text(encoding="utf-8")
title = re.search(r"<title>.*?</title>", html, re.S).group(0)
links = "\n".join(re.findall(r"<link [^>]*>", html))
styles = "\n".join(re.findall(r"<style[^>]*>.*?</style>", html, re.S))
scripts = "\n".join(re.findall(r"<script[^>]*>.*?</script>", html, re.S))
dst.write_text(f'{title}\n{links}\n{styles}\n<div id="root"></div>\n{scripts}\n', encoding="utf-8")
print(dst, f"{dst.stat().st_size / 1e6:.1f} Mo")
