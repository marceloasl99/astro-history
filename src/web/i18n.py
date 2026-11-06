"""
i18n server-side por chaves (v6) para as páginas novas (módulo pessoal, glossário, dados & fontes).

- Dicionários em src/web/i18n/{pt,en}.json (chave → texto).
- Idioma: parâmetro `?lang=`, senão cookie `astro_lang` (gravado pelo seletor PT/EN do site), senão 'pt'.
- Exposto ao Jinja como função global `t(key, **fmt)` e variável `lang`.
"""

import json
import os
from functools import lru_cache
from typing import Any, Dict

from fastapi import Request

I18N_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "i18n")
SUPPORTED = ("pt", "en")


@lru_cache(maxsize=4)
def _load(lang: str) -> Dict[str, str]:
    path = os.path.join(I18N_DIR, f"{lang}.json")
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def resolve_lang(request: Request) -> str:
    q = request.query_params.get("lang")
    if q in SUPPORTED:
        return q
    c = request.cookies.get("astro_lang")
    if c in SUPPORTED:
        return c
    return "pt"


def translate(key: str, lang: str = "pt", **fmt: Any) -> str:
    text = _load(lang).get(key)
    if text is None:
        text = _load("pt").get(key, key)
    if fmt:
        try:
            text = text.format(**fmt)
        except (KeyError, IndexError):
            pass
    return text


def translator(lang: str):
    def t(key: str, **fmt: Any) -> str:
        return translate(key, lang, **fmt)
    return t


def missing_keys(reference: str = "pt", other: str = "en") -> Dict[str, Any]:
    """Para testes: chaves presentes em um idioma e ausentes no outro."""
    a, b = set(_load(reference)), set(_load(other))
    return {"only_in_" + reference: sorted(a - b), "only_in_" + other: sorted(b - a)}
