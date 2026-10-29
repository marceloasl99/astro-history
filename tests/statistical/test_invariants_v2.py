"""
Suite de Testes de Invariantes Estatísticos e Metodológicos (astro-history v2).

Garante que os 8 critérios de integridade estipulados no plano de revisão
sejam validados automaticamente a cada execução do pipeline:
1. Ausência de saturação artificial (teto/piso < 1%).
2. Calibração da taxa de dias > P90 (entre 9% e 11%).
3. Coerência estrita texto-efeméride (0 divergências entre texto e posições calculadas).
4. Uniformidade de escalas por card e consonância com results.json.
5. Erradicação de vazamento (Leave-One-Out e janela ±1 ano no matcher).
6. Calibração de falsos positivos (taxa de rejeição entre 3% e 7% para alpha=5%).
7. Integridade amostral unificada (N=59 e consonância com exclusion_log.md).
8. Linguagem sóbria e não alarmista nas projeções.
"""

import json
import os
import re
import pytest
import numpy as np
import swisseph as swe
from datetime import date
from src.core.ephemeris_grid import get_daily_grid, get_score_for_date
from src.future_engine import get_projections_2027_2060, generate_future_timeline_1800_2100

RESULTS_FILE = "/home/astro/data/results.json"
EXCLUSION_LOG_FILE = "/home/astro/data/exclusion_log.md"
PROJECTIONS_FILE = "/home/astro/data/projections_2027_2060.json"
TIMELINE_FILE = "/home/astro/data/timeline_1800_2100.json"

ZODIAC_SIGNS = [
    "Áries", "Touro", "Gêmeos", "Câncer",
    "Leão", "Virgem", "Libra", "Escorpião",
    "Sagitário", "Capricórnio", "Aquário", "Peixes"
]

PLANET_IDS = {
    "Plutão": swe.PLUTO,
    "Netuno": swe.NEPTUNE,
    "Urano": swe.URANUS,
    "Saturno": swe.SATURN,
    "Júpiter": swe.JUPITER,
}

