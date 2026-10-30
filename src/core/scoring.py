"""
Função ÚNICA de score de tensão, lida de config/score.yaml.

Antes da v3 existiam duas fórmulas divergentes (grade diária com 9 corpos e carta de
evento com 17 corpos), o que inflava o percentil exibido na interface. Agora a grade
e a carta chamam `raw_tension_from_longitudes`, e um teste de paridade garante que
a mesma data produz o mesmo score pelos dois caminhos.
"""

import os
from functools import lru_cache
from typing import Dict, Any, Iterable, Tuple, List

import numpy as np
import yaml

CONFIG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "config"))
SCORE_CONFIG_FILE = os.path.join(CONFIG_DIR, "score.yaml")

ASPECT_KEY_TO_NAME = {
    "conjunction": "Conjunção",
    "square": "Quadratura",
    "trine": "Trígono",
    "opposition": "Oposição",
}


@lru_cache(maxsize=1)
def load_score_config() -> Dict[str, Any]:
    with open(SCORE_CONFIG_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def aspect_definitions(max_orb: float = None) -> List[Dict[str, Any]]:
    """
    Lista de aspectos no formato usado pelo motor (nome PT, ângulo, orbe, natureza, tensão).
    `max_orb` sobrescreve a orbe de todos os aspectos (usado na análise de sensibilidade H3).
    """
    cfg = load_score_config()
    symbols = {"conjunction": "☌", "square": "□", "trine": "△", "opposition": "☍"}
    out = []
    for key, a in cfg["aspects"].items():
        out.append({
            "key": key,
            "name": ASPECT_KEY_TO_NAME[key],
            "angle": float(a["angle"]),
            "orb": float(max_orb if max_orb is not None else a["orb"]),
            "symbol": symbols[key],
            "nature": a["nature"],
            "tension": float(a["tension"]),
        })
    return out


def pair_class(b1: str, b2: str) -> str:
    """Classifica o par de corpos na hierarquia arquetípica definida no YAML."""
    cfg = load_score_config()["scoring"]
    outer = set(cfg["outer_bodies"])
    lum = set(cfg["luminaries"])
    pair = {b1, b2}
    classes = {
        "saturn_pluto": pair == {"saturn", "pluto"},
        "uranus_pluto": pair == {"uranus", "pluto"},
        "saturn_uranus": pair == {"saturn", "uranus"},
        "saturn_neptune": pair == {"saturn", "neptune"},
        "outer_outer": b1 in outer and b2 in outer,
        "mars_outer": "mars" in pair and bool(pair & outer),
        "luminary_outer": bool(pair & lum) and bool(pair & outer),
    }
    for name in cfg["pair_class_order"]:
        if classes.get(name, False):
            return name
    return "other"


SPECIFIC_OUTER_CLASSES = {"saturn_pluto", "uranus_pluto", "saturn_uranus", "saturn_neptune"}


def _weight(table: Dict[str, float], cls: str) -> float:
    """Peso da classe; pares externos específicos sem entrada própria herdam `outer_outer`."""
    if cls in table:
        return float(table[cls])
    if cls in SPECIFIC_OUTER_CLASSES and "outer_outer" in table:
        return float(table["outer_outer"])
    return float(table["other"])


def angular_separation(lon1: float, lon2: float) -> float:
    diff = abs(lon1 - lon2) % 360.0
    return 360.0 - diff if diff > 180.0 else diff


def raw_tension_from_longitudes(longitudes: Dict[str, float], max_orb: float = None) -> float:
    """
    Score bruto contínuo (sem saturação) a partir das longitudes dos corpos centrais.
    Corpos ausentes no dicionário são ignorados; corpos fora de `core_bodies` também.
    """
    cfg = load_score_config()
    sc = cfg["scoring"]
    core = [b for b in sc["core_bodies"] if b in longitudes]
    aspects = aspect_definitions(max_orb)

    tension_pts = 0.0
    harmony_pts = 0.0
    for i in range(len(core)):
        for j in range(i + 1, len(core)):
            b1, b2 = core[i], core[j]
            diff = angular_separation(longitudes[b1], longitudes[b2])
            cls = pair_class(b1, b2)
            for asp in aspects:
                orb = abs(diff - asp["angle"])
                if orb <= asp["orb"]:
                    orb_factor = (asp["orb"] - orb) / asp["orb"]
                    if asp["key"] in ("square", "opposition"):
                        tension_pts += _weight(sc["hard"], cls) * orb_factor
                    elif asp["key"] == "conjunction":
                        tension_pts += _weight(sc["conjunction"], cls) * orb_factor
                    elif asp["key"] == "trine":
                        harmony_pts += _weight(sc["trine"], cls) * orb_factor
                    break
    return float(sc["base_score"] + tension_pts - harmony_pts * sc["harmony_factor"])


def raw_tension_from_array(lons: np.ndarray, body_ids: Iterable[str], max_orb: float = None) -> np.ndarray:
    """
    Versão vetorizada: `lons` tem shape (n_days, n_bodies) na ordem de `body_ids`.
    Retorna o score bruto de cada dia. Reproduz exatamente `raw_tension_from_longitudes`.
    """
    cfg = load_score_config()
    sc = cfg["scoring"]
    body_ids = list(body_ids)
    lons = np.asarray(lons, dtype=np.float64)
    n_days = lons.shape[0]
    tension = np.zeros(n_days)
    harmony = np.zeros(n_days)
    aspects = aspect_definitions(max_orb)

    core_idx = [(i, b) for i, b in enumerate(body_ids) if b in sc["core_bodies"]]
    for a in range(len(core_idx)):
        for b in range(a + 1, len(core_idx)):
            i1, b1 = core_idx[a]
            i2, b2 = core_idx[b]
            diff = np.abs(lons[:, i1] - lons[:, i2]) % 360.0
            diff = np.where(diff > 180.0, 360.0 - diff, diff)
            cls = pair_class(b1, b2)
            claimed = np.zeros(n_days, dtype=bool)  # `break` no primeiro aspecto que casa
            for asp in aspects:
                orb = np.abs(diff - asp["angle"])
                hit = (orb <= asp["orb"]) & ~claimed
                if not hit.any():
                    continue
                factor = (asp["orb"] - orb) / asp["orb"]
                if asp["key"] in ("square", "opposition"):
                    tension += np.where(hit, _weight(sc["hard"], cls) * factor, 0.0)
                elif asp["key"] == "conjunction":
                    tension += np.where(hit, _weight(sc["conjunction"], cls) * factor, 0.0)
                elif asp["key"] == "trine":
                    harmony += np.where(hit, _weight(sc["trine"], cls) * factor, 0.0)
                claimed |= hit
    return sc["base_score"] + tension - harmony * sc["harmony_factor"]


def core_body_ids() -> List[str]:
    return list(load_score_config()["scoring"]["core_bodies"])


def fixed_star_config() -> Dict[str, Any]:
    return load_score_config()["fixed_stars"]
