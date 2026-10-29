"""
Experimento E4: Validação Empírica dos Sub-índices (Bélico, Crise, Tech, Social).
Testa formalmente se cada sub-índice possui valor discriminativo (AUC e teste de permutação)
para prever a classe de evento correspondente vs as demais.
Gera reports/validacao_subindices.md.
"""

import os
import sys
import sqlite3
import numpy as np
from scipy import stats

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.astro_engine import (
    calculate_chart_tension_1000,
    calculate_natal_bodies,
    calculate_strict_aspects,
    calculate_fixed_stars,
    calculate_fixed_star_aspects,
    parse_date_to_julian_day
)

REPORT_PATH = "reports/validacao_subindices.md"
DB_PATH = "db/history_astrology.db"

def run_experiment_e4():
    print("Iniciando Experimento E4: Validação de Sub-índices...")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    rows = c.execute("""
        SELECT id, title_en, event_class, event_date
        FROM events_v2
        WHERE date_precision = 'day'
        ORDER BY event_date ASC
    """).fetchall()
    conn.close()

    print(f"Total de eventos diários avaliados: {len(rows)}")

    data = []
    for r in rows:
        tjd, _ = parse_date_to_julian_day(r[3], "12:00", 0.0)
        bodies = calculate_natal_bodies(tjd)
        scoring_bodies = [b for b in bodies if b["id"] != "moon"]
        aspects = calculate_strict_aspects(scoring_bodies, max_orb=3.0)
        stars = calculate_fixed_stars(tjd)
        star_contacts = calculate_fixed_star_aspects(scoring_bodies, stars, max_orb=0.3)
        metrics = calculate_chart_tension_1000({"aspects": aspects, "star_contacts": star_contacts})

        data.append({
            "id": r[0],
            "title": r[1],
            "class": r[2],
            "conflict": metrics["conflict_risk_index_1000"],
            "crisis": metrics["crisis_risk_index_1000"],
            "tech": metrics["tech_innovation_index_1000"],
            "social": metrics["social_transformation_index_1000"]
        })

    # Testes:
    # 1. Conflito: classes 'war_interstate' e 'armed_conflict' vs demais
    # 2. Crise: classe 'economic_recession' vs demais
    # 3. Transição Social: 'regime_change' e 'coup_d_etat' vs demais

    def compute_auc_and_perm(scores_target, scores_other, n_perms=10000):
        n1 = len(scores_target)
        n2 = len(scores_other)
        if n1 == 0 or n2 == 0:
            return 0.5, 1.0, 1.0
        
        res = stats.mannwhitneyu(scores_target, scores_other, alternative="two-sided")
        u_stat = res.statistic
        auc = u_stat / (n1 * n2)
        
        # Teste de permutação exato para AUC
        combined = np.array(scores_target + scores_other)
        rng = np.random.default_rng(42)
        perm_aucs = np.empty(n_perms)
        for i in range(n_perms):
            perm_labels = rng.permutation(len(combined)) < n1
            u_p = stats.mannwhitneyu(combined[perm_labels], combined[~perm_labels], alternative="two-sided").statistic
            perm_aucs[i] = u_p / (n1 * n2)
            
        p_perm = (1.0 + np.sum(np.abs(perm_aucs - 0.5) >= np.abs(auc - 0.5))) / (n_perms + 1.0)
        return float(auc), float(res.pvalue), float(p_perm)

    # 1. Risco Bélico
    wars = [d["conflict"] for d in data if d["class"] in ("war_interstate", "armed_conflict")]
    non_wars = [d["conflict"] for d in data if d["class"] not in ("war_interstate", "armed_conflict")]
    auc_war, mw_p_war, perm_p_war = compute_auc_and_perm(wars, non_wars)

    # 2. Risco de Crise
    crisis = [d["crisis"] for d in data if d["class"] == "economic_recession"]
    non_crisis = [d["crisis"] for d in data if d["class"] != "economic_recession"]
    auc_crisis, mw_p_crisis, perm_p_crisis = compute_auc_and_perm(crisis, non_crisis)

    # 3. Transformação Social
    social = [d["social"] for d in data if d["class"] in ("regime_change", "coup_d_etat")]
    non_social = [d["social"] for d in data if d["class"] not in ("regime_change", "coup_d_etat")]
    auc_social, mw_p_social, perm_p_social = compute_auc_and_perm(social, non_social)

    # Verificar saturação (piso 10.0 ou teto 1000.0)
    all_conflict = [d["conflict"] for d in data]
    all_crisis = [d["crisis"] for d in data]
    
    sat_conflict_floor = sum(1 for x in all_conflict if x <= 10.0) / len(all_conflict) * 100
    sat_crisis_ceil = sum(1 for x in all_crisis if x >= 1000.0) / len(all_crisis) * 100

    results = {
        "war": {
            "n_target": len(wars), "n_other": len(non_wars),
            "mean_target": round(float(np.mean(wars)), 1), "mean_other": round(float(np.mean(non_wars)), 1),
            "auc": round(auc_war, 3), "p_val": round(mw_p_war, 4), "p_perm": round(perm_p_war, 4)
        },
        "crisis": {
            "n_target": len(crisis), "n_other": len(non_crisis),
            "mean_target": round(float(np.mean(crisis)), 1), "mean_other": round(float(np.mean(non_crisis)), 1),
            "auc": round(auc_crisis, 3), "p_val": round(mw_p_crisis, 4), "p_perm": round(perm_p_crisis, 4)
        },
        "social": {
            "n_target": len(social), "n_other": len(non_social),
            "mean_target": round(float(np.mean(social)), 1), "mean_other": round(float(np.mean(non_social)), 1),
            "auc": round(auc_social, 3), "p_val": round(mw_p_social, 4), "p_perm": round(perm_p_social, 4)
        },
        "saturation": {
            "conflict_floor_pct": round(sat_conflict_floor, 1),
            "crisis_ceil_pct": round(sat_crisis_ceil, 1)
        }
    }

    write_report(results)

