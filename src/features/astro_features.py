"""
Matriz de features astrológicas diárias (1750–2150) para modelagem preditiva.

Operacionaliza os construtos da astrologia mundana moderna como variáveis contínuas:
- Fase dos ciclos sinódicos dos 5 planetas externos (seno/cosseno), geo e heliocêntrica.
- Índice Cíclico de Barbault (soma das separações angulares dos externos).
- Ativação de aspectos com kernel gaussiano (sem corte binário de orbe).
- Harmônicos 4 e 8 (concentração angular), declinação e fora-de-limites.
- Retrogradação, estações, ingressos e signos cardinais.
- Meios-pontos (Ebertin) ativados pelo Sol, Marte e Júpiter.
- Proximidade a eclipses solares e lunares.
- Índice legado de tensão (config/score.yaml) para comparação.

Tudo é calculado ao meio-dia UT. A Lua fica fora (resolução diária).
"""

import os
from datetime import date, timedelta
from typing import Dict, List, Tuple, Any, Optional

import numpy as np
import swisseph as swe

from src.core.scoring import raw_tension_from_array

for _p in ["/usr/share/libswe/ephe", "/usr/share/swisseph", "/usr/local/share/swisseph"]:
    if os.path.exists(_p):
        swe.set_ephe_path(_p)
        break

FEATURES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "features"))
GRID_FILE = os.path.join(FEATURES_DIR, "daily_astro_1750_2150.npz")

BODIES: List[Tuple[str, int]] = [
    ("sun", swe.SUN), ("mercury", swe.MERCURY), ("venus", swe.VENUS), ("mars", swe.MARS),
    ("jupiter", swe.JUPITER), ("saturn", swe.SATURN), ("uranus", swe.URANUS),
    ("neptune", swe.NEPTUNE), ("pluto", swe.PLUTO),
]
BODY_IDS = [b[0] for b in BODIES]
OUTER5 = ["jupiter", "saturn", "uranus", "neptune", "pluto"]
HELIO_BODIES = [b for b in BODY_IDS if b != "sun"]
ASPECT_ANGLES = [0.0, 60.0, 90.0, 120.0, 180.0]
OBLIQUITY = 23.44

_CACHE: Optional[Dict[str, Any]] = None


# ----------------------------------------------------------------------------- grade bruta
def build_raw_grid(start_year: int = 1750, end_year: int = 2150, verbose: bool = True) -> Dict[str, Any]:
    os.makedirs(FEATURES_DIR, exist_ok=True)
    start, end = date(start_year, 1, 1), date(end_year, 12, 31)
    n = (end - start).days + 1
    jd = np.empty(n)
    ymd = np.empty((n, 3), dtype=np.int16)
    lon = np.empty((n, len(BODIES)), dtype=np.float32)
    speed = np.empty((n, len(BODIES)), dtype=np.float32)
    dec = np.empty((n, len(BODIES)), dtype=np.float32)
    hlon = np.empty((n, len(HELIO_BODIES)), dtype=np.float32)

    flag_geo = swe.FLG_SWIEPH | swe.FLG_SPEED
    flag_eq = swe.FLG_SWIEPH | swe.FLG_EQUATORIAL
    flag_hel = swe.FLG_SWIEPH | swe.FLG_HELCTR
    helio_ids = [dict(BODIES)[b] for b in HELIO_BODIES]

    d = start
    for i in range(n):
        j = swe.julday(d.year, d.month, d.day, 12.0)
        jd[i] = j
        ymd[i] = (d.year, d.month, d.day)
        for k, (_, sid) in enumerate(BODIES):
            r, _ = swe.calc_ut(j, sid, flag_geo)
            lon[i, k], speed[i, k] = r[0], r[3]
            r, _ = swe.calc_ut(j, sid, flag_eq)
            dec[i, k] = r[1]
        for k, sid in enumerate(helio_ids):
            r, _ = swe.calc_ut(j, sid, flag_hel)
            hlon[i, k] = r[0]
        if verbose and i % 20000 == 0:
            print(f"  {d} ({i}/{n})")
        d += timedelta(days=1)

    sol = _eclipses(jd[0], jd[-1], solar=True)
    lun = _eclipses(jd[0], jd[-1], solar=False)
    np.savez_compressed(
        GRID_FILE, jd=jd, ymd=ymd, lon=lon, speed=speed, dec=dec, hlon=hlon,
        solar_eclipses=np.array(sol), lunar_eclipses=np.array(lun),
        start_year=np.int32(start_year), end_year=np.int32(end_year),
    )
    return load_raw_grid(force=True)


def _eclipses(jd_start: float, jd_end: float, solar: bool) -> List[Tuple[float, int]]:
    """Lista (jd_max, tipo) de eclipses entre jd_start e jd_end."""
    out = []
    j = jd_start
    while True:
        try:
            if solar:
                rflag, tret = swe.sol_eclipse_when_glob(j, swe.FLG_SWIEPH, 0)
            else:
                rflag, tret = swe.lun_eclipse_when(j, swe.FLG_SWIEPH, 0)
        except Exception:
            break
        t = tret[0]
        if t > jd_end or t <= j:
            break
        out.append((t, int(rflag)))
        j = t + 1.0
    return out


