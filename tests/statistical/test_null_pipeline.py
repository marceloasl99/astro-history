from datetime import date, timedelta
import numpy as np
import pytest
from src.analysis.null_models import circular_shift_test
from src.analysis.multiplicity import benjamini_hochberg

def test_null_pipeline_does_not_find_signal_in_synthetic_noise():
    """
    Testa que a pipeline estatística não detecta 'sinal' em dados sintéticos de ruído puro.
    Garante que a metodologia não é auto-enganosa.
    """
    rng = np.random.default_rng(12345)
    start_d = date(1800, 1, 1)
    span = (date(2025, 12, 31) - start_d).days

    # Gerar 40 datas puramente aleatórias
    synth_days = rng.integers(0, span, size=40)
    synth_dates = [start_d + timedelta(days=int(k)) for k in synth_days]

    # Função de pontuação constante/ruído
    def noise_score_fn(d):
        return float(500.0 + (hash(str(d)) % 100))

    res = circular_shift_test(synth_dates, noise_score_fn, n_perm=1000, seed=42)

    # O z-score em dados de ruído não deve ser significante (|z| < 2.5)
    assert abs(res["z"]) < 2.5, f"Alarme falso: ruído gerou z-score extremo {res['z']}"
    assert res["p"] > 0.01, f"Alarme falso: ruído gerou p-valor muito baixo {res['p']}"

def test_benjamini_hochberg_multiplicity():
    """
    Valida as propriedades formais do procedimento de Benjamini-Hochberg.
    """
    # Lista com 5 p-valores onde nenhum passa no limiar
    noise_pvals = [0.45, 0.72, 0.18, 0.89, 0.33]
    rejects, qvals = benjamini_hochberg(noise_pvals, q=0.05)
    assert not any(rejects), "Nenhum p-valor do ruído deveria ser rejeitado!"

    # Lista com um p-valor extremamente forte
    strong_pvals = [0.0001, 0.40, 0.80]
    rejects_strong, qvals_strong = benjamini_hochberg(strong_pvals, q=0.05)
    assert rejects_strong[0] == True, "O p-valor de 0.0001 deve ser rejeitado!"
