"""
Scanner vetorizado de trânsitos (corpo em trânsito × ponto natal × aspecto) sobre um eixo diário.

- Orbe por planeta em trânsito (config/natal.yaml) + bônus para luminares/ângulos.
- Janelas = períodos contínuos dentro da orbe; passagens exatas por interpolação linear entre
  amostras diárias (erro < 1 h para corpos rápidos, < 1 min para lentos) e, para corpos lentos,
  refinamento por secante com o Swiss Ephemeris (refine: precise).
- Passagens retrógradas detectadas naturalmente; janelas da mesma série (ex.: 3 passagens de
  Saturno) agrupadas em "episódios".
- Alvos constantes (mapa natal) ou séries alinhadas ao eixo (mapa progredido).
- Lua em trânsito: opcional, apenas em intervalos ≤ 2 anos, eixo horário.
"""

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, Union

import numpy as np
import swisseph as swe

from src.core.ephemeris import ensure_ephe_path
from src.natal.bodies import SWE_IDS, SAME_BODY, name as point_name, symbol as point_symbol
from src.natal.config import aspect_defs, natal_config, target_bonus, transit_orb
from src.natal.ephemeris_cache import CALC_FLAGS, day_axis, hourly_series, series

TargetValue = Union[float, np.ndarray]
TROPICAL_YEAR = 365.24219
UNIX_EPOCH_JD = 2440587.5


def wrap180(x):
    return (x + 180.0) % 360.0 - 180.0


def wrap360(x):
    return x % 360.0


def jd_array_to_iso(jd: np.ndarray) -> List[str]:
    """Conversão vetorizada JD (UT) → 'YYYY-MM-DD' (gregoriano)."""
    jd = np.asarray(jd, dtype=np.float64)
    if jd.size == 0:
        return []
    secs = np.round((jd - UNIX_EPOCH_JD) * 86400.0).astype("int64")
    dt = np.datetime64("1970-01-01T00:00:00") + secs.astype("timedelta64[s]")
    return np.datetime_as_string(dt, unit="D").tolist()


def jd_array_to_iso_minutes(jd: np.ndarray) -> List[str]:
    jd = np.asarray(jd, dtype=np.float64)
    if jd.size == 0:
        return []
    secs = np.round((jd - UNIX_EPOCH_JD) * 86400.0).astype("int64")
    dt = np.datetime64("1970-01-01T00:00:00") + secs.astype("timedelta64[s]")
    return [s.replace("T", " ") + " UT" for s in np.datetime_as_string(dt, unit="m").tolist()]


def _runs(mask: np.ndarray) -> List[Tuple[int, int]]:
    if not mask.any():
        return []
    m = mask.astype(np.int8)
    edges = np.diff(m)
    starts = np.where(edges == 1)[0] + 1
    ends = np.where(edges == -1)[0]
    if m[0]:
        starts = np.r_[0, starts]
    if m[-1]:
        ends = np.r_[ends, len(m) - 1]
    return list(zip(starts.tolist(), ends.tolist()))


def _merge_runs(runs: List[Tuple[int, int]], gap: int) -> List[Tuple[int, int, int]]:
    if not runs:
        return []
    out = [[runs[0][0], runs[0][1], 0]]
    for s, e in runs[1:]:
        g = s - out[-1][1] - 1
        if gap > 0 and g <= gap:
            out[-1][2] = max(out[-1][2], g)
            out[-1][1] = e
        else:
            out.append([s, e, 0])
    return [tuple(x) for x in out]


def _body_lon_speed(body: str, jd: float) -> Tuple[float, float]:
    res, _ = swe.calc_ut(float(jd), SWE_IDS[body], CALC_FLAGS)
    return float(res[0]), float(res[3])


