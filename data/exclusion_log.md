# Log de Curadoria, Inclusão e Exclusão Amostral: events_v2

> **Auditoria Metodológica (Etapa 6)**:  
> Rastreamento transparente de como o catálogo original de 300 marcos históricos foi estruturado no conjunto analítico objetivo `events_v2` e como o $N$ analítico foi unificado.

---

## 1. Funil de Seleção e Critérios de Inclusão

O catálogo inicial continha 300 marcos históricos curados informalmente (incluindo eventos antigos como a Batalha de Maratona e o Império Romano, até eventos contemporâneos). Para os testes estatísticos rigorosos contra a grade de efemérides em alta resolução, estabeleceu-se o dataset canônico `events_v2` com os seguintes filtros de higiene:

```
[300 Marcos Históricos Informais]
           │
           ▼
[Filtro 1: Fontes Acadêmicas Formais (COW, UCDP, NBER, Powell & Thyne, Polity5)]
           │
           ▼
[Filtro 2: Precisão Documental de Data (Início Exato do Fenômeno em nível 'day')]
           │
           ▼
[Catálogo events_v2 com date_precision = 'day'] ───► Total: 61 Eventos
           │
           ▼
[Filtro 3: Fronteira da Grade Diária de Efemérides (1800-01-01 a 2025-12-31)]
           │
           ├── Exclusão 1: 1789-07-14 (Storming of the Bastille) [Século XVIII]
           └── Exclusão 2: 1799-11-09 (Coup of 18 Brumaire) [Século XVIII]
           │
           ▼
[Conjunto Analítico Diário Unificado N3/N2/N1] ───► Total: 59 Eventos
```

---

## 2. Eventos Excluídos do Filtro 1800–2025

| ID | Título | Data Original | Classe | Motivo Formal de Exclusão |
| :---: | :--- | :---: | :--- | :--- |
| **52** | Storming of the Bastille (French Revolution) | `1789-07-14` | `regime_change` | Fora da janela temporal analítica da grade diária contínua ($1800$ a $2025$). |
| **40** | Coup of 18 Brumaire (Napoleon Takes Power) | `1799-11-09` | `coup_d_etat` | Fora da janela temporal analítica da grade diária contínua ($1800$ a $2025$). |

---

## 3. Composição e Balanceamento da Amostra Analítica ($N = 59$)

### 3.1 Por Classe de Evento
- `war_interstate`: 15 eventos ($25,4\%$)
- `coup_d_etat`: 11 eventos ($18,6\%$)
- `regime_change`: 9 eventos ($15,3\%$)
- `economic_recession`: 10 eventos ($16,9\%$)
- `armed_conflict`: 9 eventos ($15,3\%$)
- `pandemic`: 5 eventos ($8,5\%$)

### 3.2 Por Época (Split Temporal Walk-Forward)
- **Período de Treino Histórico (1800–1950)**: 26 eventos ($44,1\%$)
- **Período de Teste Fora da Amostra (1951–2025)**: 33 eventos ($55,9\%$)
- **Total**: $26 + 33 = 59$ eventos (unificado e sem discrepâncias entre os modelos N1, N2 e N3).

### 3.3 Por Região Continental
- Europa: 27 eventos ($45,8\%$)
- Américas: 15 eventos ($25,4\%$)
- Ásia: 11 eventos ($18,6\%$)
- África / Oriente Médio: 6 eventos ($10,2\%$)
- *Nota de Limitação*: Nenhum país isolado excede $20\%$ da amostra (EUA com $18,6\%$, França com $13,5\%$). O viés eurocêntrico remanescente decorre da maior disponibilidade de registros diplomáticos com precisão de dia no século XIX.

## astrohistory_curated_v6 — 2026-11-06 (49 excluídos)

