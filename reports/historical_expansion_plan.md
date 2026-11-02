# Plano Estratégico de Expansão da Base Histórica do AstroHistory

**Data:** 02 de Novembro de 2026  
**Documento de Engenharia e Curadoria Histórica**  
**Escopo:** Expansão da Base Geral de 300 para > 1.100 Eventos Documentados  

---

## 1. Princípios Epistemológicos & Arquitetura Tripartida

Para permitir investigações computacionais em larga escala sem violar os princípios da inferência científica e do pré-registro, a arquitetura de dados do AstroHistory é formalmente dividida em três camadas desacopladas:

```
┌────────────────────────────────────────────────────────────────────────┐
│                   A. Catálogo Histórico Geral                          │
│  > 1.100 eventos | Cobertura milenar | Exploração | Cosmic History Search│
└────────────────────────────────────────────────────────────────────────┘
                                    │
         ┌──────────────────────────┴──────────────────────────┐
         ▼                                                     ▼
┌─────────────────────────────────────┐   ┌──────────────────────────────┐
│  B. Dataset de Pesquisa Validado    │   │ C. Séries Históricas         │
│     (events_v2, N=59, 1800–2025)    │   │    Objetivas Contínuas       │
│  Inclusão estrita | Pré-registrado  │   │  COW Wars, NBER, UCDP        │
│  Testes de hipótese nula & TOST     │   │  Hindcast walk-forward v3    │
└─────────────────────────────────────┘   └──────────────────────────────┘
```

1. **Camada A — Catálogo Histórico Geral (`data/historical_events.json` e tabela `events`):**
   - Banco de alta densidade voltado para **busca de análogos astronômicos**, visualização, exploração de narrativas e contextualização histórica.
   - Reúne mais de 1.100 acontecimentos históricos reais de todas as regiões e épocas, cobrindo conflitos, crises, desastres, mas também **grandes tratados de paz, revoluções científicas, avanços médicos e marcos construtivos**.
   - Cada evento possui metadados completos de proveniência acadêmica e precisão de datação.

2. **Camada B — Dataset Analítico Validado (`data/events_v2.csv` e tabela `events_v2`, N=59):**
   - Conjunto **completamente congelado e independente** do Catálogo Geral.
   - Segue os critérios operacionais estritos pré-registrados na Fase 2 (início exato com datação diária comprovada, fontes formais COW/UCDP/NBER/P&T, janela 1800–2025, pareamento com 10.000 datas de controle estratificadas).
   - **Regra Inviolável:** A expansão do Catálogo Geral NÃO altera nem reescreve a amostra `events_v2`.

3. **Camada C — Séries Históricas Objetivas Contínuas (`data/external/`):**
   - Séries temporais mensais derivadas diretamente de arquivos brutos sem seleção pontual de marcos (inícios de guerras COW, meses de recessão NBER, episódios de conflito armado UCDP/PRIO).
   - Utilizadas exclusivamente no hindcast walk-forward com pontuação Brier Skill Score (BSS).

---

## 2. Taxonomia Canônica de 7 Categorias

O catálogo histórico expandido abandona a ênfase exclusiva em guerras e tragédias, incorporando uma classificação equilibrada e bidirecional:

| Categoria (`category`) | Descrição Temática | Polaridade Padrão | Exemplos Documentados |
| :--- | :--- | :---: | :--- |
| **`politics_geopolitics`** | Início e término de guerras, batalhas decisivas, revoluções, golpes de Estado, tratados de paz, independências e colapso de impérios. | `disruptive` / `constructive` | Início da 1ª Guerra Mundial (1914), Queda do Muro de Berlim (1989), Golpe de 1964. |
| **`economics_finance`** | Crashes de bolsas, pânicos bancários, hiperinflações, colapsos cambiais, moratórias soberanas e reformas monetárias. | `disruptive` / `structural` | Pânico de 1873, Crash de 1929, Plano Real (1994), Colapso Lehman Brothers (2008). |
| **`health_epidemics`** | Eclosão de pandemias, epidemias globais, descoberta de patógenos, declarações da OMS e erradicação de enfermidades. | `disruptive` / `constructive` | Peste Negra (1347), Gripe Espanhola (1918), Descoberta da Penicilina (1928), Erradicação da Varíola (1980). |
| **`natural_disasters`** | Grandes terremotos catastróficos, erupções vulcânicas de impacto climático global, tsunamis e secas severas. | `disruptive` | Terremoto de Lisboa (1755), Erupção do Tambora (1815), Terremoto de San Francisco (1906), Tsunami de Sumatra (2004). |
| **`science_technology`** | Invenções pioneiras, teorias físicas revolucionárias, primeiros voos, início da era espacial, computação e inteligência artificial. | `constructive` | Publicação do *Principia* de Newton (1687), Primeiro Voo de Santos Dumont (1906), Sputnik 1 (1957), Apollo 11 (1969). |
| **`society_culture`** | Movimentos de direitos civis, abolição da escravidão, reformas educacionais, sufrágio feminino e marcos humanitários. | `constructive` | Lei Áurea no Brasil (1888), Marcha sobre Washington de M.L. King (1963), Fim do Apartheid (1994). |
| **`constructive_positive`** | Tratados internacionais de desarmamento, pactos duradouros de cooperação internacional e reconciliações históricas. | `constructive` | Paz de Westfália (1648), Tratado de Versalhes (1919), Declaração Universal dos Direitos Humanos (1948). |

