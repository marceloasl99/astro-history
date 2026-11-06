"""
Classificação dos trânsitos em domínios de vida, processo e tom; intensidade mensal por domínio;
calibração 0–1000 por população sintética; detecção de anos-chave.
"""

import json
import os
from typing import Any, Dict, List, Optional

import numpy as np

from src.natal.config import ROOT_DIR, domains_config
from src.natal.bodies import SAME_BODY

_REFERENCE: Optional[Dict[str, Any]] = None


def domain_keys() -> List[str]:
    return list(domains_config()["domains"].keys())


def domain_label(key: str, lang: str = "pt") -> str:
    d = domains_config()["domains"].get(key, {})
    return d.get("label_en" if lang == "en" else "label_pt", key)


def domain_meta(lang: str = "pt") -> Dict[str, Dict[str, Any]]:
    out = {}
    for k, d in domains_config()["domains"].items():
        out[k] = {"key": k, "label": d.get("label_en" if lang == "en" else "label_pt", k), "icon": d.get("icon", ""),
                  "color": d.get("color", "slate")}
    return out


def point_domain_vector(pid: str, house: Optional[int] = None) -> Dict[str, float]:
    cfg = domains_config()
    base = dict(cfg["point_domains"].get(pid, {}))
    if not base:
        base = {"purpose_transformation": 1.0}
    if house and cfg.get("house_weight", 0) > 0:
        hk = cfg["house_domains"].get(house) or cfg["house_domains"].get(str(house))
        if hk:
            w = float(cfg["house_weight"])
            base = {k: v * (1.0 - w) for k, v in base.items()}
            base[hk] = base.get(hk, 0.0) + w
    s = sum(base.values()) or 1.0
    return {k: round(v / s, 4) for k, v in sorted(base.items(), key=lambda kv: -kv[1]) if v > 0}


def process_of(body: str, lang: str = "pt") -> Dict[str, str]:
    p = domains_config()["processes"].get(body, {"key": "activation", "label_pt": "Ativação", "label_en": "Activation"})
    return {"key": p["key"], "label": p["label_en" if lang == "en" else "label_pt"]}


def weight_of(body: str, point: str, aspect: str) -> float:
    w = domains_config()["weights"]
    return float(w["transit"].get(body, 0.3)) * float(w["point"].get(point, 0.4)) * float(w["aspect"].get(aspect, 0.4))


def classify_windows(windows: List[Dict[str, Any]], natal_houses: Dict[str, Optional[int]], lang: str = "pt") -> None:
    """Acrescenta process/tone/domains/weight/intensity_peak a cada janela (in place)."""
    tones = domains_config()["tone"]
    for w in windows:
        pid = w["natal_point"]
        w["domains"] = point_domain_vector(pid, natal_houses.get(pid))
        w["primary_domain"] = next(iter(w["domains"])) if w["domains"] else None
        proc = process_of(w["transit_body"], lang)
        w["process"] = proc["key"]
        w["process_label"] = proc["label"]
        w["tone"] = tones.get(w["aspect"], "focus")
        w["weight"] = round(weight_of(w["transit_body"], pid, w["aspect"]), 4)
        w["intensity_peak"] = round(w["weight"] * w["peak_closeness"], 4)
        w["is_return"] = SAME_BODY.get(w["transit_body"]) == pid and w["aspect"] == "conjunction"


# ----------------------------------------------------------------------------- séries mensais
def month_index_of_axis(axis: np.ndarray) -> (np.ndarray, List[str]):
    """Índice de mês (0..M-1) de cada dia do eixo e rótulos 'YYYY-MM'."""
    days = axis - 2440587.5  # dias desde 1970-01-01 00:00 UT
    dt = (np.datetime64("1970-01-01") + np.round(days).astype("timedelta64[D]")).astype("datetime64[M]")
    months = np.unique(dt)
    idx = np.searchsorted(months, dt)
    labels = [str(m) for m in months]
    return idx, labels


def monthly_domain_series(windows: List[Dict[str, Any]], axis: np.ndarray) -> Dict[str, Any]:
    keys = domain_keys()
    idx, labels = month_index_of_axis(axis)
    M = len(labels)
    acc = {k: np.zeros(M) for k in keys}
    total = np.zeros(M)
    count = np.bincount(idx, minlength=M).astype(float)
    count[count == 0] = 1.0
    for w in windows:
        c = w.get("_closeness")
        if c is None or w.get("transit_body") == "moon":
            continue
        i0, i1 = w["i0"], w["i1"]
        if i1 >= len(idx):
            continue
        daily = w["weight"] * c.astype(float)
        m_idx = idx[i0:i1 + 1]
        contrib = np.bincount(m_idx, weights=daily, minlength=M)
        total += contrib
        for k, share in w["domains"].items():
            acc[k] += contrib * share
    # média diária no mês (independe do nº de dias do mês)
    return {
        "months": labels,
        "by_domain": {k: (v / count) for k, v in acc.items()},
        "total": total / count,
    }