- `1415-10-25` **Batalha de Agincourt** (França) — duplicata: título similar (0.63) a #206
- `1453-05-29` **Queda de Constantinopla** (Turquia) — duplicata: título similar (1.00) a #18
- `1494-06-07` **Tratado de Tordesilhas** (Espanha) — duplicata: título similar (0.76) a #20
- `1500-04-22` **Chegada de Pedro Álvares Cabral ao Brasil** (Brasil) — duplicata: título similar (1.00) a #21
- `1521-08-13` **Queda de Tenochtitlán** (México) — duplicata: título similar (0.59) a #23
- `1522-09-06` **Conclusão da primeira circum-navegação (Elcano)** (Espanha) — duplicata: título similar (0.55) a #24
- `1532-11-16` **Captura de Atahualpa em Cajamarca** (Peru) — duplicata: título similar (0.73) a #207
- `1571-10-07` **Batalha de Lepanto** (Grécia) — duplicata: título similar (1.00) a #27
- `1588-08-08` **Derrota da Armada Invencível** (França) — duplicata: título similar (0.64) a #29
- `1649-01-30` **Execução de Carlos I da Inglaterra** (Reino Unido) — duplicata: título similar (0.64) a #34
- `1666-09-02` **Grande Incêndio de Londres** (Reino Unido) — duplicata: título similar (1.00) a #35
- `1683-09-12` **Batalha de Viena: fim do cerco otomano** (Áustria) — duplicata: título similar (0.73) a #210
- `1773-12-16` **Festa do Chá de Boston** (Estados Unidos) — duplicata: título similar (0.70) a #212
- `1805-10-21` **Batalha de Trafalgar** (Espanha) — duplicata: título similar (1.00) a #48
- `1948-12-10` **Declaração Universal dos Direitos Humanos** (França) — duplicata: título similar (0.81) a #113
- `1957-03-25` **Tratado de Roma cria a Comunidade Econômica Europeia** (Itália) — duplicata: título similar (0.83) a #119
- `1993-09-13` **Acordos de Oslo (Declaração de Princípios)** (Estados Unidos) — duplicata: título similar (0.61) a #162
- `1998-04-10` **Acordo de Sexta-Feira Santa** (Reino Unido) — duplicata: título similar (0.57) a #311
- `2015-12-12` **Acordo de Paris sobre o clima** (França) — duplicata: título similar (0.67) a #184
- `1720-09-01` **Estouro da Bolha da South Sea Company** (Reino Unido) — duplicata: título similar (0.56) a #38
- `1923-11-15` **Pico da hiperinflação alemã** (Alemanha) — duplicata: título similar (0.65) a #91
- `1971-08-15` **Choque de Nixon: fim da conversibilidade do dólar em ouro** (Estados Unidos) — duplicata: título similar (0.63) a #287
- `1973-10-17` **Primeiro choque do petróleo (embargo da OPAEP)** (Kuwait) — duplicata: título similar (0.89) a #138
- `1997-07-02` **Início da crise financeira asiática (flutuação do baht)** (Tailândia) — duplicata: título similar (0.80) a #167
- `1347-10-01` **Peste Negra chega à Europa (Messina)** (Itália) — duplicata: título similar (0.62) a #16
- `1980-05-08` **OMS declara a erradicação da varíola** (Suíça) — duplicata: título similar (0.67) a #310
- `1954-08-24` **Suicídio de Getúlio Vargas** (Brasil) — duplicata: título similar (0.62) a #273
- `2023-01-08` **Ataques de 8 de janeiro em Brasília** (Brasil) — duplicata: título similar (0.66) a #193
- `1961-04-17` **Invasão da Baía dos Porcos** (Cuba) — duplicata: título similar (0.71) a #277
- `1687-07-05` **Newton publica os 'Principia Mathematica'** (Reino Unido) — duplicata: título similar (0.70) a #36
- `1859-11-24` **Darwin publica 'A Origem das Espécies'** (Reino Unido) — duplicata: título similar (0.65) a #57
- `1869-11-17` **Inauguração do Canal de Suez** (Egito) — duplicata: título similar (1.00) a #62
- `1942-12-02` **Chicago Pile-1: primeira reação nuclear em cadeia controlada** (Estados Unidos) — duplicata: título similar (0.75) a #261
- `1945-07-16` **Teste Trinity: primeira explosão nuclear** (Estados Unidos) — duplicata: título similar (0.70) a #106
- `1946-02-14` **Apresentação pública do ENIAC** (Estados Unidos) — duplicata: título similar (0.61) a #266
- `1947-12-23` **Demonstração do transistor nos Bell Labs** (Estados Unidos) — duplicata: título similar (0.85) a #267
- `1955-04-12` **Anúncio da eficácia da vacina Salk contra a poliomielite** (Estados Unidos) — duplicata: título similar (0.64) a #309
- `1969-10-29` **Primeira mensagem da ARPANET** (Estados Unidos) — duplicata: título similar (0.62) a #286
- `1971-11-15` **Intel lança o microprocessador 4004** (Estados Unidos) — duplicata: título similar (0.61) a #288
- `2000-06-26` **Anúncio do rascunho do genoma humano** (Estados Unidos) — duplicata: título similar (0.63) a #170
- `1807-03-25` **Abolição do tráfico de escravizados no Império Britânico** (Reino Unido) — duplicata: título similar (0.70) a #307
- `1863-01-01` **Proclamação de Emancipação de Lincoln** (Estados Unidos) — duplicata: título similar (0.84) a #59
- `1896-04-06` **Primeiros Jogos Olímpicos da Era Moderna** (Grécia) — duplicata: título similar (0.79) a #73
- `1963-08-28` **Marcha sobre Washington ('I Have a Dream')** (Estados Unidos) — duplicata: título similar (0.68) a #126
- `1968-05-03` **Maio de 1968: início das ocupações estudantis em Paris** (França) — duplicata: título similar (0.63) a #132
- `1969-08-15` **Festival de Woodstock** (Estados Unidos) — duplicata: título similar (1.00) a #135
- `1988-10-05` **Promulgação da Constituição Cidadã** (Brasil) — duplicata: título similar (0.78) a #154
- `1990-02-11` **Libertação de Nelson Mandela** (África do Sul) — duplicata: título similar (0.71) a #157
- `1960-04-21` **Inauguração de Brasília** (Brasil) — duplicata: título similar (0.62) a #122

