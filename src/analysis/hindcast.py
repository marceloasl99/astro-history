"""
Hindcast walk-forward (v3): mede a precisão REAL de cada método de previsão.

Para cada alvo mensal e cada ano de teste t (1951–fim da cobertura), o modelo é
ajustado apenas com meses de anos <= t-1 (com intervalo de segurança) e prevê os
12 meses de t. As previsões acumuladas são avaliadas com regras de pontuação próprias:
Brier, Brier Skill Score (contra a climatologia expansiva), log-loss e AUC,
com IC por bootstrap em blocos anuais.

Modelos comparados:
- climatology      : taxa-base expansiva (baseline obrigatório)
- ar_baseline      : taxa do alvo nos 12/36 meses anteriores (agrupamento temporal)
- legacy_index     : índice de tensão legado (config/score.yaml), calibrado por logística
- barbault         : Índice Cíclico de Barbault
- tarnas_outer     : ativação de aspectos duros/conjunções entre planetas externos
- outer_phases     : fases sinódicas (sin/cos) dos 10 pares externos (sem orbe)
- astro_full       : todas as 409 features astrológicas (logística L2)
- ar_plus_astro    : AR + astro_full
"""

import json
import os
import sys
import time
from typing import Dict, Any, List, Optional

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score, log_loss

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from src.features.astro_features import monthly_features
from src.features.targets import monthly_targets

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
REPORT_JSON = os.path.join(ROOT, "reports", "hindcast_v3.json")
REPORT_MD = os.path.join(ROOT, "reports", "hindcast_v3.md")

DEFAULT_TARGETS = [
    "v2_any", "cow_war_onset", "cow_war_ongoing", "nber_recession", "nber_recession_start",
    "ucdp_onset_any", "ucdp_onset_interstate",
]
GAP_MONTHS = 12
EPS = 1e-4


def _cols(names: List[str], predicate) -> List[int]:
    return [i for i, n in enumerate(names) if predicate(n)]


def feature_sets(names: List[str]) -> Dict[str, List[int]]:
    return {
        "legacy_index": _cols(names, lambda n: n.startswith("tension_raw_legacy")),
        "barbault": _cols(names, lambda n: n.startswith("barbault_index")),
        "tarnas_outer": _cols(names, lambda n: n in ("hard_outer_total", "conj_outer_total", "hard_outer_total_max", "conj_outer_total_max")),
        "outer_phases": _cols(names, lambda n: n.startswith("phase_")),
        "astro_full": list(range(len(names))),
    }


def ar_features(y: np.ndarray) -> np.ndarray:
    """Taxa do alvo nos 12 e 36 meses anteriores (apenas passado estrito) + valor do mês anterior."""
    n = len(y)
    out = np.zeros((n, 3))
    cs = np.concatenate([[0.0], np.cumsum(y)])
    for w, c in ((12, 0), (36, 1)):
        lo = np.maximum(0, np.arange(n) - w)
        out[:, c] = (cs[np.arange(n)] - cs[lo]) / np.maximum(1, np.arange(n) - lo)
    out[1:, 2] = y[:-1]
    return out


C_GRID = (0.0005, 0.002, 0.01, 0.05)


def _fit_predict(Xtr, ytr, Xte, C: float = None) -> np.ndarray:
    """
    Logística L2 padronizada. Se C é None, escolhe C em C_GRID por validação temporal interna
    (últimos 20% dos meses de treino), evitando sobreajuste com centenas de features.
    """
    if ytr.sum() == 0 or ytr.sum() == len(ytr):
        return np.full(len(Xte), float(np.clip(ytr.mean(), EPS, 1 - EPS)))
    if C is None:
        cut = int(len(ytr) * 0.8)
        yv = ytr[cut:]
        if 0 < yv.sum() < len(yv) and ytr[:cut].sum() > 0:
            best, best_ll = C_GRID[0], np.inf
            for c in C_GRID:
                pv = _fit_predict(Xtr[:cut], ytr[:cut], Xtr[cut:], c)
                ll = log_loss(yv, pv, labels=[0, 1])
                if ll < best_ll:
                    best, best_ll = c, ll
            C = best
        else:
            C = C_GRID[0]
    sc = StandardScaler().fit(Xtr)
    clf = LogisticRegression(C=C, max_iter=2000, class_weight=None)
    clf.fit(sc.transform(Xtr), ytr)
    return np.clip(clf.predict_proba(sc.transform(Xte))[:, 1], EPS, 1 - EPS)


def brier(p, y):
    return float(np.mean((p - y) ** 2))


def reliability(p, y, bins=8):
    edges = np.quantile(p, np.linspace(0, 1, bins + 1))
    rows = []
    for k in range(bins):
        m = (p >= edges[k]) & (p <= edges[k + 1]) if k == bins - 1 else (p >= edges[k]) & (p < edges[k + 1])
        if m.sum() > 0:
            rows.append({"p_mean": round(float(p[m].mean()), 4), "obs_rate": round(float(y[m].mean()), 4), "n": int(m.sum())})
    return rows