def annual_totals(monthly: Dict[str, Any]) -> Dict[str, Any]:
    years = sorted({m[:4] for m in monthly["months"]})
    yi = {y: i for i, y in enumerate(years)}
    idx = np.array([yi[m[:4]] for m in monthly["months"]])
    tot = np.bincount(idx, weights=monthly["total"], minlength=len(years))
    cnt = np.bincount(idx, minlength=len(years)).astype(float)
    cnt[cnt == 0] = 1.0
    by_dom = {k: np.bincount(idx, weights=v, minlength=len(years)) / cnt for k, v in monthly["by_domain"].items()}
    return {"years": [int(y) for y in years], "total": tot / cnt, "by_domain": by_dom}


# ----------------------------------------------------------------------------- calibração
def _reference() -> Optional[Dict[str, Any]]:
    global _REFERENCE
    if _REFERENCE is None:
        path = os.path.join(ROOT_DIR, domains_config()["calibration"]["reference_file"])
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                _REFERENCE = json.load(f)
        else:
            _REFERENCE = {}
    return _REFERENCE or None


def score_1000(values: np.ndarray, key: str) -> np.ndarray:
    """Percentil 0–1000 contra a distribuição de referência (população sintética) ou escala saturante."""
    ref = _reference()
    v = np.asarray(values, dtype=float)
    if ref and key in ref.get("quantiles", {}):
        q = np.asarray(ref["quantiles"][key], dtype=float)  # valores dos quantis 0..1000
        return np.clip(np.searchsorted(q, v, side="right") / max(len(q) - 1, 1) * 1000.0, 0, 1000)
    scale = float((ref or {}).get("fallback_scale", {}).get(key, 0.35))
    return 1000.0 * (1.0 - np.exp(-v / scale))


def scored_series(monthly: Dict[str, Any], annual: Dict[str, Any]) -> Dict[str, Any]:
    out = {
        "months": monthly["months"],
        "monthly_1000": {k: np.round(score_1000(v, f"month_{k}")).astype(int).tolist() for k, v in monthly["by_domain"].items()},
        "monthly_total_1000": np.round(score_1000(monthly["total"], "month_total")).astype(int).tolist(),
        "years": annual["years"],
        "annual_1000": {k: np.round(score_1000(v, f"year_{k}")).astype(int).tolist() for k, v in annual["by_domain"].items()},
        "annual_total_1000": np.round(score_1000(annual["total"], "year_total")).astype(int).tolist(),
        "calibrated": bool(_reference()),
    }
    return out


def key_years(annual: Dict[str, Any], scored: Dict[str, Any], windows: List[Dict[str, Any]], top_n: int = 10) -> List[Dict[str, Any]]:
    """Anos de maior intensidade total (máximos locais), com os trânsitos que mais contribuem."""
    tot = np.asarray(annual["total"])
    years = annual["years"]
    if len(tot) == 0:
        return []
    min_pct = float(domains_config()["calibration"].get("key_year_min_percentile", 80))
    s1000 = np.asarray(scored["annual_total_1000"])
    cand = []
    for i in range(len(tot)):
        left = tot[i - 1] if i > 0 else -1
        right = tot[i + 1] if i < len(tot) - 1 else -1
        if tot[i] >= left and tot[i] >= right and s1000[i] >= min_pct * 10:
            cand.append(i)
    cand.sort(key=lambda i: -tot[i])
    out = []
    for i in cand[:top_n]:
        y = years[i]
        ys = f"{y:04d}"
        contrib = []
        for w in windows:
            if w.get("transit_body") == "moon":
                continue
            if w["start"][:4] <= ys <= w["end"][:4]:
                contrib.append((w["intensity_peak"] * min(1.0, w["duration_days"] / 30.0), w))
        contrib.sort(key=lambda x: -x[0])
        out.append({
            "year": y, "score_1000": int(s1000[i]), "raw": round(float(tot[i]), 4),
            "top": [{"id": w["id"], "label": f"{w['transit_symbol']} {w['aspect_symbol']} {w['point_symbol']}",
                     "text": f"{w['transit_name']} {w['aspect_name']} {w['point_name']}", "start": w["start"], "end": w["end"]}
                    for _, w in contrib[:3]],
        })
    out.sort(key=lambda d: d["year"])
    return out


def active_now(windows: List[Dict[str, Any]], jd_now: float, horizon_days: int = 366) -> Dict[str, List[Dict[str, Any]]]:
    """Janelas ativas hoje e próximas passagens exatas nos próximos 12 meses."""
    active, upcoming = [], []
    for w in windows:
        if w["start_jd"] <= jd_now <= w["end_jd"] + 1.0:
            active.append(w)
        for h in w["hits"]:
            if jd_now < h["jd"] <= jd_now + horizon_days:
                upcoming.append({"window_id": w["id"], "date": h["date"], "retrograde": h["retrograde"],
                                 "label": f"{w['transit_symbol']} {w['aspect_symbol']} {w['point_symbol']}",
                                 "text": f"{w['transit_name']} {w['aspect_name']} {w['point_name']}",
                                 "intensity": w["intensity_peak"], "tone": w["tone"], "primary_domain": w["primary_domain"]})
    active.sort(key=lambda w: -w["intensity_peak"])
    upcoming.sort(key=lambda u: u["date"])
    return {"active": active, "upcoming": upcoming}