def _refine_secant(body: str, t0: float, t1: float, target_fn: Callable[[float], float], angle: float,
                   iterations: int = 3) -> Tuple[float, bool]:
    """Refina um cruzamento interpolado com 2–3 passos de secante usando o Swiss Ephemeris."""
    f = lambda t: wrap180(_body_lon_speed(body, t)[0] - target_fn(t) - angle)  # noqa: E731
    a, b = t0, t1
    fa, fb = f(a), f(b)
    t = b
    for _ in range(iterations):
        if fb == fa:
            break
        t = b - fb * (b - a) / (fb - fa)
        if not (min(t0, t1) - 1.0 <= t <= max(t0, t1) + 1.0):
            t = 0.5 * (a + b)
        ft = f(t)
        a, fa, b, fb = b, fb, t, ft
        if abs(ft) < 1e-6:
            break
    return t, _body_lon_speed(body, t)[1] < 0


class Targets:
    """Alvos natais (constantes) ou progredidos (séries alinhadas ao eixo)."""

    def __init__(self, axis: np.ndarray, values: Dict[str, TargetValue], extra_orb: Optional[Dict[str, float]] = None):
        self.axis = np.asarray(axis, dtype=np.float64)
        self.values = values
        self.extra_orb = extra_orb or {}

    def ids(self) -> List[str]:
        return list(self.values.keys())

    def is_moving(self, pid: str) -> bool:
        return not np.isscalar(self.values[pid])

    def lon(self, pid: str) -> np.ndarray:
        v = self.values[pid]
        if np.isscalar(v):
            return np.full(len(self.axis), float(v))
        return np.asarray(v, dtype=np.float64)

    def speed(self, pid: str) -> np.ndarray:
        v = self.values[pid]
        if np.isscalar(v):
            return np.zeros(len(self.axis))
        arr = np.asarray(v, dtype=np.float64)
        if len(arr) < 2:
            return np.zeros(len(arr))
        d = wrap180(np.diff(arr))
        return np.r_[d, d[-1]]

    def fn(self, pid: str) -> Callable[[float], float]:
        v = self.values[pid]
        if np.isscalar(v):
            c = float(v)
            return lambda t: c
        arr = np.asarray(v, dtype=np.float64)
        axis = self.axis

        def interp(t: float) -> float:
            i = int(np.clip(np.searchsorted(axis, t) - 1, 0, len(axis) - 2))
            span = axis[i + 1] - axis[i]
            frac = (t - axis[i]) / span if span else 0.0
            return wrap360(arr[i] + wrap180(arr[i + 1] - arr[i]) * frac)
        return interp


def _aspect_angles(asp: Dict[str, Any]) -> List[float]:
    a = float(asp["angle"])
    return [a] if a in (0.0, 180.0) else [a, 360.0 - a]


def _scan_pair(body: str, LT: np.ndarray, vT: np.ndarray, axis: np.ndarray, targets: Targets, pid: str,
               orb: float, asp: Dict[str, Any], merge_gap: int, precise: bool, raw: List[Dict[str, Any]]) -> None:
    LP = targets.lon(pid)
    vP = targets.speed(pid)
    tfn = targets.fn(pid) if precise else None
    for a in _aspect_angles(asp):
        d = wrap180(LT - LP - a)
        inorb = np.abs(d) <= orb
        if not inorb.any():
            continue
        for s, e, gap in _merge_runs(_runs(inorb), merge_gap):
            seg = d[s:e + 1]
            sgn = np.sign(seg)
            hit_jd: List[float] = []
            hit_retro: List[bool] = []
            zeros = np.where(sgn == 0)[0]
            for z in zeros:
                hit_jd.append(float(axis[s + z]))
                hit_retro.append(bool(vT[s + z] < 0))
            cross = np.where(sgn[:-1] * sgn[1:] < 0)[0]
            if cross.size:
                frac = seg[cross] / (seg[cross] - seg[cross + 1])
                t_lin = axis[s + cross] + frac * (axis[s + cross + 1] - axis[s + cross])
                retro = (vT[s + cross] + vT[s + cross + 1]) < 0
                for k, c in enumerate(cross):
                    if precise:
                        t, r = _refine_secant(body, float(axis[s + c]), float(axis[s + c + 1]), tfn, a)
                        hit_jd.append(t)
                        hit_retro.append(bool(r))
                    else:
                        hit_jd.append(float(t_lin[k]))
                        hit_retro.append(bool(retro[k]))
            order = np.argsort(hit_jd) if hit_jd else []
            hit_jd = [hit_jd[i] for i in order]
            hit_retro = [hit_retro[i] for i in order]
            closeness = np.clip(1.0 - np.abs(seg) / orb, 0.0, 1.0)
            peak_i = int(np.argmax(closeness))
            rel0 = vT[s] - vP[s]
            raw.append({
                "transit_body": body, "natal_point": pid, "aspect": asp["key"], "aspect_name": asp["name"],
                "aspect_symbol": asp["symbol"], "family": asp["family"], "angle": float(asp["angle"]),
                "waxing": a <= 180.0, "orb_max": round(orb, 2), "i0": int(s), "i1": int(e),
                "start_jd": float(axis[s]), "end_jd": float(axis[e]), "duration_days": int(e - s + 1), "gap_days": int(gap),
                "hit_jd": hit_jd, "hit_retro": hit_retro, "applying_at_start": bool(seg[0] * rel0 < 0),
                "peak_closeness": round(float(closeness[peak_i]), 4), "peak_jd": float(axis[s + peak_i]),
                "at_birth": s == 0, "_closeness": closeness.astype(np.float32),
            })


