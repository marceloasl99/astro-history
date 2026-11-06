"""
Datas do catálogo (v6): parsing único para 'YYYY-MM-DD' e '-YYYY-MM-DD' (a.C. histórico).

Convenção: "-0490-09-12" significa 12/09/490 a.C. (ano histórico). O ano ASTRONÔMICO
correspondente é 1 − 490 = −489 (o Swiss Ephemeris numera 1 a.C. como ano 0).
"""

from typing import Tuple

import swisseph as swe


def parse_catalog_date(date_str: str) -> Tuple[int, int, int, bool]:
    """Retorna (ano_astronômico, mês, dia, é_aC)."""
    s = date_str.strip()
    if s.startswith("-"):
        parts = s[1:].split("-")
        if len(parts) != 3:
            raise ValueError(f"data inválida: {date_str}")
        y, m, d = (int(x) for x in parts)
        return 1 - y, m, d, True
    parts = s.split("-")
    if len(parts) != 3:
        raise ValueError(f"data inválida: {date_str}")
    y, m, d = (int(x) for x in parts)
    return y, m, d, False


def historical_year(date_str: str) -> int:
    """Ano histórico com sinal (490 a.C. → -490) para ordenação/exibição; 1 d.C. → 1."""
    y, _, _, bce = parse_catalog_date(date_str)
    return (y - 1) if bce else y


def catalog_date_to_jd(date_str: str, hour_ut: float = 12.0) -> float:
    """JD UT ao meio-dia (ou hora dada) com calendário juliano antes de 15/10/1582 (regra 'default')."""
    y, m, d, _ = parse_catalog_date(date_str)
    cal = swe.GREG_CAL if (y, m, d) >= (1582, 10, 15) else swe.JUL_CAL
    return swe.julday(y, m, d, hour_ut, cal)


def format_historical(date_str: str, lang: str = "pt") -> str:
    """'-0490-09-12' → '12/09/490 a.C.' (pt) ou '490 BCE-09-12' (en)."""
    y, m, d, bce = parse_catalog_date(date_str)
    yh = (1 - y) if bce else y
    if lang == "en":
        return f"{yh} {'BCE' if bce else 'CE'}-{m:02d}-{d:02d}" if bce else f"{yh:04d}-{m:02d}-{d:02d}"
    return f"{d:02d}/{m:02d}/{yh}{' a.C.' if bce else ''}"
