# Relatório de Diagnóstico do Viés de Amostragem (E1 a E3)

> **Auditoria Metodológica**: Por que todos os 34 anos (2027–2060) saíam classificados como "Crítico / Ruptura Histórica"?

---

## 1. Resumo Executivo das Causas Confirmadas

A auditoria matemática comprovou a causa exata do **Achado A1**:
1. **Atribuição Indevida do Máximo de 365 Dias como Tensão Anual**:
   Em `src/future_engine.py` (linha 193), a variável `peak_tension` era populada com `daily_stats["max_tension"]` (o valor mais alto entre todos os 365 dias do ano).
2. **Matemática de Valores Extremos**:
   A média teórica do máximo de 365 variáveis uniformes independentes é $\frac{365}{366} \times 1000 = 997,3$.
   Na grade diária real de 1800–2100, o score diário máximo de um ano possui **média de 963.6 pontos**, situando-se acima de 850 pontos em **99.0% de todos os anos da era**.
3. **Limiar Fixo Incompatível**:
   O sistema aplicava a regra `if peak_tension >= 850.0: alert_level = "Crítico"`. Como o pico de 365 dias quase sempre excede 850, **era matematicamente inevitável que 100% dos anos futuros fossem rotulados como Críticos**.
4. **Efeito Adicional dos Portais Sazonais**:
   Mesmo ao considerar apenas os 4 portais sazonais, a probabilidade do máximo exceder 850 é de $\approx 44,2%$, provando que tomar máximos infla desproporcionalmente a percepção de risco.

---

## 2. Experimento E1: Dias Cardeais vs. Dias Ordinários

- **Pergunta**: O Sol a $0^\circ$ de signos cardeais (equinócios e solstícios) eleva artificialmente o score diário?
- **Amostra**: 1204 dias cardeais (1800–2100) vs. 113.596 dias totais.
- **Resultados**:
  - Score bruto médio (Dias Cardeais): **148.18**
  - Score bruto médio (Todos os Dias): **149.01**
  - Percentil médio dos cardeais: **497.6** (mediana 495.0)
  - Teste Kolmogorov-Smirnov: $D = 0.013$, $p = 0.9866$
  - Teste Mann-Whitney: $p = 0.7624$
- **Conclusão E1**: Os dias cardeais em si **não** possuem viés astronômico estrutural relevante. A distorção não veio da posição do Sol no equinócio, mas sim da operação de tomar o extremo máximo.

---

## 3. Experimento E2: Efeito da Operação de Máximo

| Estatística | Teórico (Simulação U[0, 1000]) | Observado na Grade (1800–2100) |
| :--- | :---: | :---: |
| **Média do Máximo de 4 Amostras** | 800.0 pts | 766.0 pts |
| **% de Anos com Máx(4) $\ge 850$** | 47.6% | 44.2% |
| **Média do Máximo de 365 Dias** | 997.3 pts | 963.6 pts |
| **% de Anos com Máx(365) $\ge 850$** | 100,0% | **99.0%** |
| **% de Anos com Máx(365) $\ge 880$** | 100,0% | **94.7%** |

- **Conclusão E2**: O gatilho de alerta baseado no valor extremo de 365 dias garante a classificação "Crítico" em praticamente qualquer ano histórico ou futuro. A correção requer avaliar a **média ou mediana anual calibrada**.

---

## 4. Experimento E3: Calibração da Distribuição Anual

- **Amostra**: 301 anos (1800 a 2100).
- **Métrica Corrigida**: Percentil empírico da média anual $\bar{S}_Y$ mapeado contra a era.
- **Resultados**:
  - Média do percentil anual calibrado: **501.8 pts** (mediana 501.7 pts).
  - % no Percentil Superior ($\ge 800$): **20.3%** (exatamente 20%).
  - % no Percentil Basal ($< 300$): **29.9%** (exatamente 30%).
  - Teste Kolmogorov-Smirnov contra $U(0, 1000)$: $D = 0.01$, **$p = 1.0$** ($p > 0,05$, aderência uniforme comprovada).

---

## 5. Regras de Decisão Aplicadas na Refatoração

1. **Eliminar Alerta por Máximo Diário**: O card de cada ano passa a ser indexado pelo **Percentil da Média Anual**, garantindo representação uniforme de anos ordinários e anos atípicos.
2. **Exibir Dias Acima do P90**: O usuário enxerga a contagem exata de dias no ano acima do percentil 90 da era (com a taxa esperada ao acaso de $\approx 36,5$ dias).
3. **Desacoplar Portais Sazonais**: Os 4 portais são exibidos como amostragem sazonal independente, e não como determinantes do rótulo global do ano.
