# astro-history 🪐🏛️
### Plataforma de Pesquisa Científica Aberta e Reprodutível sobre Alinhamentos Astrológicos e Fatos Históricos

![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![Swiss Ephemeris](https://img.shields.io/badge/Swiss_Ephemeris-2.10.3-00599C)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)
![Testes](https://img.shields.io/badge/Testes-29_Passaram-10B981)
![Licença](https://img.shields.io/badge/Licen%C3%A7a-AGPL--3.0-8B5CF6)
![Marco M2](https://img.shields.io/badge/Marco_M2-Caminho_A_(Piv%C3%B4_Metodol%C3%B3gico)-blue)

> 🌍 **Idiomas / Languages**: **Português** • [English Version (README.md)](README.md)

---

## 1. Resumo Executivo & Pergunta de Pesquisa

O **astro-history** é uma bancada de testes de código aberto concebida para responder com honestidade e método à seguinte questão empírica:

> **"As geometrias de aspectos planetários e alinhamentos astronômicos distinguem grandes eventos históricos da humanidade de datas aleatórias melhor do que o mero acaso?"**

Originalmente construído como um navegador de correlações baseado no **Swiss Ephemeris (`pyswisseph`)**, o projeto passou por uma reconstrução metodológica integral (v2) para erradicar o viés de confirmação retrospectivo (*cherry-picking*), vazamentos de dados e artefatos matemáticos.

### Principal Resultado Empírico (Validação Pré-Registrada da Fase 3 v2)
Sob hipóteses pré-registradas estritas (`docs/hipoteses.md`), amostra analítica unificada ($N=59$) e modelos nulos controlados:
- **Modelo Nulo de Deslocamento Circular (N3, 10.000 permutações)**: Tensão observada $z = -0.506$ ($p = 0.6941$, FDR $q = 0.8834$).
- **Teste Temporal Fora da Amostra (1951–2025)**: $z = -0.851$ ($p = 0.7996$, FDR $q = 0.9329$).
- **Teste de Equivalência Formal (TOST, $\Delta = \pm 0.30$ DP)**: $p_{\text{TOST}} = 0.04103$ (efeito estatisticamente equivalente a zero; hipótese nula sustentada).
- **Tese Arquetípica de Richard Tarnas (Aspectos Duros entre Planetas Lentos)**: $z = -0.063$ ($p = 0.5103$, FDR $q = 0.8834$).

**Conclusão (Decisão do Marco M2)**: A hipótese nula **não pôde ser rejeitada**. Quando os vieses de seleção, a inflação de contatos estelares e o vazamento do matcher são eliminados, as configurações celestes de grandes marcos históricos não diferem estatisticamente de distribuições temporais aleatórias.

Em cumprimento aos critérios pré-registrados, o projeto executou o **CAMINHO A (Pivô Metodológico)**:
1. **Sem Previsões Determinísticas**: Eliminação de termos proféticos ou não calibrados ("Pico Crítico 99%").
2. **Relato Transparente de Resultados Negativos**: Documentação clara de como correlações espúrias surgem na literatura retrospectiva.
3. **Ferramenta Educacional Aberta**: Plataforma interativa que permite ao usuário comparar qualquer mapa histórico com um grupo de controle de 10.000 datas aleatórias.

---

## 2. Reforma Metodológica: Diagnóstico e Correções

| Problema no Código Legado | Falha Metodológica | Correção Técnica Implementada |
| :--- | :--- | :--- |
| **Vazamento de Dados no Matcher (P0-3)** | O comparador de similaridade avaliava o ano contra o próprio evento, gerando auto-matches artificiais de 98.5%. | **Janela Leave-One-Out**: Exclui o ano avaliado $\pm 1$ ano de todo pool de comparação (`find_similar_events`). |
| **Inflação de Contatos com Estrelas (P1-4 / P1-5)** | 1.467 contatos em 300 mapas (~4.9/mapa). Testar 4 aspectos (0°, 90°, 120°, 180°) com 17 corpos gerava ~5 contatos por mapa por puro acaso geométrico uniforme. | **Restrição a Conjunções**: Contatos restritos estritamente a Conjunções ($0^\circ \pm 0.3^\circ$), reduzindo para ~0.72 contatos/mapa, correspondente à probabilidade teórica. |
| **Saturação do Score em 990 (P1-3)** | Fórmula de contraste exponencial arbitrária `min(1.0, excess/640)**1.35 * 920 + 70` fixava o teto em 990.0. | **Percentil Empírico Contínuo**: Escala contínua de 0 a 1000 baseada nos 109.938 dias da grade diária 1800–2100. Score 850 = mais tenso que 85% dos dias modernos. |
| **Incerteza da Lua sem Horário Exato (P1-1)** | A Lua anda ~13.2°/dia. Fixar arbitrariamente 12:00 UT cobria ~22% do zodíaco por dia ao acaso. | **Exclusão Condicional**: A Lua é excluída dos aspectos e do score quando o horário não é comprovado documentalmente. |
| **Amostragem Temporal Assimétrica (P1-2)** | 4 pontos sazonais/ano em anos comuns versus datas exatas em anos com eventos distorciam a linha do tempo. | **Grade Diária Vetorizada**: 1800–2100 pré-computado diariamente (109.938 dias) com agregações anuais homogêneas (mediana, média, p90, máximo). |

---

## 3. Resultados Estatísticos Empíricos (Fase 3 v2)

| Hipótese Testada | N | Score Obs. | Distribuição Nula (Média ± DP) | Efeito ($z$) | $p$ (bicaudal) | $q$ (FDR) | Significante ($q < 0.05$)? |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **H1 Geral vs N3 Deslocamento Circular** | 59 | 481.1 | 500.6 ± 38.5 | -0.506 | 0.6117 | 0.8834 | ❌ Não significante |
| **H1 Geral vs N2 Estratificado por Década** | 59 | 481.1 | 493.9 ± 36.6 | -0.350 | 0.7163 | 0.8834 | ❌ Não significante |
| **H1 Geral vs N1 Uniforme Aleatório** | 59 | 481.1 | 499.7 ± 37.7 | -0.493 | 0.6299 | 0.8834 | ❌ Não significante |
| **H1 Classe: Guerra Interestadual** | 15 | 462.1 | 499.4 ± 73.3 | -0.509 | 0.6163 | 0.8834 | ❌ Não significante |
| **H1 Classe: Crise Econômica** | 10 | 547.6 | 501.9 ± 93.8 | +0.487 | 0.6223 | 0.8834 | ❌ Não significante |
| **H1 Classe: Golpe de Estado** | 11 | 538.4 | 501.6 ± 84.9 | +0.434 | 0.6653 | 0.8834 | ❌ Não significante |
| **H2 Treino Temporal (1800–1950)** | 26 | 512.4 | 499.4 ± 56.8 | +0.229 | 0.8165 | 0.8834 | ❌ Não significante |
| **H2 Teste Fora da Amostra (1951–2025)** | 33 | 456.5 | 501.6 ± 53.0 | -0.851 | 0.4008 | 0.9329 | ❌ Sem sinal preditivo |
| **H4 Tese de Tarnas (Planetas Lentos)** | 59 | 33.4 | 34.0 ± 8.7 | -0.063 | 0.9794 | 0.8834 | ❌ Não significante |

### Inovações Metodológicas na v2
- **Teste de Equivalência TOST**: Com margem $\Delta = \pm 0.30$ DP ($\pm 86.4$ pts), $p_{\text{TOST}} = 0.04103$ rejeitou a hipótese de relevância prática.
- **Poder Estatístico & MDE**: O efeito mínimo detectável com 80% de poder sob $\sigma_{\text{nulo}} = 38.5$ e DP diário uniforme $\sigma = 1000/\sqrt{12} \approx 288.7$ é de 95.7 pontos ($0.332$ DP). O poder formal atinge 72.8% para 0.30 DP, 80.1% no limiar de 0.332 DP e 98.2% para 0.50 DP.
- **Controles Negativos Calibrados**: 1.000 catálogos de ruído puro obtiveram taxa de rejeição de 3.7% com $\alpha = 5\%$ (faixa alvo 3% a 7%), desacoplados do FDR.
- **Amostra Unificada ($N=59$)**: Funil transparente documentado em [`data/exclusion_log.md`](data/exclusion_log.md) delimitado em 1800–2025 com precisão diária.

*Documentos de auditoria e relatórios*:
- Pré-registro formal: [`docs/hipoteses.md`](docs/hipoteses.md)
- Relatório de validação estatística v2: [`reports/validacao_v2.md`](reports/validacao_v2.md)
- Decisão do Marco M2: [`docs/decisao_M2.md`](docs/decisao_M2.md)
- Relatório técnico final v2: [`reports/final_report_v2.md`](reports/final_report_v2.md)

---

## 3b. v3 — Previsão probabilística com skill medido (2026–2060)

A v3 redefine "precisão da estimativa do futuro" como **skill fora da amostra + incerteza calibrada** (ver [`docs/hipoteses_v3.md`](docs/hipoteses_v3.md)):

- **Cálculo:** fuso horário histórico real (IANA; Hora Média Local exata antes de 1883; virada de dia), função de score única lida de `config/score.yaml` com teste de paridade grade↔carta, calendário juliano/gregoriano por região, fallback de casas em latitude polar, estrelas fixas filtradas por latitude eclíptica.
- **Sinal:** 409 features diárias 1750–2150 (fases sinódicas, Índice Cíclico de Barbault, ativação gaussiana de aspectos, harmônicos, declinação, estações/ingressos, meios-pontos, eclipses) e datas exatas por busca de raiz.
- **Alvos:** séries mensais do COW Guerras Interestatais v4, NBER, UCDP/PRIO v24.1 e catálogo v2.
- **Hindcast walk-forward** desde 1951 com Brier Skill Score, AUC, log-loss e IC por bootstrap em blocos anuais → `reports/hindcast_v3.md`.
- **Forecast** em `/forecast` e `/api/forecast`: p(evento) por ano com intervalo p10–p90, razão contra a taxa-base, drivers com datas exatas, análogos por fase dos ciclos e selo de skill.

```bash
make v3   # features -> hindcast -> forecast -> caches da UI
```

**Primeiro resultado:** nenhum modelo astrológico supera a climatologia com IC positivo; a página recomenda a taxa-base onde não há skill.

## 4. Como Executar e Reproduzir

### Pré-requisitos
- Linux / macOS (Python 3.12+)
- Bibliotecas C do Swiss Ephemeris (`libswe-dev`, `libswe0`, `swisseph-data-all`)

```bash
# 1. Clonar repositório
git clone https://github.com/marceloasl99/astro-history.git
cd astro-history

# 2. Configurar ambiente e instalar dependências congeladas
make setup

# 3. Executar suíte completa de testes automatizados
make test

# 4. Rodar validação estatística completa (10.000 permutações sob N3)
make validate

# 5. Iniciar servidor local com a interface responsável (localhost:8000 ou :81)
make run
```

### Execução via Docker
```bash
docker compose up -d --build
```
O proxy reverso Caddy nas portas 80/443 encaminha o tráfego de forma segura para a aplicação.

---

## 5. Estrutura do Repositório

```
astro-history/
├── CITATION.cff              # Metadados de citação acadêmica
├── LICENSE                   # Licença GNU Affero General Public License v3
├── Makefile                  # Automação de compilação, testes e validação
├── Dockerfile                # Especificação de container de produção
├── docker-compose.yml        # Orquestração da aplicação + proxy Caddy
├── Caddyfile                 # Configuração de proxy reverso seguro
├── ci/
│   └── ci.yml                # Especificação de automação de CI/CD
├── pyproject.toml            # Configuração de ferramentas (pytest, ruff, mypy)
├── requirements.lock         # Dependências congeladas exatas
├── config/
│   ├── score.yaml            # Definições de aspectos e pesos de orbes
│   ├── stars.yaml            # Catálogo curado de 28 estrelas fixas
│   └── analysis.yaml         # Permutações estatísticas, sementes e divisões
├── data/
│   ├── DATASET_CARD.md       # Regras objetivas de inclusão e cartão de dados
│   ├── events_v2.csv         # Dataset estruturado (COW, UCDP, NBER, P&T)
│   └── ephemeris/            # Grade diária 1800-2100 pré-computada (.npz)
├── db/
│   └── history_astrology.db  # Banco SQLite (events, events_v2, control_dates)
├── docs/
│   ├── hipoteses.md          # Hipóteses pré-registradas e critérios de sucesso
│   └── decisao_M2.md         # Registro formal de decisão do Marco M2 (Caminho A)
├── reports/
│   ├── baseline_metrics.json # Métricas da auditoria inicial v0
│   ├── phase1_before_after.md# Diff metodológico detalhado (antes vs. depois)
│   ├── phase3_validation.md  # Relatório de permutações, valores-p, escores-z, FDR
│   └── final_report.md       # Relatório científico exaustivo de pesquisa
├── src/
│   ├── astro_engine.py       # Motor de cálculo astronômico Swiss Ephemeris
│   ├── correlation_engine.py # Matcher histórico com leave-one-out
│   ├── future_engine.py      # Linha do tempo homogênea e modelo prospectivo
│   ├── core/
│   │   └── ephemeris_grid.py # 109k efemérides diárias e percentis contínuos
│   ├── data/
│   │   └── ingest_historical.py # Ingestão de dados e gerador de datas de controle
│   ├── analysis/
│   │   ├── null_models.py    # Permutações N1, N2, N3 (deslocamento circular)
│   │   ├── multiplicity.py   # Correção de multiplicidade Benjamini-Hochberg FDR
│   │   └── run_phase3_validation.py # Executor da validação completa
│   └── web/
│       ├── app.py            # Aplicação web FastAPI
│       ├── mandala.py        # Gerador vetorial SVG de mandala zodiacal
│       └── templates/        # Dashboard, detalhe de eventos e aba de metodologia
└── tests/
    ├── regression/           # Testes golden baseline (reprodutibilidade v0)
    ├── unit/                 # Testes unitários (leave-one-out, percentis, orbes)
    └── statistical/          # Verificações de integridade em ruído sintético
```

---

## 6. Licença e Atribuição

- **Código-Fonte**: Licenciado sob a **[GNU Affero General Public License v3 (AGPL-3.0-or-later)](LICENSE)**.
- **Swiss Ephemeris**: Utiliza a biblioteca Swiss Ephemeris da **Astrodienst AG**. Em conformidade com os termos da Astrodienst, o projeto é distribuído sob AGPL. Uso comercial sem termos AGPL exige licença proprietária comercial da Astrodienst AG.
- **Bases de Dados Históricas**: Correlates of War (COW), UCDP Conflict Data, NBER Business Cycles, Powell & Thyne Coup Data e Polity5/V-Dem Project.
