# Decisão Formal do Marco M2 (Versão v2 Calibrada)

- **Data da Decisão**: 2026-10-29
- **Veredito Oficial**: **CAMINHO A (Pivô Metodológico)**

---

## 1. Sumário Executivo da Decisão

De acordo com os princípios de pré-registro de hipóteses (`docs/hipoteses.md`):
1. **Ausência de Efeito Detectável**: O teste principal sob deslocamento circular N3 resultou em $z = -0.506$ ($p = 0.6941$, FDR $q = 0.8834$).
2. **Equivalência Estatística Comprovada (TOST)**: Rejeitou-se a existência de efeito $\ge 0,3$ DP ($p_{\text{TOST}} = 0.04103 < 0,05$). O efeito é equivalente ao acaso.
3. **Poder Estatístico Declarado**: O teste possui poder $\ge 80\%$ para detectar efeitos $\ge 95.7 pontos$.
4. **Generalização Fora da Amostra**: No período pós-1950 intocado, $z = -0.851$ ($p = 0.7996$).

---

## 2. Ações Metodológicas Implementadas

- **Cancelamento de Modelos Preditivos**: Nenhuma alegação de previsões determinísticas ou de "risco bélico/crise" é exibida ao usuário.
- **Plataforma de Literacia Estatística**: O dashboard atua como instrumento educacional e de pensamento crítico, demonstrando como ilusões de correlação se formam por orbes largos e viés de confirmação retrospectivo.
- **Fonte Canônica Única**: Todos os dados apresentados no site derivam exclusivamente do arquivo auditável `data/results.json` gerado por `make validate`.