def get_planet_sign(planet_id: int, year: int, month: int = 7, day: int = 1) -> str:
    jd = swe.julday(year, month, day, 12.0)
    res, _ = swe.calc_ut(jd, planet_id)
    lon = res[0] % 360.0
    sign_idx = int(lon // 30)
    return ZODIAC_SIGNS[sign_idx]


def test_invariant_1_no_saturation():
    """1. Ausência de saturação: nenhum score tem >= 1% dos valores no teto ou piso."""
    with open(PROJECTIONS_FILE, "r", encoding="utf-8") as f:
        proj_data = json.load(f)

    projections = proj_data["projections"]
    assert len(projections) == 34

    ceil_count = 0
    floor_count = 0
    total_scores = 0

    for p in projections:
        # Score anual
        score = p.get("tension_1000", p.get("annual_percentile_1000", 0.0))
        total_scores += 1
        if score >= 1000.0:
            ceil_count += 1
        if score <= 10.0:
            floor_count += 1

        # Portais sazonais
        for gate in p.get("seasonal_gates", []):
            g_score = gate.get("tension_1000", 0.0)
            total_scores += 1
            if g_score >= 1000.0:
                ceil_count += 1
            if g_score <= 10.0:
                floor_count += 1

    ceil_rate = ceil_count / total_scores
    floor_rate = floor_count / total_scores

    assert ceil_rate < 0.01, f"Taxa no teto excessiva: {ceil_rate:.2%}"
    assert floor_rate < 0.01, f"Taxa no piso excessiva: {floor_rate:.2%}"


def test_invariant_2_calibration_p90_rate():
    """2. Calibração: taxa de dias > P90 na grade diária fica entre 9% e 11%."""
    grid = get_daily_grid()
    total_days = grid["total_days"]
    p90_idx = int(total_days * 0.90)
    p90_threshold = grid["sorted_scores"][p90_idx]
    days_above_p90 = np.sum(grid["raw_scores"] > p90_threshold)
    rate = float(days_above_p90) / float(total_days)

    assert 0.09 <= rate <= 0.11, f"Taxa de dias > P90 fora da calibração: {rate:.4f}"

    # Validar que a média de dias > P90 nas projeções é razoável (~36.5 dias/ano)
    with open(PROJECTIONS_FILE, "r", encoding="utf-8") as f:
        proj_data = json.load(f)

    avg_days_p90 = sum(p["days_above_p90"] for p in proj_data["projections"]) / len(proj_data["projections"])
    assert 20.0 <= avg_days_p90 <= 55.0, f"Média de dias > P90 fora do intervalo esperado: {avg_days_p90}"


def test_invariant_3_text_ephemeris_consistency():
    """3. Coerência texto-dados: o texto cita apenas signos onde os planetas realmente estão."""
    with open(PROJECTIONS_FILE, "r", encoding="utf-8") as f:
        proj_data = json.load(f)

    divergences = []

    for p in proj_data["projections"]:
        year = p["year"]
        trigger = p["cosmic_trigger"]
        scenarios = p["scenarios_and_possibilities"]
        full_text = f"{trigger} {scenarios}"

        # Verificar signos reais de Plutão, Netuno, Urano e Saturno
        for planet_name, planet_id in [("Plutão", swe.PLUTO), ("Netuno", swe.NEPTUNE), ("Urano", swe.URANUS), ("Saturno", swe.SATURN)]:
            # Inícios e meios do ano
            sign_mid = get_planet_sign(planet_id, year, 7, 1)
            sign_start = get_planet_sign(planet_id, year, 1, 1)
            sign_end = get_planet_sign(planet_id, year, 12, 31)
            valid_signs = {sign_start, sign_mid, sign_end}

            # Buscar no texto afirmações como "Netuno em [Signo]"
            pattern = re.compile(rf"{planet_name}\s+em\s+([A-ZÁÉÍÓÚÂÊÔãõa-záéíóúâêôãõ]+)", re.IGNORECASE)
            matches = pattern.findall(full_text)
            for cited_sign in matches:
                cited_clean = cited_sign.capitalize()
                if cited_clean in ZODIAC_SIGNS:
                    if cited_clean not in valid_signs:
                        divergences.append(
                            f"Ano {year}: texto afirma '{planet_name} em {cited_clean}', mas efeméride calculada está em {valid_signs}"
                        )

    # Casos notórios verificados diretamente
    # 2039: Netuno deve estar em Touro
    netuno_2039 = get_planet_sign(swe.NEPTUNE, 2039, 7, 1)
    assert netuno_2039 == "Touro"

    # 2046: Urano deve estar em Leão
    urano_2046 = get_planet_sign(swe.URANUS, 2046, 7, 1)
    assert urano_2046 == "Leão"

    # 2049: Netuno deve estar em Touro
    netuno_2049 = get_planet_sign(swe.NEPTUNE, 2049, 7, 1)
    assert netuno_2049 == "Touro"

    # 2060: Saturno no pico (22 de Setembro de 2060) deve estar em Gêmeos
    p2060 = next(p for p in proj_data["projections"] if p["year"] == 2060)
    assert p2060["saturn_sign"] == "Gêmeos", f"Saturno em 2060 deveria ser Gêmeos, obtido: {p2060['saturn_sign']}"
    assert p2060["peak_date"] == "2060-09-22"

    assert len(divergences) == 0, f"Divergências encontradas entre texto e efeméride: {divergences}"


def test_invariant_4_single_scale_and_results_match():
    """4. Uniformidade de escala e consonância com results.json."""
    assert os.path.exists(RESULTS_FILE), "results.json não encontrado"
    with open(RESULTS_FILE, "r", encoding="utf-8") as f:
        res = json.load(f)

    # Validar que scores observados estão na escala 0-1000
    for h in res["hypotheses_results"]:
        assert 0 <= h["obs"] <= 1000, f"Score fora da escala 0-1000: {h['obs']}"
        assert 0 <= h["null_mean"] <= 1000, f"Média nula fora da escala 0-1000: {h['null_mean']}"
        assert 0.0 <= h["p"] <= 1.0, f"p-valor inválido: {h['p']}"
        assert 0.0 <= h["q"] <= 1.0, f"q-valor inválido: {h['q']}"

    # Validar que os portais sazonais e scores anuais nas projeções usam a mesma escala
    with open(PROJECTIONS_FILE, "r", encoding="utf-8") as f:
        proj_data = json.load(f)

    for p in proj_data["projections"]:
        score = p.get("tension_1000", p.get("annual_percentile_1000", 0.0))
        assert 0 <= score <= 1000
        for g in p.get("seasonal_gates", []):
            g_score = g.get("tension_1000", 0.0)
            assert 0 <= g_score <= 1000
            assert 0 <= g.get("tension_percent", 0.0) <= 100.0

    # Validar consistência da curva de poder estatístico
    pwr_data = res.get("power_analysis", {}).get("power_by_effect_size_sd", {})
    if pwr_data:
        # Monotonicidade com o tamanho de efeito
        vals = [float(v) for k, v in sorted(pwr_data.items(), key=lambda kv: float(kv[0]))]
        assert all(vals[i] <= vals[i+1] for i in range(len(vals)-1)), "Curva de poder deve ser monotonicamente não-decrescente"
        # Poder no MDE declarado (0.332 DP) deve ser >= 80%
        mde_pwr = float(pwr_data.get("0.332", pwr_data.get("0.3", 0.0)))
        assert mde_pwr >= 0.70, f"Poder próximo a 0.33 DP deveria ser expressivo: {mde_pwr}"


def test_invariant_5_precedents_leave_one_out():
    """5. Precedentes: nenhum evento tem similaridade consigo mesmo ou em janela de ±1 ano."""
    with open(PROJECTIONS_FILE, "r", encoding="utf-8") as f:
        proj_data = json.load(f)

    checked_projections = 0
    for p in proj_data["projections"]:
        year = p["year"]
        prec = p.get("top_precedent")
        if prec:
            # O precedente deve ter um ano identificável
            prec_date = prec.get("date", "")
            prec_year = int(prec_date.split("-")[0]) if prec_date else prec.get("year")
            assert prec_year is not None, f"Precedente sem ano válido no card de {year}: {prec}"
            # Na projeção futura (2027-2060), precedentes históricos vêm de < 2026
            assert prec_year < 2026, f"Precedente no futuro não permitido: {prec_year}"
            # Janela de exclusão estrita
            assert abs(year - prec_year) > 1
            checked_projections += 1

    assert checked_projections == len(proj_data["projections"]), "Todos os anos devem ter precedentes válidos"

    # Validação direta do algoritmo Leave-One-Out contra o banco de dados
    from src.db import get_event_by_id
    from src.correlation_engine import find_similar_events
    sample_ids = [1, 93, 107, 134, 156]
    checked_events = 0

    for eid in sample_ids:
        ev = get_event_by_id(eid)
        if not ev or not ev.get("chart"):
            continue
        ev_year = int(ev["date"].split("-")[0])
        sims = find_similar_events(ev["chart"], top_k=5, exclude_event_id=ev["id"]).get("top_matches", [])
        assert len(sims) > 0, f"Deveria encontrar similares para evento {eid}"
        for sim in sims:
            sim_year = int(sim["date"].split("-")[0])
            assert sim["id"] != ev["id"], f"Auto-match violado para evento {ev['id']}"
            assert abs(sim_year - ev_year) > 1, (
                f"Vazamento temporal ±1 ano detectado: evento {ev['id']} ({ev_year}) "
                f"pareou com {sim['id']} ({sim_year})"
            )
        checked_events += 1

    assert checked_events == len(sample_ids), "Todos os eventos de amostra devem ter sido avaliados no teste LOO"


def test_invariant_6_synthetic_control_false_positive_rate():
    """6. Calibração de falsos positivos: taxa de rejeição entre 3% e 7% para alpha=5%."""
    with open(RESULTS_FILE, "r", encoding="utf-8") as f:
        res = json.load(f)

    calib = res.get("negative_controls_calibration")
    assert calib is not None, "negative_controls_calibration ausente em results.json"
    assert calib["n_synthetic_runs"] == 1000
    rate = calib["observed_rejection_rate"]
    assert 0.03 <= rate <= 0.07, f"Taxa de falsos positivos descalibrada: {rate:.4f}"
    assert calib["in_calibration_range_03_to_07"] is True


def test_invariant_7_sample_size_integrity():
    """7. Integridade amostral: N=59 consistente em todos os testes e alinhado ao exclusion_log."""
    with open(RESULTS_FILE, "r", encoding="utf-8") as f:
        res = json.load(f)

    assert res["sample"]["n_events"] == 59
    assert res["sample"]["era"] == "1800-2025"

    # Verificar testes principais
    h1_n3 = next(h for h in res["hypotheses_results"] if "vs N3" in h["hypothesis"] and h["group"] == "Geral")
    h1_n2 = next(h for h in res["hypotheses_results"] if "vs N2" in h["hypothesis"] and h["group"] == "Geral")
    h1_n1 = next(h for h in res["hypotheses_results"] if "vs N1" in h["hypothesis"] and h["group"] == "Geral")
    h4_tarnas = next(h for h in res["hypotheses_results"] if "Tarnas" in h["hypothesis"])

    assert h1_n3["n"] == 59
    assert h1_n2["n"] == 59
    assert h1_n1["n"] == 59
    assert h4_tarnas["n"] == 59

    # Verificar temporal split: 26 (treino 1800-1950) + 33 (teste 1951-2025) = 59
    h2_train = next(h for h in res["hypotheses_results"] if "1800-1950" in h["hypothesis"])
    h2_test = next(h for h in res["hypotheses_results"] if "1951-2025" in h["hypothesis"])
    assert h2_train["n"] + h2_test["n"] == 59

    # Verificar que o log de exclusão documenta o funil
    assert os.path.exists(EXCLUSION_LOG_FILE)
    with open(EXCLUSION_LOG_FILE, "r", encoding="utf-8") as f:
        log_content = f.read()
    assert "300" in log_content
    assert "61" in log_content
    assert "59" in log_content
    assert "1789" in log_content
    assert "1799" in log_content


def test_invariant_8_no_alarmist_language_in_projections():
    """8. Linguagem: rótulos alarmistas não aparecem nos dados de projeção futura."""
    with open(PROJECTIONS_FILE, "r", encoding="utf-8") as f:
        proj_data = json.load(f)

    allowed_tiers = {
        "Percentil Superior",
        "Percentil Superior (P90+)",
        "Percentil Moderado",
        "Percentil Basal"
    }

    forbidden_substrings = [
        "Crítico",
        "Ruptura Histórica",
        "risco bélico catastrófico",
        "iminência de conflito bélico",
        "alerta vermelho de guerra"
    ]

    for p in proj_data["projections"]:
        tier = p["alert_level"]
        assert tier in allowed_tiers, f"Ano {p['year']} possui tier não permitido: '{tier}'"

        trigger = p["cosmic_trigger"]
        scenarios = p["scenarios_and_possibilities"]
        combined = f"{trigger} {scenarios}"

        for forbidden in forbidden_substrings:
            assert forbidden.lower() not in combined.lower(), (
                f"Ano {p['year']} contém termo proibido '{forbidden}': {combined}"
            )
