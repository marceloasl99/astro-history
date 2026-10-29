# astro-history 🪐🏛️
### Astrologia Moderna, Cálculos Cosmológicos e Motor de Correlação Histórica para 300 Grandes Fatos Mundiais (1800–2100)

![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![Swiss Ephemeris](https://img.shields.io/badge/Swiss_Ephemeris-2.10.3-00599C)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)
![Porta 81](https://img.shields.io/badge/Dashboard-Porta_81-F59E0B)
![Testes](https://img.shields.io/badge/Testes-13_Aprovados-10B981)
![Licença](https://img.shields.io/badge/Licen%C3%A7a-MIT-8B5CF6)

> 🌍 **Languages / Idiomas**: [English Version (README.md)](README.md) • **Português**

O **astro-history** é uma plataforma analítica e prospectiva de código aberto fundamentada na **Astrologia Moderna e Astrologia Mundial**. O sistema utiliza o motor de alta precisão **Swiss Ephemeris (`pyswisseph`)** para calcular as posições celestes de **17 corpos celestes**, aspectos ptolomaicos estritos (orbe máx. de 3,0°) e contatos longitudinais com as **30 principais estrelas fixas** da abóbada celeste.

A plataforma audita um catálogo de **300 marcos históricos reais** (da Antiguidade a 2024), quantifica a tensão sistêmica em uma **Escala de Tensão Cósmica de alta resolução (0 a 1000 pontos e porcentagem)** e gera uma **linha do tempo contínua de 301 anos (1800 a 2100)** que correlaciona arquétipos planetários com os grandes pontos de inflexão da história humana.

---

## Demonstração Visual (Screenshots em Resolução Full HD 1920×1080)

### 1. Dashboard Interativo e Linha do Tempo Cósmica (1800–2100)
Gráfico interativo em Chart.js com filtros por época (*1800–1899*, *1900–1999*, *2000–2025*, *2026–2100* e *Todos*). Estrelas douradas (★) demarcam fatos históricos reais e a linha contínua mapeia a evolução da tensão de fundo:
![Dashboard & Linha do Tempo AstroHistory](docs/screenshots/01_dashboard_timeline.png)

---

### 2. Linha do Tempo & Simulador Prospectivo (1800–2100)
Motor de simulação em tempo real com níveis de alerta (Estável, Moderado, Alto, Crítico), sub-índices de risco (Bélico, Crise Financeira, Inovação Tecnológica) e correspondência analógica automatizada:
![Simulador & Linha do Tempo](docs/screenshots/02_simulator_timeline.png)

---

### 3. Mandala Zodiacal Vetorial SVG Nativa & Diagnóstico do Fato
Mapa natal interativo com graus exatos, movimentos retrógrados e aspectos coloridos por orbe estrito, acompanhado de pontuação matemática e corroboração teórica (ex.: Crash de 1929):
![Detalhes do Evento com Mandala Zodiacal SVG](docs/screenshots/03_event_mandala.png)

---

### 4. Catálogo dos 300 Grandes Fatos Históricos
Busca textual instantânea e filtros por categorias geopolíticas: Revoluções Políticas, Guerras & Conflitos, Ciência & Tecnologia, Crises Econômicas, Transformações Culturais e Pandemias:
![Catálogo dos 300 Fatos](docs/screenshots/04_events_catalog.png)

---

### 5. Hub de Macro Correlações & Estatísticas Planetárias
Análise estatística comparativa demonstrando distribuições planetárias, balanço dos quatro elementos e médias de tensão cósmica em todas as categorias históricas:
![Hub de Correlações](docs/screenshots/05_correlations_hub.png)

---

### 6. Matriz de Cenários & Portais Sazonais (2027–2060)
Aba analítica dedicada oferecendo a projeção ano a ano dos 34 anos do horizonte futuro, com identificação da data exata do pico sazonal (Equinócios e Solstícios), avaliação de riscos multidimensionais e gaveta expansível dos 4 portais sazonais por ano:
![Matriz de Cenários 2027–2060](docs/screenshots/06_projections_2027_2060.png)

---

## Sumário
1. [Visão Geral & Fundamentação Teórica](#1-visão-geral--fundamentação-teórica)
2. [Arquitetura do Sistema](#2-arquitetura-do-sistema)
3. [Motor Astronômico & Efemérides](#3-motor-astronômico--efemérides)
4. [Escala de Tensão Cósmica (0–1000 Pontos)](#4-escala-de-tensão-cósmica-01000-pontos)
5. [Aba de Cenários Prospectivos (2027–2060)](#5-aba-de-cenários-prospectivos-20272060)
6. [Catálogo dos 300 Fatos Históricos](#6-catálogo-dos-300-fatos-históricos)
7. [Diagnóstico via Linha de Comando (CLI)](#7-diagnóstico-via-linha-de-comando-cli)
8. [Dashboard Web & Especificação da API REST](#8-dashboard-web--especificação-da-api-rest)
9. [Instalação, Dependências & Daemon Systemd](#9-instalação-dependências--daemon-systemd)
10. [Suíte de Testes Automatizados](#10-suíte-de-testes-automatizados)

---

## 1. Visão Geral & Fundamentação Teórica

A Astrologia Moderna concebe a correlação entre dinâmica celeste e história humana não como determinismo mecânico causal, mas como uma **ordem sincrônica arquetípica**. Fundamenta-se em:
- **Carl G. Jung**: O princípio da *Sincronicidade* — coincidências significativas acausais conectando estados psíquicos e eventos físicos externos.
- **Dane Rudhyar**: *Astrologia Humanística e Transpessoal* — ciclos planetários como fases evolutivas da consciência coletiva.
- **Richard Tarnas**: *Cosmos e Psique (2006)* — extensa validação histórica demonstrando que momentos revolucionários e geopolíticos coincidem com aspectos tensos entre planetas transpessoais (*Urano, Netuno, Plutão e Saturno*).

---

## 2. Arquitetura do Sistema

- **Armazenamento**: Swiss Ephemeris (`libswe`), SQLite (`db/history_astrology.db`) com 300 mapas astrais pré-calculados e 1.467 contatos com estrelas fixas.
- **Motores Centrais (`src/`)**:
  - `astro_engine.py`: 17 corpos celestes, 30 estrelas fixas (orbe 0,3°), aspectos maiores (orbe 3,0°).
  - `correlation_engine.py`: Comparador arquetípico e similaridade histórica.
  - `future_engine.py`: Motor de linha do tempo contínua 1800–2100 e amostragem sazonal quádrupla.
  - `analyze_correlations.py`: Diagnóstico analítico de ênfase cosmológica.
- **Camada Web (FastAPI na Porta 81)**:
  - `app.py`: Servidor HTTP/JSON bound em `0.0.0.0:81`.
  - `mandala.py`: Gerador de mandalas SVG zodiacais vetoriais nativas.
  - Templates em Tailwind CSS e Chart.js otimizados para resolução Full HD (1920×1080).

---

## 3. Motor Astronômico & Efemérides

- **17 Corpos Celestes**: Sol, Lua, Mercúrio, Vênus, Marte, Júpiter, Saturno, Urano, Netuno, Plutão, Ceres, Pallas, Juno, Vesta, Quíron, Lilith Média e Nodo Norte Verdadeiro.
- **Aspectos Ptolomaicos Estritos**: Conjunção (0°), Oposição (180°), Quadratura (90°) e Trígono (120°) com orbe estrito $\le 3,0^\circ$.
- **30 Estrelas Fixas Principais**: Algol, Sirius, Aldebaran, Betelgeuse, Rigel, Regulus, Spica, Antares, Vega, Altair, Deneb, Fomalhaut, Polaris, Scheat, etc. (orbe estrito $\le 0,3^\circ$).

---

## 4. Escala de Tensão Cósmica (0–1000 Pontos)

Fórmula de alta resolução baseada no cálculo ponderado de fricção angular:
- **0 a 349 pontos**: Céu Calmo / Estável (🟢)
- **350 a 549 pontos**: Tensão Moderada / Transição (🟡)
- **550 a 749 pontos**: Tensão Alta / Alerta Intenso (🟠)
- **750 a 1000 pontos**: Tensão Crítica / Ruptura Histórica (🔴)

---

## 5. Aba de Cenários Prospectivos (2027–2060)

Disponível na rota `/projections` e na API `/api/projections-2027-2060`:
- **34 Anos Mapeados**: Amostragem de todos os portais sazonais (Equinócios de Março e Setembro, Solstícios de Junho e Dezembro).
- **Data Exata do Pico**: Identificação automatizada do portal mais tenso do ano.
- **Sub-Índices**: Risco Bélico %, Crise Financeira % e Inovação Tecnológica %.
- **Gaveta Expansível**: Visualização detalhada das 4 medições sazonais individuais por ano.

---

## 6. Catálogo dos 300 Fatos Históricos

Armazenado em `data/historical_events.json` e indexado no banco SQLite:
- **Revoluções Políticas (96 eventos)**: Independência dos EUA, Revolução Francesa, Queda da Bastilha, Restauração Meiji, Proclamação da República no Brasil, Queda do Muro de Berlim, Primavera Árabe.
- **Guerras & Conflitos (91 eventos)**: Guerras Napoleônicas, Guerra Civil Americana, Primeira e Segunda Guerras Mundiais, Vietnã, Guerra da Ucrânia.
- **Ciência & Tecnologia (58 eventos)**: Principia de Newton, Máquina a Vapor, Teoria da Relatividade, Pouso na Lua, Criação da Internet, CRISPR, ChatGPT.
- **Crises Econômicas (25 eventos)**: Bolha das Tulipas, Crash de 1929, Choques do Petróleo, Crise Asiática, Crise Financeira de 2008.
- **Transformações Culturais (17 eventos)**: Reforma Protestante, Woodstock, Declaração Universal dos Direitos Humanos.
- **Pandemias & Desastres (13 eventos)**: Peste Negra, Gripe Espanhola de 1918, Desastre de Chernobyl, Pandemia de COVID-19.

---

## 7. Diagnóstico via Linha de Comando (CLI)

```bash
source .venv/bin/activate

# 1. Auditar um evento específico (ex.: Crash de 1929 #93)
python src/analyze_correlations.py --event 93

# 2. Auditar a Bomba de Hiroshima (#107)
python src/analyze_correlations.py --event 107

# 3. Auditar uma categoria inteira
python src/analyze_correlations.py --category "Crise Econômica"

# 4. Exportar relatório macro-estatístico completo
python src/analyze_correlations.py --export-json data/correlations_report.json
```

---

## 8. Dashboard Web & Especificação da API REST

O serviço web roda na porta 81 (`0.0.0.0:81`):
- **`/`**: Dashboard principal com gráfico Chart.js 1800–2100 e marcos paradigmáticos.
- **`/events`**: Catálogo completo dos 300 fatos com busca e filtros.
- **`/events/{id}`**: Mandala zodiacal SVG vetorial nativa e posições dos 17 corpos celestes.
- **`/correlations`**: Hub de macro correlações geopolíticas.
- **`/projections`**: Matriz de cenários prospectivos 2027–2060 e portais sazonais.
- **`/simulator`**: Linha do tempo 1800–2100 e simulador personalizado de cartas astrais.

### Endpoints da API REST
| Endpoint | Método | Formato | Descrição |
| :--- | :---: | :---: | :--- |
| `/api/stats` | `GET` | JSON | Total de eventos, progresso e balanço elemental. |
| `/api/events` | `GET` | JSON | Lista dos 300 eventos com filtros (`?category=` e `?search=`). |
| `/api/events/{id}` | `GET` | JSON | Mapa astral natal detalhado, estrelas fixas e aspectos. |
| `/api/future-timeline` | `GET` | JSON | Linha do tempo contínua completa de 301 anos (1800–2100). |
| `/api/projections-2027-2060` | `GET` | JSON | Projeções anuais dos 34 anos futuros com 4 portais sazonais por ano. |
| `/api/simulate` | `POST` | JSON | Cálculo on-demand de carta astral e 5 principais precedentes. |

---

## 9. Instalação, Dependências & Daemon Systemd

### 9.1. Requisitos do Sistema (Ubuntu 24.04 LTS / Debian)
```bash
sudo apt-get update
sudo apt-get install -y build-essential python3-dev python3-venv git \
    libswisseph-dev swe-basic-data swe-standard-data
```

### 9.2. Instalação do Ambiente Python
```bash
git clone https://github.com/marceloasl99/astro-history.git
cd astro-history
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 9.3. Serviço Systemd (Porta 81)
O serviço é gerenciado pelo systemd em `/etc/systemd/system/astro-history.service`:
```bash
sudo systemctl daemon-reload
sudo systemctl enable astro-history.service
sudo systemctl restart astro-history.service
sudo systemctl status astro-history.service
```

---

## 10. Suíte de Testes Automatizados

A suíte completa de testes unitários e de integração roda via `pytest`:
```bash
source .venv/bin/activate
pytest tests/
```
**Resultado**: 13 testes aprovados cobrindo motores astronômicos, cálculo de tensão, correlacionador arquetípico, linha do tempo prospectiva e todos os endpoints HTTP da API REST.
