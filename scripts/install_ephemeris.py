#!/usr/bin/env python3
"""
Instala os arquivos completos do Swiss Ephemeris (planetas 5400 a.C.–5400 d.C. e Lua a.C.)
em data/ephemeris/swisseph/, verificando SHA-256 contra data/ephemeris/swisseph_manifest.sha256.

Fonte: https://github.com/aloistr/swisseph (pasta ephe/, licença AGPL-3.0 — compatível com o projeto).
Uso:  python scripts/install_ephemeris.py [--check-only]
"""
import hashlib
import os
import sys
import urllib.request

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEST = os.path.join(ROOT, "data", "ephemeris", "swisseph")
MANIFEST = os.path.join(ROOT, "data", "ephemeris", "swisseph_manifest.sha256")
BASE_URL = "https://raw.githubusercontent.com/aloistr/swisseph/master/ephe/"


def read_manifest():
    entries = []
    with open(MANIFEST, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            digest, name = line.split()
            entries.append((name.lstrip("*"), digest))
    return entries


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    check_only = "--check-only" in sys.argv
    os.makedirs(DEST, exist_ok=True)
    ok, missing, bad = 0, [], []
    for name, digest in read_manifest():
        path = os.path.join(DEST, name)
        if not os.path.exists(path) and not check_only:
            print(f"baixando {name} ...")
            urllib.request.urlretrieve(BASE_URL + name, path)
        if not os.path.exists(path):
            missing.append(name)
            continue
        if sha256(path) != digest:
            bad.append(name)
            continue
        ok += 1
    print(f"{ok} arquivos verificados; {len(missing)} ausentes; {len(bad)} com hash divergente.")
    if missing or bad:
        for n in missing:
            print("  ausente:", n)
        for n in bad:
            print("  hash divergente:", n)
        sys.exit(1)
    sys.path.insert(0, ROOT)
    from src.core.ephemeris import ephemeris_status
    st = ephemeris_status()
    print("Swiss Ephemeris pleno:", st["full_planets"], "| fallback Moshier (J2000):", st["moshier_fallback_j2000"])


if __name__ == "__main__":
    main()
