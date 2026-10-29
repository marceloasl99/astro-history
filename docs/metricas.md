# Dicionário de Métricas Metodológicas: astro-history v2

Este guia formaliza todas as métricas calculadas pelo sistema, eliminando ambiguidades conceituais, misturas de escala e saturação artificial.

---

## 1. Princípios de Desenho

1. **Uma Única Escala por Tela**: Todas as pontuações apresentadas ao usuário operam na **escala percentil empírica calibrada de 0 a 1000 pontos** (onde 500,0 representa exatamente a mediana da distribuição de referência).
2. **Sem Saturação Artificial (No-Clamp)**: Nenhum índice utiliza funções de corte como `min(1000.0, max(10.0, ...))` ou divisores arbitrários. Todo valor decorre da sua posição no ranking empírico contínuo.
3. **Distribuição de Referência Declarada**: Cada número explicita contra qual universo é comparado (ex: todos os ~110.000 dias de 1800–2100 vs. todos os 301 anos da era).
4. **Sem Conotação Preditiva Indevida**: Conforme a decisão formal do Marco M2 (Caminho A), as métricas medem exclusivamente **geometria astronômica e densidade de aspectos angulares**, não probabilidades mecânicas de guerras, crises financeiras ou eventos sociais.

---

## 2. Definições das Métricas Canônicas

### 2.1 Score Geométrico Bruto Diário ($S_{\text{raw}}$)
- **O que é**: Soma ponderada das orbes dos aspectos maiores clássicos (conjunção, quadratura, trígono, oposição) formados entre os corpos planetários em determinado dia às 12:00 UT.
- **Corpos Utilizados**: 9 corpos celestes principais do sistema solar (Sol, Mercúrio, Vênus, Marte, Júpiter, Saturno, Urano, Netuno, Plutão).
- **Orbe Máximo**: $3,0^\circ$, com peso inversamente proporcional à orbe: $w = (3,0 - \text{orbe}) / 3,0$.
- **Uso**: Estritamente interno, serve de base para o mapeamento de percentil empírico. Não é exibido diretamente ao usuário final.

### 2.2 Percentil Geométrico Diário ($P_{\text{dia}}$)
- **Fórmula**: 
  $$P_{\text{dia}}(d) = \frac{\text{rank}(S_{\text{raw}}(d))}{|\text{Grade Diária}|} \times 1000,0$$
- **Escala**: $0,0$ a $1000,0$ pontos (equivalente a $0,0\%$ a $100,0\%$).
- **Distribuição de Referência**: Grade contínua diária de 113.596 dias ($01/01/1800$ a $31/12/2100$).
- **Interpretação**: Um dia com $P_{\text{dia}} = 850,0$ possui alinhamento geométrico mais tenso do que $85,0\%$ de todos os dias dos três séculos.

### 2.3 Percentil Médio Anual ($P_{\text{ano}}$)
- **Fórmula**: 
  1. Calcula-se a média aritmética dos 365/366 scores brutos diários do ano $Y$: $\bar{S}_Y = \frac{1}{N_{\text{dias}}} \sum_{d \in Y} S_{\text{raw}}(d)$.
  2. Mapeia-se $\bar{S}_Y$ contra o vetor das 301 médias anuais de 1800 a 2100:
     $$P_{\text{ano}}(Y) = \frac{\text{rank}(\bar{S}_Y)}{301} \times 1000,0$$
- **Escala**: $0,0$ a $1000,0$ pontos.
- **Distribuição de Referência**: Conjunto dos 301 anos (1800–2100).
- **Interpretação**: Responde onde o ano $Y$ se posiciona em relação a anos típicos. Um ano com $P_{\text{ano}} \approx 500$ é um ano ordinário na história astronômica.
- **Classificação por Faixas**:
  - `Percentil Superior (≥ 800,0)`: Ano de configuração geométrica infrequente (top 20% da era).
  - `Percentil Moderado (300,0 a 799,9)`: Ano dentro do comportamento típico esperado.
  - `Percentil Basal (< 300,0)`: Ano com baixa densidade de aspectos tensos na média.

### 2.4 Dias Acima do Percentil 90 ($\text{Dias}_{>P90}$)
- **Fórmula**: Contagem de dias no ano civil cujo score diário excede o limiar empírico do percentil 90 da era inteira ($S_{\text{raw}} \ge \text{P90}_{\text{global}}$).
- **Escala**: Inteiro entre $0$ e $366$.
- **Valor Esperado ao Acaso**: $\approx 36,5$ dias por ano ($10\%$ dos dias).
- **Interpretação**: Evita a distorção do "máximo anual". Mostra quantos dias de alta tensão angular o ano efetivamente concentrou.

### 2.5 Portais Sazonais
- **O que são**: Amostragem do percentil geométrico diário nos 4 marcos do ciclo solar (Equinócio de Março, Solstício de Junho, Equinócio de Setembro, Solstício de Dezembro).
- **Escala**: $0,0$ a $1000,0$ pontos por portal.
- **Interpretação**: Variação intra-anual da geometria celeste entre as estações.

### 2.6 Índice de Similaridade Geométrica (Matcher)
- **Fórmula**: Medida de concordância angular entre corpos lentos e aspectos de uma data frente aos eventos históricos catalogados, aplicando penalização por prevalência de aspectos para evitar efeito *hub*.
- **Escala**: $0,0\%$ a $100,0\%$.
- **Natureza Metodológica**: **Exploração de isomorfismo geométrico**. Não é uma previsão de causalidade histórica ou de repetição factual de eventos.

---

## 3. Sub-índices Removidos e Justificativa

| Sub-índice Anterior | Motivo da Remoção da Interface | Evidência Empírica |
| :--- | :--- | :--- |
| **Risco Bélico** | Não discrimina eventos de guerra em relação a outros tipos de eventos. Nome sugestivo e enganoso. | $\text{AUC} = 0,457$ ($p = 0,57$) via Mann-Whitney U. |
| **Risco de Crise** | Sem calibração, inflado artificialmente em anos com Saturno/Plutão, saturava em 1000,0. | 4 anos no teto (1000,0) e ausência de correlação com recessões NBER. |
| **Disrupção Tech** | Fórmula baseada em trígonos arbitrários, saturava e não possuía validação empírica. | Rejeitado conforme critério de higiene metodológica. |

---

## 4. Resumo de Conversão Visual para a Interface

| Conceito Anterior | Problema | Solução v2 |
| :--- | :--- | :--- |
| "Tensão Cósmica: 96,9% (Crítico / Ruptura Histórica)" em 34 de 34 anos | Saturação decorrente do uso do pico diário máximo do ano frente a limiar fixo. | **Percentil Anual**: Exibe o percentil empírico da média do ano (distribuição equilibrada entre anos altos, médios e baixos). |
| "Média Anual 349,8" ao lado de portais de média 848,5 | Mistura de bases com e sem estrelas fixas. | Escala diária uniforme para os portais e indicação transparente da média do ano. |
| "43,6% match" e "40,2% de similaridade" misturados | Ambiguidade entre Top-1 e média do Top-3. | Exibição unificada com rótulo "Similaridade Geométrica Top-1 (com evento X)". |