def load_raw_grid(force: bool = False) -> Dict[str, Any]:
    global _CACHE
    if _CACHE is not None and not force:
        return _CACHE
    if not os.path.exists(GRID_FILE):
        raise FileNotFoundError(f"{GRID_FILE} não existe. Rode: python -m src.features.astro_features")
    z = np.load(GRID_FILE)
    _CACHE = {k: z[k] for k in z.files}
    return _CACHE


# ----------------------------------------------------------------------------- derivadas
def _sep(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    d = np.abs(a - b) % 360.0
    return np.where(d > 180.0, 360.0 - d, d)


def _gauss(x: np.ndarray, sigma: float) -> np.ndarray:
    return np.exp(-0.5 * (x / sigma) ** 2)


def _sigma(b1: str, b2: str) -> float:
    outer = {"saturn", "uranus", "neptune", "pluto"}
    if b1 in outer and b2 in outer:
        return 5.0
    if b1 in ("jupiter", *outer) and b2 in ("jupiter", *outer):
        return 4.0
    return 2.0


def derive_daily_features(grid: Optional[Dict[str, Any]] = None) -> Tuple[np.ndarray, List[str]]:
    """Retorna (X diário [n_days, n_feat], nomes). Vetorizado."""
    g = grid or load_raw_grid()
    lon = g["lon"].astype(np.float64)
    speed = g["speed"].astype(np.float64)
    dec = g["dec"].astype(np.float64)
    hlon = g["hlon"].astype(np.float64)
    jd = g["jd"]
    idx = {b: i for i, b in enumerate(BODY_IDS)}
    hidx = {b: i for i, b in enumerate(HELIO_BODIES)}
    cols: Dict[str, np.ndarray] = {}

    # 1. Fases sinódicas e índice de Barbault (geo e helio)
    barb = np.zeros(len(jd))
    hbarb = np.zeros(len(jd))
    for i in range(len(OUTER5)):
        for j in range(i + 1, len(OUTER5)):
            fast, slow = OUTER5[i], OUTER5[j]
            ph = np.deg2rad((lon[:, idx[fast]] - lon[:, idx[slow]]) % 360.0)
            cols[f"phase_sin_{fast}_{slow}"] = np.sin(ph)
            cols[f"phase_cos_{fast}_{slow}"] = np.cos(ph)
            cols[f"phase_sin2_{fast}_{slow}"] = np.sin(2 * ph)  # captura quadraturas/oposições
            cols[f"phase_cos2_{fast}_{slow}"] = np.cos(2 * ph)
            s = _sep(lon[:, idx[fast]], lon[:, idx[slow]])
            cols[f"sep_{fast}_{slow}"] = s
            barb += s
            hph = np.deg2rad((hlon[:, hidx[fast]] - hlon[:, hidx[slow]]) % 360.0)
            cols[f"hphase_sin_{fast}_{slow}"] = np.sin(hph)
            cols[f"hphase_cos_{fast}_{slow}"] = np.cos(hph)
            hbarb += _sep(hlon[:, hidx[fast]], hlon[:, hidx[slow]])
    cols["barbault_index"] = barb
    cols["barbault_index_helio"] = hbarb

    # 2. Ativação de aspectos (kernel gaussiano) para todos os pares dos 9 corpos
    hard_outer = np.zeros(len(jd))
    hard_all = np.zeros(len(jd))
    soft_all = np.zeros(len(jd))
    conj_outer = np.zeros(len(jd))
    for i in range(len(BODY_IDS)):
        for j in range(i + 1, len(BODY_IDS)):
            b1, b2 = BODY_IDS[i], BODY_IDS[j]
            s = _sep(lon[:, i], lon[:, j])
            sg = _sigma(b1, b2)
            for ang in ASPECT_ANGLES:
                act = _gauss(s - ang, sg)
                cols[f"asp_{b1}_{b2}_{int(ang)}"] = act
                if ang in (90.0, 180.0):
                    hard_all += act
                    if b1 in OUTER5 and b2 in OUTER5:
                        hard_outer += act
                elif ang in (60.0, 120.0):
                    soft_all += act
                elif ang == 0.0 and b1 in OUTER5 and b2 in OUTER5:
                    conj_outer += act
    cols["hard_outer_total"] = hard_outer
    cols["hard_all_total"] = hard_all
    cols["soft_all_total"] = soft_all
    cols["conj_outer_total"] = conj_outer

    # 3. Harmônicos (comprimento do vetor resultante)
    for h in (4, 8):
        for label, bodies in (("outer", OUTER5), ("all", BODY_IDS)):
            ang = np.deg2rad(h * lon[:, [idx[b] for b in bodies]])
            cols[f"harm{h}_{label}"] = np.hypot(np.cos(ang).mean(axis=1), np.sin(ang).mean(axis=1))

    # 4. Declinação e fora-de-limites
    for b in ("mercury", "venus", "mars", "jupiter", "saturn", "uranus", "neptune", "pluto"):
        cols[f"dec_{b}"] = dec[:, idx[b]]
    for b in ("mercury", "venus", "mars"):
        cols[f"oob_{b}"] = (np.abs(dec[:, idx[b]]) > OBLIQUITY).astype(float)

    # 5. Retrogradação, estações, ingressos, cardinais
    for b in BODY_IDS[1:]:
        sp = speed[:, idx[b]]
        cols[f"retro_{b}"] = (sp < 0).astype(float)
        st = np.zeros(len(jd))
        st[1:] = (np.sign(sp[1:]) != np.sign(sp[:-1])).astype(float)
        cols[f"station_{b}"] = st
    for b in OUTER5:
        sign = np.floor(lon[:, idx[b]] / 30.0).astype(int)
        ing = np.zeros(len(jd))
        ing[1:] = (sign[1:] != sign[:-1]).astype(float)
        cols[f"ingress_{b}"] = ing
        cols[f"cardinal_{b}"] = np.isin(sign, [0, 3, 6, 9]).astype(float)
        cols[f"sign_sin_{b}"] = np.sin(np.deg2rad(lon[:, idx[b]]))
        cols[f"sign_cos_{b}"] = np.cos(np.deg2rad(lon[:, idx[b]]))

    # 6. Meios-pontos (Ebertin): eixo de 90° (conjunção/quadratura/oposição ao meio-ponto)
    for a, b in (("mars", "saturn"), ("saturn", "pluto"), ("uranus", "pluto"), ("saturn", "neptune"), ("saturn", "uranus")):
        mp = ((lon[:, idx[a]] + lon[:, idx[b]]) / 2.0) % 360.0
        for c in ("sun", "mars", "jupiter"):
            if c in (a, b):
                continue
            dist = np.abs((lon[:, idx[c]] - mp + 45.0) % 90.0 - 45.0)
            cols[f"mp_{a}_{b}_{c}"] = _gauss(dist, 1.5)

    # 7. Eclipses: dias até o eclipse solar/lunar mais próximo
    for label, key in (("solar", "solar_eclipses"), ("lunar", "lunar_eclipses")):
        ecl = g[key]
        if len(ecl):
            t = np.sort(ecl[:, 0])
            pos = np.searchsorted(t, jd)
            prev_t = t[np.clip(pos - 1, 0, len(t) - 1)]
            next_t = t[np.clip(pos, 0, len(t) - 1)]
            dist = np.minimum(np.abs(jd - prev_t), np.abs(next_t - jd))
            cols[f"days_to_{label}_eclipse"] = dist
            cols[f"{label}_eclipse_window15"] = (dist <= 15.0).astype(float)

    # 8. Índice legado (score.yaml)
    cols["tension_raw_legacy"] = raw_tension_from_array(lon, BODY_IDS)

    names = list(cols.keys())
    X = np.column_stack([cols[k] for k in names]).astype(np.float32)
    return X, names


# ----------------------------------------------------------------------------- agregação mensal
def month_index(start_year: int, end_year: int) -> np.ndarray:
    """Array [(ano, mês)] contíguo."""
    return np.array([(y, m) for y in range(start_year, end_year + 1) for m in range(1, 13)], dtype=np.int32)


def monthly_features(grid: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Agrega a matriz diária por mês: média de todas as features e máximo das ativações/índices
    de tensão (`*_max`). Retorna {"months": [(y,m)], "X": [n_months, n_feat], "names": [...]}.
    """
    g = grid or load_raw_grid()
    X, names = derive_daily_features(g)
    ymd = g["ymd"]
    key = ymd[:, 0].astype(np.int64) * 12 + (ymd[:, 1].astype(np.int64) - 1)
    uniq, inv = np.unique(key, return_inverse=True)
    n_m = len(uniq)
    sums = np.zeros((n_m, X.shape[1]))
    counts = np.bincount(inv, minlength=n_m).astype(float)
    for c in range(X.shape[1]):
        sums[:, c] = np.bincount(inv, weights=X[:, c], minlength=n_m)
    means = sums / counts[:, None]

    max_cols = [i for i, nm in enumerate(names) if nm.startswith(("hard_", "conj_", "tension_raw", "harm", "asp_")) and not nm.startswith("asp_sun_") and not nm.startswith("asp_mercury_") and not nm.startswith("asp_venus_")]
    maxes = np.full((n_m, len(max_cols)), -np.inf)
    for k, c in enumerate(max_cols):
        np.maximum.at(maxes[:, k], inv, X[:, c])
    months = np.column_stack([uniq // 12, uniq % 12 + 1]).astype(np.int32)
    all_names = names + [names[c] + "_max" for c in max_cols]
    return {"months": months, "X": np.hstack([means, maxes]).astype(np.float32), "names": all_names}


if __name__ == "__main__":
    import time
    t0 = time.time()
    print("Construindo grade diária de features 1750–2150 (geo + equatorial + helio + eclipses)...")
    g = build_raw_grid()
    print(f"Grade: {len(g['jd'])} dias, {len(g['solar_eclipses'])} eclipses solares, {len(g['lunar_eclipses'])} lunares em {time.time()-t0:.0f}s")
    mf = monthly_features(g)
    print(f"Features mensais: {mf['X'].shape}")