## ncei_significant_earthquakes — 2026-11-06 (44 excluídos)

- `1605-02-03` **Terremoto de Enshunada (M 7.9)** (Japão) — duplicata: título similar (0.80) a #1680
- `1707-10-28` **Terremoto de Nankaido (M 8.4)** (Japão) — duplicata: título similar (0.80) a #1714
- `1725-01-08` **Terremoto de Arequipa (M 7.6)** (Peru) — duplicata: título similar (0.64) a #1722
- `1755-11-01` **Terremoto de Lisbon (M 8.5)** (Portugal) — duplicata: título similar (0.59) a #39
- `1819-04-04` **Terremoto de Copiapo (M 8)** (Chile) — duplicata: título similar (1.00) a #1758
- `1854-12-24` **Terremoto de Nankaido (M 8.4)** (Japão) — duplicata: título similar (0.71) a #1798
- `1868-08-16` **Terremoto de San Pablo (M 7.7)** (Equador) — duplicata: título similar (0.66) a #1812
- `1897-09-21` **Terremoto de Mindanao, Zamboanga, Sulu, Isabela (M 8.7)** (Filipinas) — duplicata: título similar (0.58) a #1849
- `1899-09-10` **Terremoto de Se Alaska (M 8.2)** (Estados Unidos) — duplicata: título similar (0.73) a #1857
- `1901-08-09` **Terremoto de Off Northeast Coast Honshu (M 8.2)** (Japão) — duplicata: título similar (0.96) a #1869
- `1904-04-04` **Terremoto de Struma (M 7.8)** (Bulgária) — duplicata: título similar (0.96) a #1893
- `1904-06-25` **Terremoto de Off Kamchatka (M 8.1)** (Rússia) — duplicata: título similar (0.97) a #1895
- `1908-03-27` **Terremoto de Guerrero (M 7.5)** (México) — duplicata: título similar (0.93) a #1939
- `1916-01-13` **Terremoto de Irian Jaya (M 8.1)** (Indonésia) — duplicata: título similar (1.00) a #1997
- `1919-01-01` **Terremoto de Fiji Islands (M 7.8)** (Fiji) — duplicata: título similar (0.56) a #826
- `1923-09-02` **Terremoto de Near S Coast Honshu (M 7.7)** (Japão) — duplicata: título similar (0.56) a #2050
- `1937-01-07` **Terremoto de Qinghai Province (M 7.5)** (China) — duplicata: título similar (0.56) a #798
- `1938-11-05` **Terremoto de Near E Coast Honshu (M 7.6)** (Japão) — duplicata: título similar (0.97) a #2111
- `1938-11-06` **Terremoto de Off East Coast Honshu (M 7.5)** (Japão) — duplicata: título similar (0.85) a #2111
- `1946-09-12` **Terremoto de Myanmar (Burma) (M 7.8)** (Mianmar) — duplicata: título similar (0.97) a #2151
- `1949-12-17` **Terremoto de Tierra Del Fuego (M 7.8)** (Chile) — duplicata: título similar (1.00) a #2166
- `1951-11-24` **Terremoto de Taiwan (M 7.5)** (Taiwan) — duplicata: título similar (0.64) a #771
- `1960-05-22` **Terremoto de Puerto Montt, Valdivia (M 9.5)** (Chile) — duplicata: título similar (0.67) a #2217
- `1968-05-16` **Terremoto de Off Coast Of Honshu Island (M 7.5)** (Japão) — duplicata: título similar (0.91) a #2245
- `1972-01-25` **Terremoto de Taiwan (M 7.7)** (Taiwan) — duplicata: título similar (0.96) a #2267
- `1975-07-20` **Terremoto de Buin, Boku (M 7.7)** (Papua-Nova Guiné) — duplicata: título similar (0.75) a #2281
- `1975-10-11` **Terremoto de S Of Tonga (M 7.8)** (Tonga) — duplicata: título similar (0.65) a #737
- `1976-01-14` **Terremoto de Kermadec Islands (M 7.9)** (Kermadec Islands (New Zealand)) — duplicata: título similar (0.97) a #2285
- `1977-04-21` **Terremoto de Solomon Islands (M 8.1)** (Ilhas Salomão) — duplicata: título similar (0.94) a #2291
- `1978-03-24` **Terremoto de Kuril Islands (M 7.6)** (Rússia) — duplicata: título similar (0.97) a #2295
- `1995-07-30` **Terremoto de Antofagasta, Calama, Mejillones (M 8)** (Chile) — duplicata: título similar (0.57) a #717
- `2000-11-16` **Terremoto de New Ireland, New Britain (M 7.8)** (Papua-Nova Guiné) — duplicata: título similar (0.77) a #2375
- `2000-11-17` **Terremoto de New Britain (M 7.8)** (Papua-Nova Guiné) — duplicata: título similar (0.68) a #2375
- `1977-04-20` **Terremoto de Solomon Islands (M 7.6)** (Ilhas Salomão) — duplicata: título similar (0.97) a #2291
- `1498-09-20` **Terremoto de Enshunada Sea (M 8.3)** (Japão) — duplicata: título similar (0.68) a #1657
- `2007-09-12` **Terremoto de Sumatra (M 7.9)** (Indonésia) — duplicata: título similar (0.92) a #2461
- `2002-08-19` **Terremoto de Fiji Islands (M 7.7)** (Fiji) — duplicata: título similar (1.00) a #2478
- `2011-03-11` **Terremoto de Near E Coast Honshu (M 7.9)** (Japão) — duplicata: título similar (0.73) a #2490
- `2011-03-11` **Terremoto de Off East Coast Honshu (M 7.6)** (Japão) — duplicata: título similar (0.71) a #2490
- `2012-04-11` **Terremoto de Off West Coast (M 8.2)** (Indonésia) — duplicata: título similar (0.97) a #2493
- `1868-08-14` **Terremoto de Arica (M 8.5)** (Chile) — duplicata: título similar (1.00) a #1811
- `2015-11-24` **Terremoto de Peru-Brazil (M 7.6)** (Peru) — duplicata: título similar (1.00) a #2521
- `2021-08-12` **Terremoto de South Sandwich Islands (M 8.1)** (South Georgia And The South Sandwich Islands) — duplicata: título similar (0.95) a #2554
- `2023-02-06` **Terremoto de Turkey; Syria (M 7.5)** (Turquia) — duplicata: título similar (0.72) a #2560

