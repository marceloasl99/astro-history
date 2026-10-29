"""
Controle de Taxa de Falsas Descobertas (FDR - False Discovery Rate).
Implementa o procedimento de Benjamini & Hochberg (1995) para correção
de múltiplos testes de hipóteses estatísticas.
"""

from typing import List, Tuple
import numpy as np

def benjamini_hochberg(pvals: List[float], q: float = 0.05) -> Tuple[np.ndarray, np.ndarray]:
    """
    Aplica a correção de Benjamini-Hochberg aos p-valores informados.
    
    Retorna:
        reject: array booleano indicando se a hipótese nula foi rejeitada (significante).
        adjusted_pvals: array com os q-valores (p-valores ajustados).
    """
    p = np.asarray(pvals, dtype=float)
    m = len(p)
    if m == 0:
        return np.array([], dtype=bool), np.array([], dtype=float)

    order = np.argsort(p)
    ranked = p[order]

    # q * (i / m)
    thresholds = q * (np.arange(1, m + 1) / m)
    passed = ranked <= thresholds

    k = int(np.max(np.where(passed)[0])) + 1 if passed.any() else 0

    reject = np.zeros(m, dtype=bool)
    reject[order[:k]] = True

    # Calcular q-valores ajustados monotonicamente decrescentes
    adjusted = np.empty(m, dtype=float)
    running_min = 1.0
    for i in range(m - 1, -1, -1):
        adj = ranked[i] * (m / (i + 1))
        running_min = min(running_min, adj)
        adjusted[i] = min(1.0, running_min)

    orig_adjusted = np.empty(m, dtype=float)
    orig_adjusted[order] = adjusted

    return reject, orig_adjusted
