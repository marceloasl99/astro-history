"""
Resolução centralizada do caminho das efemérides Swiss Ephemeris.

Ordem de busca (todas as pastas existentes são concatenadas com ':' — o Swiss
Ephemeris aceita uma lista de diretórios no estilo PATH):
  1. variável de ambiente SE_EPHE_PATH;
  2. data/ephemeris/swisseph (arquivos sepl_*/seplm*/semom* instalados por
     scripts/install_ephemeris.py — planetas e Lua com precisão suíça completa);
  3. /usr/share/libswe/ephe, /usr/share/swisseph, /usr/local/share/swisseph
     (pacotes do sistema: asteroides seas_*, Lua semo_*, estrelas fixas).

Sem arquivos sepl_* o pyswisseph recorre ao modelo de Moshier (≈0,1" nos
planetas, ≈3" na Lua) — `ephemeris_status()` detecta esse fallback.
"""

import os
from typing import Dict, Any, List, Optional

import swisseph as swe

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
LOCAL_EPHE_DIR = os.path.join(ROOT_DIR, "data", "ephemeris", "swisseph")
SYSTEM_EPHE_DIRS = ["/usr/share/libswe/ephe", "/usr/share/swisseph", "/usr/local/share/swisseph"]

# Arquivos de planetas que caracterizam a instalação "completa" (0–5400 d.C. e 5400 a.C.–0).
PLANET_FILES_CE = [f"sepl_{i:02d}.se1" for i in range(0, 54, 6)]
PLANET_FILES_BCE = [f"seplm{i:02d}.se1" for i in range(6, 60, 6)]
MOON_FILES_BCE = [f"semom{i:02d}.se1" for i in range(6, 60, 6)]

_ACTIVE_PATH: Optional[str] = None


def candidate_dirs() -> List[str]:
    dirs: List[str] = []
    env = os.environ.get("SE_EPHE_PATH")
    if env:
        dirs.extend(p for p in env.split(":") if p)
    dirs.append(LOCAL_EPHE_DIR)
    dirs.extend(SYSTEM_EPHE_DIRS)
    seen, out = set(), []
    for d in dirs:
        if d and d not in seen and os.path.isdir(d):
            seen.add(d)
            out.append(d)
    return out


def ensure_ephe_path(force: bool = False) -> Optional[str]:
    """Configura `swe.set_ephe_path` uma única vez com todas as pastas disponíveis."""
    global _ACTIVE_PATH
    if _ACTIVE_PATH is not None and not force:
        return _ACTIVE_PATH
    dirs = candidate_dirs()
    if not dirs:
        _ACTIVE_PATH = ""
        return None
    _ACTIVE_PATH = ":".join(dirs)
    swe.set_ephe_path(_ACTIVE_PATH)
    return _ACTIVE_PATH


def has_full_planet_files() -> bool:
    """True se os arquivos sepl_* (planetas 0–5400 d.C.) estão em alguma pasta ativa."""
    for d in candidate_dirs():
        if all(os.path.exists(os.path.join(d, f)) for f in PLANET_FILES_CE):
            return True
    return False


def uses_moshier(tjd_ut: float = 2451545.0, body: int = swe.MARS) -> bool:
    """Calcula um corpo e verifica se o retorno veio do fallback Moshier."""
    ensure_ephe_path()
    try:
        _, retflag = swe.calc_ut(tjd_ut, body, swe.FLG_SWIEPH)
    except Exception:
        return True
    return bool(retflag & swe.FLG_MOSEPH)


def ephemeris_status() -> Dict[str, Any]:
    """Resumo para diagnóstico/UI: pastas, cobertura e se o cálculo é Swiss Ephemeris pleno."""
    ensure_ephe_path()
    dirs = candidate_dirs()
    present = set()
    for d in dirs:
        try:
            present.update(os.listdir(d))
        except OSError:
            continue
    ce = [f for f in PLANET_FILES_CE if f in present]
    bce = [f for f in PLANET_FILES_BCE if f in present]
    moon_bce = [f for f in MOON_FILES_BCE if f in present]
    return {
        "active_path": _ACTIVE_PATH,
        "dirs": dirs,
        "swisseph_version": swe.version,
        "planet_files_ce": len(ce),
        "planet_files_bce": len(bce),
        "moon_files_bce": len(moon_bce),
        "full_planets": has_full_planet_files(),
        "moshier_fallback_j2000": uses_moshier(),
        "moshier_fallback_500bce": uses_moshier(1538000.0),
    }


# Configura ao importar, preservando o comportamento dos módulos antigos.
ensure_ephe_path()