---

## 3. Especificação do Esquema de Dados dos Eventos

Cada registro do catálogo expandido implementa os seguintes 19 atributos normalizados:

```json
{
  "id": 1042,
  "title": "Primeiro Pouso Humano na Lua (Missão Apollo 11)",
  "description": "O módulo lunar Eagle pousa com sucesso na superfície lunar, marcando o ápice da exploração espacial.",
  "category": "science_technology",
  "subcategory": "space_exploration",
  "date": "1969-07-20",
  "date_precision": "day",
  "time": "20:17",
  "is_time_known": true,
  "city": "Houston",
  "country": "Estados Unidos",
  "continent": "América do Norte",
  "latitude": 29.56,
  "longitude": -95.09,
  "polarity": "constructive",
  "severity": 10.0,
  "source_name": "NASA Historical Archives",
  "source_url": "https://www.nasa.gov/mission_pages/apollo/missions/apollo11.html",
  "source_record_id": "APOLLO-11-LUNAR-LANDING",
  "verification_status": "verified"
}
```

### Regras de Precisão Temporal (`date_precision`):
1. **`day` (Obrigatório para cálculos de trânsito planetário diário):** Dia do calendário histórico civil rigorosamente documentado.
2. **`month` / `year` (Permitido para contextualização narrativa ou estudos de séculos):** Se o dia for contestado, o evento é marcado explicitamente como `date_precision = "month"` ou `"year"`, impedindo que seja tratado como se tivesse precisão horária.
3. **`is_time_known`:** Se `false`, o cálculo astronômico exclui automaticamente a Lua e não gera casas/Ascendente, eliminando falsos positivos.

---

## 4. Matriz de Fontes Estruturadas & Metas de Ingestão

| Fonte Primária | Tipo de Dados | Período | Formato | Quantidade Esperada |
| :--- | :--- | :---: | :---: | :---: |
| **Catálogo Curado Legado** | Marcos multidisciplinares mundiais | 1000 a.C. a 2024 | JSON interno | ~300 eventos |
| **Correlates of War (COW v4.0)** | Inícios de guerras interestatais | 1816 a 2007 | CSV acadêmico | ~95 guerras |
| **UCDP/PRIO Armed Conflict v24.1** | Início de episódios de conflito armado | 1946 a 2023 | CSV acadêmico | ~299 conflitos |
| **Powell & Thyne Coup Dataset** | Golpes de Estado globais (sucesso/falha) | 1950 a 2026 | CSV oficial | ~497 golpes |
| **USGS Earthquake Hazards Catalog** | Sismos mundiais catastróficos ($M \ge 7.8$) | 1900 a 2024 | GeoJSON API / CSV | ~90 sismos |
| **Marcos Históricos Positivos Curados** | Tratados de paz, ciência, saúde, tecnologia | 1500 a 2024 | Base curada auditada | ~150 eventos |
| **Total Projetado Pós-Deduplicação** | **Base Consolidada Expandida** | **Milenar** | **JSON / SQLite** | **> 1.100 eventos** |

---

## 5. Regras de Deduplicação & Higiene de Dados

Durante a fusão das fontes, o importador mestre [`scripts/expand_historical_database.py`](file:///home/astro/scripts/expand_historical_database.py) aplica as seguintes regras:
1. **Deduplicação Fuzzy:** Se dois eventos ocorrerem dentro de $\pm 2$ dias no mesmo país ou com distância geográfica $\le 300\text{ km}$ e apresentarem similaridade de título $> 0.70$ (ex.: *Guerra da Crimeia* em COW e no catálogo legado), o registro com maior riqueza de metadados é preservado, registrando os IDs cruzados no campo de notas.
2. **Datas Múltiplas do Mesmo Conflito:** Cada conflito tem uma única entrada para o seu **início formal/deflagração** (`onset`). Tratados de encerramento são codificados separadamente na categoria `constructive_positive` ou `politics_geopolitics`, com o título indicando claramente tratar-se do acordo de paz (ex.: *Tratado de Versalhes*, e não *Primeira Guerra Mundial*).
3. **Validação Astronômica de Calendário:** Datas anteriores a 1582 utilizam o Calendário Juliano com conversão astronômica rigorosa via Swiss Ephemeris (`swe.julday`), respeitando a transição gregoriana de cada região documentada.