## wikidata_events — 2026-11-06 (66 excluídos)

- `0378-08-10` **Batalha de Adrianópolis** (Turquia) — duplicata: título similar (1.00) a #1363
- `-0338-08-01` **Batalha de Queroneia** (Grécia) — duplicata: título similar (0.60) a #1352
- `1757-06-23` **Batalha de Plassey** (Índia) — duplicata: título similar (1.00) a #1392
- `1876-06-25` **Batalha de Little Bighorn** (Estados Unidos) — duplicata: título similar (1.00) a #221
- `1862-07-01` **Segunda Batalha de Bull Run** (Estados Unidos) — duplicata: título similar (0.80) a #2749
- `0312-10-29` **Batalha da Ponte Mílvia** (Itália) — duplicata: título similar (0.63) a #1361
- `1941-12-07` **Ataque a Pearl Harbor** (Estados Unidos) — duplicata: título similar (0.84) a #101
- `0009-09-01` **Batalha da Floresta de Teutoburgo** (Alemanha) — duplicata: título similar (1.00) a #1359
- `-0218-12-01` **Batalha do Trébia** (Itália) — duplicata: título similar (0.74) a #2765
- `1824-12-09` **Batalha de Ayacucho** (Peru) — duplicata: título similar (1.00) a #1401
- `1805-12-02` **Batalha de Austerlitz** (Chéquia) — duplicata: título similar (1.00) a #1398
- `0451-06-21` **Batalha dos Campos Cataláunicos** (França) — duplicata: título similar (0.83) a #1365
- `1812-07-01` **Batalha de Smolensk** (Rússia) — duplicata: título similar (0.68) a #2728
- `1066-09-26` **Batalha de Fulford** (Reino Unido) — duplicata: título similar (0.68) a #2737
- `1819-08-07` **Batalha de Boyacá** (Colômbia) — duplicata: título similar (1.00) a #1400
- `1862-07-01` **Batalha de Fredericksburg** (Estados Unidos) — duplicata: título similar (0.64) a #2847
- `-0279-07-01` **Batalha de Ásculo** (Itália) — duplicata: título similar (0.76) a #2994
- `2022-07-01` **Batalha de Sievierodonetsk** (Ucrânia) — duplicata: título similar (0.56) a #3031
- `-0480-07-01` **Batalha de Artemísio** (Grécia) — duplicata: título similar (0.71) a #2853
- `1805-10-21` **Batalha de Trafalgar** (Espanha) — duplicata: título similar (1.00) a #48
- `-0260-07-01` **Batalha de Mylae** (Itália) — duplicata: título similar (0.72) a #2836
- `2022-02-24` **Batalha de Sumy** (Ucrânia) — duplicata: título similar (0.56) a #3031
- `2022-02-24` **Batalha de Chernigov** (Ucrânia) — duplicata: título similar (0.71) a #3031
- `1938-09-30` **Acordo de Munique** (Alemanha) — duplicata: título similar (1.00) a #1417
- `1918-11-11` **Armistício de Compiègne** (França) — duplicata: título similar (0.60) a #87
- `1945-09-02` **Rendição do Japão** (Império do Japão) — duplicata: título similar (0.83) a #3141
- `1945-06-26` **Carta das Nações Unidas** (Estados Unidos) — duplicata: título similar (0.77) a #1418
- `1776-07-04` **Declaração da Independência dos Estados Unidos** (Estados Unidos) — duplicata: título similar (0.98) a #41
- `1948-05-14` **Declaração de Independência do Estado de Israel** (Palestina) — duplicata: título similar (1.00) a #112
- `2021-09-05` **Golpe de Estado na Guiné em 2021** (Guiné) — duplicata: título similar (0.82) a #1093
- `2021-10-25` **Golpe de Estado no Sudão em 2021** (Sudão) — duplicata: título similar (0.82) a #1235
- `2023-07-26` **Golpe de Estado no Níger em 2023** (Níger) — duplicata: título similar (0.82) a #1083
- `2013-07-03` **Golpe de Estado no Egito em 2013** (Egito) — duplicata: título similar (0.82) a #1256
- `2014-05-22` **Golpe de Estado na Tailândia em 2014** (Tailândia) — duplicata: título similar (0.84) a #1313
- `2020-08-18` **Golpe de Estado no Mali em 2020** (Mali) — duplicata: título similar (0.81) a #1057
- `2023-01-08` **Ataques de 8 de janeiro em Brasília** (Brasil) — duplicata: título similar (0.66) a #193
- `2017-11-14` **Golpe de Estado no Zimbabwe em 2017** (Zimbábue) — duplicata: título similar (0.81) a #1192
- `2021-01-06` **Invasão do Capitólio dos Estados Unidos em 2021** (Estados Unidos) — duplicata: título similar (0.86) a #190
- `1968-10-02` **Massacre de Tlatelolco** (México) — duplicata: título similar (1.00) a #1528
- `1989-07-01` **Massacre da Praça da Paz Celestial em 1989** (China) — duplicata: título similar (0.84) a #155
- `1890-12-29` **Massacre de Wounded Knee** (Estados Unidos) — duplicata: título similar (0.96) a #224
- `1770-03-05` **Massacre de Boston** (Estados Unidos) — duplicata: título similar (0.95) a #211
- `1906-04-18` **Sismo de São Francisco de 1906** (Estados Unidos) — duplicata: título similar (0.68) a #1917
- `1976-07-28` **Sismo de Tangshan de 1976** (China) — duplicata: título similar (0.65) a #2287
- `2001-01-26` **Terremoto de Gujarat em 2001** (Índia) — duplicata: título similar (0.56) a #2377
- `2025-07-30` **Sismo de Kamchatka de 2025** (Rússia) — duplicata: título similar (0.56) a #2568
- `2020-01-23` **Pandemia de COVID-19 no Nepal** (Nepal) — duplicata: título similar (0.85) a #3332
- `2020-01-30` **pandemia de COVID-19 nas Filipinas** (Filipinas) — duplicata: título similar (0.86) a #3337
- `2020-01-31` **Pandemia de COVID-19 na Suécia** (Suécia) — duplicata: título similar (0.88) a #3337
- `2020-01-31` **Pandemia de COVID-19 na Rússia** (Rússia) — duplicata: título similar (0.88) a #3337
- `2020-01-31` **pandemia de COVID-19 em Espanha** (Espanha) — duplicata: título similar (0.85) a #3338
- `2020-02-26` **Pandemia de COVID-19 na Noruega** (Noruega) — duplicata: título similar (0.87) a #3345
- `2020-02-14` **Surto de coronavírus em 2020 no Egito** (Egito) — duplicata: título similar (0.61) a #3344
- `2020-03-03` **Pandemia de COVID-19 na Ucrânia** (Ucrânia) — duplicata: título similar (0.90) a #3350
- `2020-02-25` **Pandemia de COVID-19 na Croácia** (Croácia) — duplicata: título similar (0.87) a #3345
- `2020-02-26` **Pandemia de COVID-19 na Roménia** (Roménia) — duplicata: título similar (0.87) a #3345
- `2020-02-26` **Pandemia de COVID-19 na Geórgia** (Geórgia) — duplicata: título similar (0.87) a #3345
- `2020-03-06` **pandemia de COVID-19 no Peru** (Peru) — duplicata: título similar (0.86) a #3352
- `2020-02-26` **pandemia de COVID-19 no Paquistão** (Paquistão) — duplicata: título similar (0.88) a #3348
- `1963-11-22` **assassinato de John F. Kennedy** (Estados Unidos) — duplicata: título similar (0.73) a #127
- `1968-04-04` **assassinato de Martin Luther King Jr.** (Estados Unidos) — duplicata: título similar (0.74) a #284
- `1865-04-15` **assassinato de Abraham Lincoln** (Estados Unidos) — duplicata: título similar (1.00) a #60
- `1948-01-30` **Assassinato de Mahatma Gandhi** (Domínio da Índia) — duplicata: título similar (0.75) a #268
- `1871-03-18` **Comuna de Paris** (França) — duplicata: título similar (0.94) a #64
- `1943-04-19` **Levante do Gueto de Varsóvia** (Polónia) — duplicata: título similar (0.67) a #262
- `1707-12-01` **Erupção do Monte Fuji de 1707** (Japão) — duplicata: título similar (0.68) a #2654