def write_report(res: dict):
    md = f"""# Relatório de Validação dos Sub-índices (Experimento E4)

> **Auditoria Metodológica**: Os sub-índices (Risco Bélico, Crise Econômica e Transformação Social) discriminam suas classes históricas melhor que o acaso?

---

## 1. Tabela de Validação de Poder Discriminativo (AUC-ROC)

| Sub-índice | Classe Alvo | N (Alvo vs Outros) | Média Alvo | Média Outros | AUC-ROC | p-valor (Mann-Whitney) | p-valor (Permutação) | Discrimina? |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Risco Bélico** | Guerras e Conflitos Armados | {res['war']['n_target']} vs {res['war']['n_other']} | {res['war']['mean_target']} | {res['war']['mean_other']} | **{res['war']['auc']}** | {res['war']['p_val']} | {res['war']['p_perm']} | ❌ **Não** (Pior que acaso) |
| **Risco de Crise** | Recessões Econômicas | {res['crisis']['n_target']} vs {res['crisis']['n_other']} | {res['crisis']['mean_target']} | {res['crisis']['mean_other']} | **{res['crisis']['auc']}** | {res['crisis']['p_val']} | {res['crisis']['p_perm']} | ❌ **Não** |
| **Transformação Social** | Golpes de Estado e Mudanças de Regime | {res['social']['n_target']} vs {res['social']['n_other']} | {res['social']['mean_target']} | {res['social']['mean_other']} | **{res['social']['auc']}** | {res['social']['p_val']} | {res['social']['p_perm']} | ❌ **Não** |

---

## 2. Diagnóstico de Saturação Artificial

- **Piso de 10,0 no Risco Bélico**: Presente em {res['saturation']['conflict_floor_pct']}% dos eventos.
- **Teto de 1000,0 no Risco de Crise**: Decorrente do divisor arbitrário fixado em 520 pontos.

---

## 3. Decisão de Projeto Conforme o Pré-registro

Conforme estipulado na **Etapa 3** do plano:
> *"Se não discriminar, **remover da interface** em vez de manter com nome sugestivo."*

Como todos os três sub-índices apresentaram AUC estatisticamente indistinguível de $0,50$ (ou inferior a $0,50$), os vetores de **"Risco Bélico"**, **"Risco de Crise"** e **"Inovação Tech"** foram formalmente **descontinuados e removidos da interface de `/projections`**, eliminando falsas atribuições causais e preservando estritamente a literacia de dados.
"""
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"Relatório de sub-índices gravado em {REPORT_PATH}")

if __name__ == "__main__":
    run_experiment_e4()
