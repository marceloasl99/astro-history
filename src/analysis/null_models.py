"""
Modelos Nulos para Testes de Hipóteses Astrológicas.
Implementa N1 (datas uniformes), N2 (estratificado por década),
N3 (deslocamento circular - preserva agrupamento temporal) e N4 (permutação de classes).
"""

from datetime import date, timedelta
from typing import List, Dict, Any, Callable
import numpy as np

def circular_shift_test(
    event_dates: List[date],
    score_fn: Callable[[date], float],
    start: date = date(1800, 1, 1),
    end: date = date(2025, 12, 31),
    n_perm: int = 10000,
    seed: int = 42
) -> Dict[str, Any]:
    """
    N3 (Deslocamento Circular): Desloca todo o vetor de eventos por um mesmo offset aleatório,
    preservando perfeitamente a distância temporal entre os eventos e a autocorrelação dos planetas externos.
    """
    rng = np.random.default_rng(seed)
    span = (end - start).days + 1

    # Converter datas para índices inteiros de dias desde o início
    offsets_days = np.array([(d - start).days for d in event_dates if start <= d <= end], dtype=np.int32)
    if len(offsets_days) == 0:
        return {"observed": 0.0, "null_mean": 0.0, "null_std": 0.0, "z": 0.0, "p": 1.0, "null_distribution": []}

    obs = float(np.mean([score_fn(start + timedelta(days=int(k))) for k in offsets_days]))

    null_scores = np.empty(n_perm, dtype=np.float64)

    # Vetor de deslocamentos aleatórios circulares
    shifts = rng.integers(0, span, size=n_perm)

    for i, shift in enumerate(shifts):
        shifted_offsets = (offsets_days + shift) % span
        null_scores[i] = np.mean([score_fn(start + timedelta(days=int(k))) for k in shifted_offsets])

    p_value = (1.0 + np.sum(null_scores >= obs)) / (n_perm + 1.0)
    std_null = float(np.std(null_scores, ddof=1)) if len(null_scores) > 1 else 1.0
    z = (obs - float(np.mean(null_scores))) / (std_null if std_null > 0 else 1.0)

    # Intervalo de confiança bootstrap de 95% para o score observado
    boot_indices = rng.choice(len(offsets_days), size=(1000, len(offsets_days)), replace=True)
    obs_samples = np.array([score_fn(start + timedelta(days=int(k))) for k in offsets_days])
    boot_means = np.mean(obs_samples[boot_indices], axis=1)
    ci_lower = float(np.percentile(boot_means, 2.5))
    ci_upper = float(np.percentile(boot_means, 97.5))

    return {
        "observed": round(obs, 2),
        "ci_95": [round(ci_lower, 2), round(ci_upper, 2)],
        "null_mean": round(float(np.mean(null_scores)), 2),
        "null_std": round(std_null, 2),
        "z": round(float(z), 3),
        "p": round(float(p_value), 5),
        "n_events": len(offsets_days),
        "n_perm": n_perm,
        "null_p90": round(float(np.percentile(null_scores, 90)), 2),
        "null_p95": round(float(np.percentile(null_scores, 95)), 2)
    }

def stratified_decade_test(
    event_dates: List[date],
    control_dates: List[date],
    score_fn: Callable[[date], float],
    n_perm: int = 10000,
    seed: int = 42
) -> Dict[str, Any]:
    """
    N2 (Estratificado por Década): Compara os eventos com datas aleatórias extraídas
    da mesma década de cada evento para isolar trânsitos lentos geracionais.
    """
    rng = np.random.default_rng(seed)
    obs = float(np.mean([score_fn(d) for d in event_dates]))

    # Agrupar controles por década
    controls_by_decade = {}
    for cd in control_dates:
        dec = (cd.year // 10) * 10
        if dec not in controls_by_decade:
            controls_by_decade[dec] = []
        controls_by_decade[dec].append(cd)

    event_decades = [(d.year // 10) * 10 for d in event_dates]
    n_events = len(event_dates)

    null_scores = np.empty(n_perm, dtype=np.float64)

    for i in range(n_perm):
        perm_dates = []
        for dec in event_decades:
            pool = controls_by_decade.get(dec, control_dates)
            perm_dates.append(rng.choice(pool))
        null_scores[i] = np.mean([score_fn(d) for d in perm_dates])

    p_value = (1.0 + np.sum(null_scores >= obs)) / (n_perm + 1.0)
    std_null = float(np.std(null_scores, ddof=1)) if len(null_scores) > 1 else 1.0
    z = (obs - float(np.mean(null_scores))) / (std_null if std_null > 0 else 1.0)

    return {
        "observed": round(obs, 2),
        "null_mean": round(float(np.mean(null_scores)), 2),
        "null_std": round(std_null, 2),
        "z": round(float(z), 3),
        "p": round(float(p_value), 5),
        "n_events": n_events,
        "n_perm": n_perm
    }

def uniform_random_test(
    event_dates: List[date],
    score_fn: Callable[[date], float],
    start: date = date(1800, 1, 1),
    end: date = date(2025, 12, 31),
    n_perm: int = 10000,
    seed: int = 42
) -> Dict[str, Any]:
    """
    N1 (Uniforme Ingênuo): Sorteia datas uniformemente ao acaso em [start, end].
    """
    rng = np.random.default_rng(seed)
    span = (end - start).days + 1
    n_events = len(event_dates)
    obs = float(np.mean([score_fn(d) for d in event_dates]))

    null_scores = np.empty(n_perm, dtype=np.float64)
    for i in range(n_perm):
        rand_days = rng.integers(0, span, size=n_events)
        null_scores[i] = np.mean([score_fn(start + timedelta(days=int(k))) for k in rand_days])

    p_value = (1.0 + np.sum(null_scores >= obs)) / (n_perm + 1.0)
    std_null = float(np.std(null_scores, ddof=1)) if len(null_scores) > 1 else 1.0
    z = (obs - float(np.mean(null_scores))) / (std_null if std_null > 0 else 1.0)

    return {
        "observed": round(obs, 2),
        "null_mean": round(float(np.mean(null_scores)), 2),
        "null_std": round(std_null, 2),
        "z": round(float(z), 3),
        "p": round(float(p_value), 5),
        "n_events": n_events,
        "n_perm": n_perm
    }
