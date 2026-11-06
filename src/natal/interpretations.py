"""
Composição de textos interpretativos (PT/EN) a partir de data/interpretations/{pt,en}.yaml.

Camadas: 1) texto manual por chave `transit.{corpo}.{família}.{ponto}`; 2) template
processo × tom × ponto (+ casa, duração e passagens). Linguagem reflexiva, sem determinismo
e sem aconselhamento médico, financeiro ou jurídico (ver docs/spec_modulo_pessoal_natal_transitos.md §6.8).
"""

import os
from functools import lru_cache
from typing import Any, Dict, Optional

import yaml

from src.natal.config import ROOT_DIR

INTERP_DIR = os.path.join(ROOT_DIR, "data", "interpretations")


@lru_cache(maxsize=4)
def library(lang: str = "pt") -> Dict[str, Any]:
    path = os.path.join(INTERP_DIR, f"{lang}.yaml")
    if not os.path.exists(path):
        path = os.path.join(INTERP_DIR, "pt.yaml")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _fmt_dates(w: Dict[str, Any], lang: str) -> str:
    lib = library(lang)["phrases"]
    hits = w.get("hits") or []
    if not hits:
        return lib["no_exact"].format(start=w["start"], end=w["end"])
    parts = [h["date"] + (" ℞" if h.get("retrograde") else "") for h in hits]
    if len(hits) == 1:
        return lib["one_pass"].format(start=w["start"], end=w["end"], date=parts[0])
    return lib["many_passes"].format(n=len(hits), start=w["start"], end=w["end"], dates=", ".join(parts))


def describe_window(w: Dict[str, Any], lang: str = "pt") -> str:
    lib = library(lang)
    body, pid, fam = w["transit_body"], w["natal_point"], w.get("family", "focus")
    manual = lib.get("manual", {})
    key = f"transit.{body}.{fam}.{pid}"
    base = manual.get(key)
    if not base:
        proc = lib["processes"].get(body, lib["processes"]["default"])
        point = lib["points"].get(pid, lib["points"]["default"])
        tmpl = lib["templates"].get(fam, lib["templates"]["focus"])
        base = tmpl.format(process=proc.get(fam, proc.get("focus", "")), point=point)
    house = w.get("natal_house")
    house_txt = ""
    if house:
        house_txt = " " + lib["phrases"]["house"].format(house=house, theme=lib["houses"].get(str(house), lib["houses"].get(house, "")))
    return f"{base}{house_txt} {_fmt_dates(w, lang)}".strip()


def describe_cycle(c: Dict[str, Any], lang: str = "pt") -> str:
    lib = library(lang)
    txt = lib.get("cycles", {}).get(c["key"])
    if not txt:
        return ""
    return txt


def describe_progressed_moon_sign(sign_index: int, lang: str = "pt") -> str:
    return library(lang).get("progressed_moon_signs", {}).get(sign_index, "")


def describe_progressed_moon_house(house: int, lang: str = "pt") -> str:
    return library(lang).get("progressed_moon_houses", {}).get(house, "")


def describe_phase(index: int, lang: str = "pt") -> str:
    return library(lang).get("lunation_phases", {}).get(index, "")


def glossary(lang: str = "pt") -> Dict[str, str]:
    return library(lang).get("glossary", {})


def disclaimer(lang: str = "pt") -> str:
    return library(lang)["phrases"]["disclaimer"]
