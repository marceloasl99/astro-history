# Relatório de Comparação Antes / Depois: Fase 1 (fix/method-v1)

Data: 2026-10-29  
Objetivo: Auditar quantitativamente as correções de bugs, eliminação de vazamento de dados, remoção do teto artificial de 990 e restrição de contatos estelares.

---

## 1. Tabela Comparativa de Métricas (300 Eventos Históricos)

| Métrica / Dimensão | Antes (v0-baseline) | Depois (Fase 1 Corrigida) | Variação Absoluta | Impacto Metodológico |
| :--- | :---: | :---: | :---: | :--- |
| **Média de Contatos com Estrelas / Mapa** | **4.89** | **0.72** | **-4.17** | **Eliminado o ruído combinatorial**: restrito estritamente a Conjunções ($0^\circ \pm 0.3^\circ$). Taxa real aproxima-se do valor analítico esperado (~0.8/mapa). |
| **Total de Contatos com Estrelas** | **1,467** | **216** | **-1,251** | Queda de 85.3% em contatos espúrios provenientes de quadraturas/trígonos irrelevantes. |
| **Média de Aspectos / Mapa** | **13.13** | **12.57** | **-0.56** | Redução decorrente da **exclusão da Lua** em mapas sem hora exata (P1-1). |
| **Teto Artificial de 990 (Saturação)** | **1** eventos | **0** eventos saturados | **Eliminado** | Eliminação da curva arbitrária `min(1.0, excess/640)**1.35 * 920 + 70`. Pontuação agora reflete rank percentil empírico contínuo. |
| **Tensão Cósmica Média (Escala 0-1000)** | **305.8** | **845.6** | **+539.8** | Scores convertidos em percentis empíricos contra os 109.938 dias da grade diária 1800-2100. |
| **Tensão Mediana** | **276.9** | **872.8** | **+596.0** | Interpretação probabilística direta. |
| **Tensão Máxima Registrada** | **990.0** | **999.6** | **+9.6** | Escala aberta até 1000.0 sem truncamento. |
| **Vazamento de Dados (Matcher Self-Match)** | **Ativo** (Meiji = 98.5% consigo) | **Zero (Leave-One-Out)** | **100% Corrigido** | Janela de exclusão `[ano - 1, ano + 1]` impede auto-combinação. |

---

## 2. Diagnóstico Específico dos Problemas Corrigidos

### P0-3: Vazamento de Dados no Matcher
- **Antes**: Ao analisar um ano ou evento, o catálogo comparava a assinatura daquele ano com o próprio evento já registrado no banco (auto-match artificial com 98.5% de similaridade).
- **Depois**: A função `find_similar_events` agora exige `exclude_year` e `exclude_window=1`, garantindo que eventos dentro de $|ano - Y| \le 1$ sejam excluídos do pool de busca de análogos.

### P1-1: Lua em Mapas sem Hora Exata
- **Antes**: A Lua (velocidade média de ~13.2° por dia) era calculada arbitrariamente ao meio-dia para todos os eventos sem horário, gerando aspectos aleatórios com orbe de 3.0° que cobriam ~22% do zodíaco por acaso.
- **Depois**: Quando `is_time_known is False`, a Lua é sinalizada como incerta e excluída do cômputo de aspectos e do score de tensão.

### P1-2: Amostragem Temporal Sazonal vs. Eventos
- **Antes**: A linha do tempo 1800–2100 usava 4 amostras/ano para anos vazios, mas injetava datas exatas de eventos em anos com registros históricos, distorcendo completamente a comparabilidade.
- **Depois**: Implementada grade diária vetorizada (`src/core/ephemeris_grid.py`) contendo 109.938 dias pré-computados (1800 a 2100). A métrica anual utiliza agregações diárias homogêneas (média, mediana, p90 e máximo de todos os 365 dias).

### P1-3: Saturação do Score em 990
- **Antes**: A curva de contraste exponencial sofria clamp explícito em 990.0, eliminando poder discriminativo em picos de alta tensão.
- **Depois**: O score de tensão agora mapeia a pontuação bruta para o rank percentil empírico exato em relação à distribuição diária contínua de 1800–2100.

### P1-4 & P1-5: Contatos Estelares e a Anomalia de "Scheat"
- **Antes**: O motor testava 4 aspectos (conjunção, quadratura, trígono, oposição) com orbe de 0.3° para 17 corpos e 30 estrelas, gerando uma taxa combinatorial esperada ao acaso de ~5 contatos por mapa (totalizando os 1.467 contatos reportados). Além disso, Scheat (29° Peixes) era sistematicamente ativada por trânsitos de planetas lentos no início de Áries.
- **Depois**: Contatos estelares foram estritamente restritos a **Conjunções ($0^\circ \pm 0.3^\circ$)**, derrubando o total de contatos de 1.467 para 216 (~0.72 contatos por mapa), exatamente condizente com a probabilidade geométrica teórica.