def evaluate(p: np.ndarray, y: np.ndarray, p_clim: np.ndarray, years: np.ndarray, rng: np.random.Generator, n_boot: int = 500) -> Dict[str, Any]:
    b = brier(p, y)
    bc = brier(p_clim, y)
    bss = 1.0 - b / bc if bc > 0 else 0.0
    uniq_years = np.unique(years)
    boots = []
    for _ in range(n_boot):
        ys = rng.choice(uniq_years, size=len(uniq_years), replace=True)
        idx = np.concatenate([np.where(years == yy)[0] for yy in ys])
        bb, bcc = brier(p[idx], y[idx]), brier(p_clim[idx], y[idx])
        boots.append(1.0 - bb / bcc if bcc > 0 else 0.0)
    lo, hi = np.percentile(boots, [2.5, 97.5])
    auc = float(roc_auc_score(y, p)) if 0 < y.sum() < len(y) else None
    return {
        "n_months": int(len(y)), "positives": int(y.sum()),
        "brier": round(b, 5), "brier_climatology": round(bc, 5),
        "bss": round(bss, 4), "bss_ci95": [round(float(lo), 4), round(float(hi), 4)],
        "bss_p_gt0": round(float(np.mean(np.array(boots) > 0)), 3),
        "logloss": round(float(log_loss(y, p, labels=[0, 1])), 5),
        "auc": round(auc, 4) if auc is not None else None,
        "reliability": reliability(p, y),
    }


def run_hindcast(target_names: Optional[List[str]] = None, test_start: int = 1951, C_full: float = 0.02, C_small: float = 1.0, seed: int = 42, verbose: bool = True) -> Dict[str, Any]:
    rng = np.random.default_rng(seed)
    mf = monthly_features()
    T = monthly_targets()
    names = mf["names"]
    fsets = feature_sets(names)

    # alinhar meses de features e alvos
    fkey = mf["months"][:, 0].astype(np.int64) * 12 + mf["months"][:, 1] - 1
    tkey = T.keys
    common = np.intersect1d(fkey, tkey)
    fi = np.searchsorted(fkey, common)
    ti = np.searchsorted(tkey, common)
    X_all = mf["X"][fi].astype(np.float64)
    years_all = (common // 12).astype(int)

    results: Dict[str, Any] = {"test_start": test_start, "gap_months": GAP_MONTHS, "C_full": C_full, "targets": {}}
    for tname in (target_names or DEFAULT_TARGETS):
        if tname not in T.targets:
            continue
        y_full = (T.targets[tname][ti] > 0).astype(float)
        cov = T.mask(tname)[ti]
        y0, y1 = T.coverage[tname]
        test_years = [yy for yy in range(max(test_start, y0 + 30), y1 + 1)]
        if len(test_years) < 10:
            continue
        AR = ar_features(np.where(cov, y_full, 0.0))
        preds: Dict[str, List[np.ndarray]] = {k: [] for k in ["climatology", "ar_baseline", *fsets.keys(), "ar_plus_astro"]}
        ys, yrs = [], []
        t0 = time.time()
        for yy in test_years:
            te = cov & (years_all == yy)
            tr = cov & (years_all <= yy - 1) & (common < common[te].min() - GAP_MONTHS)
            if te.sum() == 0 or tr.sum() < 120:
                continue
            ytr, yte = y_full[tr], y_full[te]
            ys.append(yte)
            yrs.append(years_all[te])
            preds["climatology"].append(np.full(te.sum(), float(np.clip(ytr.mean(), EPS, 1 - EPS))))
            preds["ar_baseline"].append(_fit_predict(AR[tr], ytr, AR[te], C_small))
            for fs, cols in fsets.items():
                C = None if fs in ("astro_full", "outer_phases") else C_small
                preds[fs].append(_fit_predict(X_all[tr][:, cols], ytr, X_all[te][:, cols], C))
            Xc_tr = np.hstack([AR[tr], X_all[tr]])
            Xc_te = np.hstack([AR[te], X_all[te]])
            preds["ar_plus_astro"].append(_fit_predict(Xc_tr, ytr, Xc_te, None))
        y = np.concatenate(ys)
        years = np.concatenate(yrs)
        p_clim = np.concatenate(preds["climatology"])
        tres = {"description": T.description[tname], "coverage": [y0, y1], "test_years": [test_years[0], test_years[-1]], "base_rate_test": round(float(y.mean()), 4), "models": {}}
        for k, lst in preds.items():
            tres["models"][k] = evaluate(np.concatenate(lst), y, p_clim, years, rng)
        results["targets"][tname] = tres
        if verbose:
            print(f"[{tname}] {len(test_years)} anos de teste em {time.time()-t0:.0f}s | taxa-base={y.mean():.3f} | "
                  + " ".join(f"{k}={v['bss']:+.3f}" for k, v in tres['models'].items()))
    return results


def write_reports(results: Dict[str, Any]):
    os.makedirs(os.path.dirname(REPORT_JSON), exist_ok=True)
    with open(REPORT_JSON, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    lines = ["# Hindcast v3 — Skill de previsão (walk-forward)", "",
             f"Teste a partir de {results['test_start']}; treino apenas com anos anteriores (gap de {results['gap_months']} meses). "
             "BSS = Brier Skill Score contra a climatologia expansiva (>0 = melhor que a taxa-base; IC 95% por bootstrap em blocos anuais).", ""]
    for tname, t in results["targets"].items():
        lines += [f"## {tname}", "", f"{t['description']}  ", f"Cobertura {t['coverage'][0]}–{t['coverage'][1]}; anos de teste {t['test_years'][0]}–{t['test_years'][1]}; taxa-base no teste {t['base_rate_test']}.", "",
                  "| Modelo | n | Brier | BSS | IC 95% BSS | P(BSS>0) | AUC | log-loss |", "|---|---:|---:|---:|---|---:|---:|---:|"]
        for k, m in t["models"].items():
            lines.append(f"| {k} | {m['n_months']} | {m['brier']:.4f} | {m['bss']:+.3f} | [{m['bss_ci95'][0]:+.3f}, {m['bss_ci95'][1]:+.3f}] | {m['bss_p_gt0']:.2f} | {m['auc'] if m['auc'] is not None else '—'} | {m['logloss']:.4f} |")
        lines.append("")
    with open(REPORT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    res = run_hindcast()
    write_reports(res)
    print(f"Relatórios: {REPORT_JSON} e {REPORT_MD}")