def _finalize(raw: List[Dict[str, Any]], birth_jd: float, mode: str, lang: str, hourly: bool = False) -> List[Dict[str, Any]]:
    """Completa os campos textuais de forma vetorizada."""
    if not raw:
        return []
    starts = np.array([r["start_jd"] for r in raw])
    ends = np.array([r["end_jd"] for r in raw])
    peaks = np.array([r["peak_jd"] for r in raw])
    s_iso, e_iso, p_iso = jd_array_to_iso(starts), jd_array_to_iso(ends), jd_array_to_iso(peaks)
    all_hits = np.array([h for r in raw for h in r["hit_jd"]], dtype=np.float64)
    hit_iso = jd_array_to_iso(all_hits)
    hit_iso_min = jd_array_to_iso_minutes(all_hits)
    names = {}
    k = 0
    windows = []
    for i, r in enumerate(raw):
        body, pid = r["transit_body"], r["natal_point"]
        if body not in names:
            names[body] = (point_name(body, lang), point_symbol(body))
        if pid not in names:
            names[pid] = (point_name(pid, lang), point_symbol(pid))
        hits = []
        for j, hj in enumerate(r["hit_jd"]):
            hits.append({"jd": hj, "date": hit_iso[k], "datetime_ut": hit_iso_min[k], "retrograde": r["hit_retro"][j],
                         "age": round((hj - birth_jd) / TROPICAL_YEAR, 2)})
            k += 1
        w = {key: v for key, v in r.items() if key not in ("hit_jd", "hit_retro")}
        if hourly:
            w["start"], w["end"], w["peak_date"] = jd_array_to_iso_minutes([starts[i]])[0], jd_array_to_iso_minutes([ends[i]])[0], p_iso[i]
        else:
            w["start"], w["end"], w["peak_date"] = s_iso[i], e_iso[i], p_iso[i]
        w["hits"] = hits
        w["n_passes"] = len(hits)
        w["exact"] = len(hits) > 0
        w["age_start"] = round((r["start_jd"] - birth_jd) / TROPICAL_YEAR, 2)
        w["age_end"] = round((r["end_jd"] - birth_jd) / TROPICAL_YEAR, 2)
        w["target_mode"] = mode
        w["transit_name"], w["transit_symbol"] = names[body]
        w["point_name"], w["point_symbol"] = names[pid]
        windows.append(w)
    return windows


