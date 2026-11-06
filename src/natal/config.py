"""Carregamento (com cache) das configurações do módulo pessoal."""

import os
from functools import lru_cache
from typing import Any, Dict, List

import yaml

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CONFIG_DIR = os.path.join(ROOT_DIR, "config")
NATAL_FILE = os.path.join(CONFIG_DIR, "natal.yaml")
DOMAINS_FILE = os.path.join(CONFIG_DIR, "natal_domains.yaml")


@lru_cache(maxsize=1)
def natal_config() -> Dict[str, Any]:
    with open(NATAL_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@lru_cache(maxsize=1)
def domains_config() -> Dict[str, Any]:
    with open(DOMAINS_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def aspect_defs(include_minor: bool = False) -> List[Dict[str, Any]]:
    cfg = natal_config()["aspects"]
    out = [dict(a) for a in cfg["major"]]
    if include_minor:
        for a in cfg["minor"]:
            d = dict(a)
            d["minor"] = True
            out.append(d)
    return out


def aspect_by_key(key: str) -> Dict[str, Any]:
    for a in aspect_defs(include_minor=True):
        if a["key"] == key:
            return a
    raise KeyError(key)


def transit_orb(body_id: str, preset: str = "standard", custom: Dict[str, float] = None) -> float:
    cfg = natal_config()
    base = float((custom or {}).get(body_id, cfg["transit_orbs"].get(body_id, 1.0)))
    factor = float(cfg["orb_presets"].get(preset, 1.0)) if preset != "custom" else 1.0
    return round(base * factor, 3)


def target_bonus(point_id: str) -> float:
    return float(natal_config().get("target_bonus", {}).get(point_id, 0.0))


def grid_path() -> str:
    return os.path.join(ROOT_DIR, natal_config()["grid"]["file"])