def _assign_episodes(windows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Agrupa janelas consecutivas da mesma série (corpo, ponto, aspecto, fase) em episódios."""
    cfg = natal_config()
    slow = set(cfg["slow_bodies"])
    gap_by_body = {"pluto": 600, "neptune": 600, "uranus": 560, "saturn": 420, "chiron": 500, "mean_node": 400, "jupiter": 330}
    order = sorted(range(len(windows)), key=lambda i: (windows[i]["transit_body"], windows[i]["natal_point"],
                                                       windows[i]["aspect"], windows[i]["waxing"], windows[i]["start_jd"]))
    episodes: List[Dict[str, Any]] = []
    prev_key = None
    cur: Optional[Dict[str, Any]] = None
    for i in order:
        w = windows[i]
        key = (w["transit_body"], w["natal_point"], w["aspect"], w["waxing"])
        gap = gap_by_body.get(w["transit_body"], 0) if w["transit_body"] in slow else 0
        if cur is not None and key == prev_key and gap and (w["start_jd"] - cur["end_jd"]) <= gap:
            cur["end_jd"] = max(cur["end_jd"], w["end_jd"])
            cur["end"] = max(cur["end"], w["end"])
            cur["window_ids"].append(w["id"])
            cur["hits"].extend(w["hits"])
            cur["peak_closeness"] = max(cur["peak_closeness"], w["peak_closeness"])
        else:
            cur = {"id": f"ep-{len(episodes)}", "transit_body": w["transit_body"], "natal_point": w["natal_point"],
                   "aspect": w["aspect"], "aspect_symbol": w["aspect_symbol"], "aspect_name": w["aspect_name"],
                   "family": w["family"], "waxing": w["waxing"], "start_jd": w["start_jd"], "end_jd": w["end_jd"],
                   "start": w["start"], "end": w["end"], "window_ids": [w["id"]], "hits": list(w["hits"]),
                   "peak_closeness": w["peak_closeness"], "transit_name": w["transit_name"],
                   "transit_symbol": w["transit_symbol"], "point_name": w["point_name"], "point_symbol": w["point_symbol"]}
            episodes.append(cur)
            prev_key = key
        w["episode_id"] = cur["id"]
    for ep in episodes:
        ep["hits"].sort(key=lambda h: h["jd"])
        ep["n_passes"] = len(ep["hits"])
        ep["n_windows"] = len(ep["window_ids"])
        ep["age_start"] = None
    episodes.sort(key=lambda e: e["start_jd"])
    return episodes


def scan_transits(targets: Targets, *, birth_jd: float, bodies: Sequence[str], preset: str = "standard",
                  custom_orbs: Optional[Dict[str, float]] = None, include_minor: bool = False,
                  mode: str = "natal", lang: str = "pt", moon_extra_orb: float = 0.0,
                  precise: Optional[bool] = None) -> Dict[str, Any]:
    """
    Varre todos os pares (corpo em trânsito, ponto natal, aspecto) no eixo de `targets`.
    Retorna {"windows": [...], "episodes": [...], "notes": [...], "axis": eixo}.
    """
    ensure_ephe_path()
    cfg = natal_config()
    axis = targets.axis
    aspects = aspect_defs(include_minor)
    slow = set(cfg["slow_bodies"])
    gap_slow = int(cfg["window_merge_gap_days"]["slow"])
    gap_fast = int(cfg["window_merge_gap_days"]["fast"])
    if precise is None:
        precise = str(cfg.get("refine", "precise")) in ("precise", "bisection", "secant")
    raw: List[Dict[str, Any]] = []
    notes: List[str] = []

    for body in bodies:
        if body == "moon":
            continue
        LT, vT = series(body, axis)
        base_orb = transit_orb(body, preset, custom_orbs)
        merge_gap = gap_slow if body in slow else gap_fast
        body_precise = precise and body in slow
        for pid in targets.ids():
            orb = base_orb + target_bonus(pid) + (moon_extra_orb if pid == "moon" else 0.0) + float(targets.extra_orb.get(pid, 0.0))
            for asp in aspects:
                o = orb * (float(cfg["aspects"]["minor_orb_factor"]) if asp.get("minor") else 1.0)
                _scan_pair(body, LT, vT, axis, targets, pid, o, asp, merge_gap, body_precise, raw)

    windows = _finalize(raw, birth_jd, mode, lang)

    if "moon" in bodies:
        span_years = (axis[-1] - axis[0]) / TROPICAL_YEAR
        if span_years > 2.05:
            notes.append("moon_skipped_long_range")
        else:
            jds, LT, vT = hourly_series("moon", float(axis[0]), float(axis[-1]) + 1.0)
            h_vals: Dict[str, TargetValue] = {}
            for pid in targets.ids():
                if targets.is_moving(pid):
                    unwrapped = np.degrees(np.unwrap(np.radians(targets.lon(pid))))
                    h_vals[pid] = wrap360(np.interp(jds, axis, unwrapped))
                else:
                    h_vals[pid] = targets.values[pid]
            h_targets = Targets(jds, h_vals)
            base_orb = transit_orb("moon", preset, custom_orbs)
            allowed = set(cfg["targets"]["moon_transit_aspects"])
            raw_m: List[Dict[str, Any]] = []
            for pid in h_targets.ids():
                orb = base_orb + target_bonus(pid)
                for asp in aspects:
                    if asp["key"] in allowed:
                        _scan_pair("moon", LT, vT, jds, h_targets, pid, orb, asp, 0, False, raw_m)
            windows.extend(_finalize(raw_m, birth_jd, mode, lang, hourly=True))

    windows.sort(key=lambda w: (w["start_jd"], w["transit_body"], w["natal_point"]))
    for k, w in enumerate(windows):
        w["id"] = f"{w['transit_body']}-{w['aspect']}-{w['natal_point']}-{w['start'][:10].replace('-', '')}-{k}"
    episodes = _assign_episodes([w for w in windows if w["transit_body"] != "moon"])
    return {"windows": windows, "episodes": episodes, "notes": notes, "axis": axis}


# ----------------------------------------------------------------------------- casas em trânsito
def scan_house_ingresses(cusps: List[float], axis: np.ndarray, bodies: Sequence[str], birth_jd: float,
                         lang: str = "pt") -> List[Dict[str, Any]]:
    """Ingressos (e reentradas retrógradas) de corpos lentos nas 12 casas natais."""
    if not cusps or len(cusps) != 12:
        return []
    c = np.asarray(cusps, dtype=np.float64)
    out: List[Dict[str, Any]] = []
    for body in bodies:
        LT, vT = series(body, axis)
        offsets = wrap360(LT[:, None] - c[None, :])
        house = np.argmin(offsets, axis=1) + 1
        change = np.where(house[:-1] != house[1:])[0]
        ingresses = []
        for ci in change:
            h0, h1 = int(house[ci]), int(house[ci + 1])
            boundary = float(c[h1 - 1]) if h1 == (h0 % 12) + 1 else float(c[h0 - 1])
            d0 = wrap180(LT[ci] - boundary)
            d1 = wrap180(LT[ci + 1] - boundary)
            frac = d0 / (d0 - d1) if d0 != d1 else 0.5
            jd_hit = float(axis[ci]) + frac
            ingresses.append({"from_house": h0, "to_house": h1, "jd": jd_hit, "retrograde": bool(vT[ci + 1] < 0),
                              "age": round((jd_hit - birth_jd) / TROPICAL_YEAR, 2)})
        dates = jd_array_to_iso([g["jd"] for g in ingresses])
        for g, dt in zip(ingresses, dates):
            g["date"] = dt
        periods = []
        prev_i = 0
        bounds = [int(x) for x in change] + [len(axis) - 1]
        starts_iso = jd_array_to_iso([axis[prev_i]] + [axis[ci + 1] for ci in change])
        ends_iso = jd_array_to_iso([axis[b] for b in bounds])
        idxs = [0] + [int(ci) + 1 for ci in change]
        for n, i in enumerate(idxs):
            periods.append({"house": int(house[i]), "start": starts_iso[n], "end": ends_iso[n]})
        out.append({"body": body, "body_name": point_name(body, lang), "symbol": point_symbol(body),
                    "ingresses": ingresses, "periods": periods, "house_at_start": int(house[0])})
    return out


# ----------------------------------------------------------------------------- utilidades
def lifetime_axis(birth_jd: float, years: float, range_from: Optional[int] = None,
                  range_to: Optional[int] = None) -> np.ndarray:
    start = birth_jd
    end = birth_jd + years * TROPICAL_YEAR
    if range_from is not None:
        start = max(start, swe.julday(range_from, 1, 1, 0.0, swe.GREG_CAL))
    if range_to is not None:
        end = min(end, swe.julday(range_to, 12, 31, 0.0, swe.GREG_CAL))
    if end < start:
        end = start + 1.0
    return day_axis(start, end)


def strip_internal(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [{k: v for k, v in w.items() if not k.startswith("_")} for w in items]
