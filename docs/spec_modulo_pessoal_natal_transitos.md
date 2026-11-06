# Especificação Técnica — Módulo Pessoal: Mapa Natal, Trânsitos de Vida e Progressões Secundárias

**Data:** 06/11/2026
**Status:** PROPOSTA — nada implementado.
**Contexto:** Frente D do [`plano_v6_roadmap.md`](plano_v6_roadmap.md). Fases 4 (MVP), 5 (progressões) e 6 (interpretações).
**Base:** astrologia moderna ocidental (zodíaco tropical, planetas transaturninos, regências modernas, leitura psicológica/arquetípica).

---

## 1. Objetivo e escopo

**Objetivo.** Permitir que uma pessoa informe data, hora e local de nascimento e receba: (1) o mapa natal calculado com a mesma precisão do motor atual; (2) a lista completa e datada de todos os trânsitos relevantes sobre o mapa natal ao longo de toda a vida, organizados por período, planeta e domínio de vida; (3) as progressões secundárias, com a Lua progredida como fio condutor; (4) opcionalmente, os trânsitos calculados sobre o mapa progredido.

**Dentro do escopo (v6.0):**
- Carta natal completa (planetas, pontos, casas, ângulos, aspectos natais, elementos/modalidades, estrelas fixas em conjunção).
- Trânsitos ao natal, nascimento → 100 anos (ou intervalo escolhido), com datas exatas por passagem.
- Ciclos de vida (retornos e aspectos genéricos de idade).
- Classificação por 8 domínios de vida e intensidade mensal calibrada.
- Progressões secundárias: carta progredida em data qualquer, linha do tempo da Lua progredida, ingressos de Sol/planetas progredidos, aspectos progredido→natal.
- Modo "trânsitos ao mapa progredido".
- Hora de nascimento desconhecida tratada explicitamente.
- Exportação CSV, ICS (calendário) e JSON; permalink.
- PT/EN; três temas.

**Fora do escopo (v6.x futuro):** sinastria/composto, retornos solares/lunares como cartas completas, eclipses sobre pontos natais, direções de arco solar, retificação de hora, zodíaco sideral, contas de usuário.

---

## 2. Fundamentos astrológicos adotados

| Tema | Decisão | Opções expostas ao usuário |
| :--- | :--- | :--- |
| Zodíaco | Tropical | — |
| Casas | Placidus (padrão) | Koch, Signos Inteiros, Igual (ASC), Porphyry; fallback polar automático como hoje |
| Corpos natais | Sol, Lua, Mercúrio, Vênus, Marte, Júpiter, Saturno, Urano, Netuno, Plutão, Quíron, Nodo Norte **verdadeiro**, Lilith média, ASC, MC, DSC, IC | Asteroides (Ceres, Pallas, Juno, Vesta) ligáveis |
| Corpos em trânsito | Sol, Mercúrio, Vênus, Marte, Júpiter, Saturno, Urano, Netuno, Plutão, Quíron, Nodo Norte **médio** | Lua em trânsito **desligada por padrão** (ligável; orbe 3°, apenas conjunção/oposição, para consultas de curto prazo); Lilith e asteroides em trânsito desligados |
| Aspectos | Conjunção 0°, Oposição 180°, Quadratura 90°, Trígono 120°, Sextil 60° | Menores (Quincúncio 150°, Semiquadratura 45°, Sesquiquadratura 135°, Semissextil 30°) com 50% da orbe, desligados por padrão |
| Orbes em trânsito | Por **planeta em trânsito** (tabela abaixo) | Presets *Estrito* (×0,7), *Padrão* (×1,0), *Amplo* (×1,3) e edição manual |
| Bônus de alvo | +0,5° quando o ponto natal é Sol, Lua, ASC ou MC | Ligado por padrão |
| Regências | Modernas (Urano/Aquário, Netuno/Peixes, Plutão/Escorpião), já em `ZODIAC_SIGNS` | — |
| Progressões | Secundárias, 1 dia = 1 ano trópico (365,24219 d) | Ano juliano (365,25 d) |
| Ângulos progredidos | MC por **arco solar** (MC_p = MC_n + (☉_p − ☉_n)); ASC_p derivado do MC_p com a latitude natal | Naibod em AR (0°59′08″/ano) |
| Lua progredida | Alvo e agente central das progressões; orbe 1,0° para aspectos ao natal | — |

### 2.1 Tabela de orbes padrão (`config/natal.yaml`)

| Planeta em trânsito | Orbe máxima | Justificativa |
| :--- | ---: | :--- |
| Plutão | 1,0° | Lento; janela já dura 1–3 anos com 1° |
| Netuno | 1,0° | idem |
| Urano | 1,0° | idem |
| Saturno | 1,5° | Janela ~9–12 meses com passagens retrógradas |
| Quíron | 1,0° | Lento e irregular |
| Nodo Norte médio | 1,5° | Movimento retrógrado regular (~19°/ano) |
| Júpiter | 2,0° | Janela ~3–6 semanas por passagem |
| Marte | 3,0° | Janela ~1 semana; 3 passagens em retrogradação |
| Sol | 4,0° | Janela ~8 dias; gatilho de curto prazo |
| Mercúrio | 4,0° | idem; retrogradações frequentes |
| Vênus | 4,0° | idem (ver pergunta aberta: 3°?) |
| Lua (se ligada) | 3,0° | Só conjunção/oposição; janelas de horas |

Para aspectos menores: 50% dos valores. Para alvos Sol/Lua/ASC/MC: +0,5°.

---

## 3. Entradas

### 3.1 Formulário (`/natal`)

| Campo | Tipo | Validação | Observação |
| :--- | :--- | :--- | :--- |
| `label` | texto ≤ 60 | opcional | Nome/apelido só para exibição; nunca logado |
| `date` | `YYYY-MM-DD` | 1850–2100 (fora disso: cálculo on-the-fly mais lento, aviso) | Gregoriano |
| `time` | `HH:MM` | obrigatório se `time_known=1` | Hora local civil |
| `time_known` | 0/1 | — | 0 → modo "sem hora" (§6.4) |
| `place_id` | id do gazetteer | **ou** `lat`/`lon` manuais | Autocomplete offline (§5.2) |
| `lat`, `lon` | decimal | −90..90 / −180..180 | Preenchidos pelo gazetteer; editáveis |
| `tz` | IANA | derivado de lat/lon (`timezonefinder`) | Editável (ex.: nascimento em navio) |
| `house_system` | enum | P/K/W/E/O | Padrão P |
| `orb_preset` | enum | strict/standard/wide/custom | Padrão standard |
| `orbs` | JSON compacto | só se custom | — |
| `bodies` | lista | subconjunto permitido | Asteroides, Lilith, Lua em trânsito |
| `aspects` | lista | majors (+ minors) | — |
| `target_mode` | enum | `natal` / `progressed` | Padrão natal |
| `range` | `from,to` (anos ou idades) | dentro de nascimento → +100 | Padrão: vida inteira |
| `lang` | pt/en | — | — |

Submissão `POST /natal` → `303` para `GET /natal/transits?...` (mesmo padrão do Simulador: resultado compartilhável e recarregável).

### 3.2 Privacidade (LGPD)

- Dados de nascimento são dados pessoais. O servidor **não persiste** nada: sem banco, sem arquivo, sem cache em disco. Cache apenas em memória (LRU, chave = SHA-256 dos parâmetros, TTL 10 min).
- `uvicorn --no-access-log`; nginx com `log_format` que omite `$args` para `/natal/*`.
- Aviso curto no formulário: "Os dados ficam apenas na URL do seu navegador. Não armazenamos nem compartilhamos."
- Botão "Salvar neste navegador" grava a URL em `localStorage` (cliente), com lista de mapas salvos e remoção.
- Rate limit 30 req/min/IP nas rotas `/natal/*`; tamanho máximo da query 4 KB.

---

## 4. Saídas (páginas)

### 4.1 `/natal` — Formulário
Explicação em 3 linhas, formulário (§3.1), exemplos clicáveis (figuras públicas com hora AA do Astrodatabank, ex.: Albert Einstein 14/03/1879 11:30 LMT Ulm), aviso de privacidade, enquadramento epistêmico (§14).

### 4.2 `/natal/chart` — Mapa natal
- Roda SVG (reuso de `src/web/mandala.py`, estendido com casas, ângulos, linhas de aspecto coloridas por natureza, legenda).
- Tabela de posições (longitude, signo, grau, casa, velocidade, retrógrado), tabela de casas, tabela de aspectos natais com orbe e aplicativo/separativo.
- Resumo: elementos, modalidades, hemisférios, dominâncias, estrelas fixas em conjunção (orbe 0,3° — mesmo motor).
- Selo de precisão (`Hora exata` / `Sem hora — meio-dia, sem casas`).
- Bloco "Como ler este mapa" (glossário embutido).
- Abas → Trânsitos da Vida, Progressões.

### 4.3 `/natal/transits` — Trânsitos da Vida
Seções, de cima para baixo:
1. **Agora** — trânsitos ativos hoje e nos próximos 12 meses, com próximas datas exatas.
2. **Linha da vida** — gráfico interativo (D3): eixo X = anos/idades; faixas (lanes) por planeta em trânsito; barras = janelas em orbe; marcadores = passagens exatas (● direto, ◐ retrógrado); cor = tom (desafiador/fluido/foco); hover com detalhes; zoom e brush por década.
3. **Mapa de calor da vida** — anos (X) × 8 domínios (Y), intensidade 0–1000; clique abre o ano.
4. **Anos-chave** — top 10 picos de intensidade total, com os 3 trânsitos que mais contribuem.
5. **Ciclos de vida** — retornos e aspectos genéricos com idades e datas exatas.
6. **Lista detalhada** — agrupada por ano → mês → trânsito; cada item: planeta ☌/□/△ ponto natal, orbe máxima, janela (início–fim), passagens exatas (datas e R), aplicativo/separativo, duração, domínios, tom, texto interpretativo (colapsável).
7. **Filtros** (barra lateral fixa): planeta, ponto natal, aspecto, domínio, tom, intensidade mínima, só exatos, só ativos agora, intervalo de anos.
8. **Exportar**: CSV (janelas + passagens), ICS (passagens exatas como eventos de dia inteiro; janelas como eventos multi-dia opcionais), JSON, Imprimir/PDF (CSS de impressão).

### 4.4 `/natal/progressions` — Progressões
1. **Carta progredida em uma data** (seletor de data, padrão hoje): biwheel natal (interno) × progredido (externo), reuso de `mandala_biwheel.py`; tabela de posições progredidas; aspectos progredido→natal com orbe 1°.
2. **Linha do tempo da Lua progredida**: signos (ingressos com datas), casas natais (ingressos), fases da lunação progredida (Nova, Crescente, Quarto, Gibosa, Cheia, Disseminadora, Balsâmica — a cada 45°), aspectos exatos ao natal.
3. **Ingressos progredidos**: mudanças de signo do Sol, Mercúrio, Vênus, Marte progredidos; estações (direto↔retrógrado) de Mercúrio/Vênus/Marte progredidos; mudanças de signo de ASC/MC progredidos (se hora conhecida).
4. **Modo "trânsitos ao mapa progredido"** (toggle que replica §4.3 com `target_mode=progressed`).

---

## 5. Arquitetura

### 5.1 Módulos

```
src/natal/
  __init__.py
  models.py            # dataclasses/pydantic: BirthData, NatalChart, TransitWindow, Hit, ProgressionEvent
  gazetteer.py         # busca de cidades (SQLite FTS5) + resolução de fuso
  ephemeris_cache.py   # grade diária 1850–2150: longitudes e velocidades dos corpos em trânsito (npz, lazy, memória)
  chart.py             # calculate_natal_chart(BirthData, options) -> NatalChart  (reusa src.astro_engine)
  transits.py          # scan_transits(targets(t), options) -> [TransitWindow]  (núcleo vetorizado)
  cycles.py            # rotulagem de retornos/ciclos genéricos
  progressions.py      # posições progredidas, Lua progredida, ingressos, trânsitos ao progredido
  domains.py           # classificação por domínios, intensidade mensal, calibração, picos
  interpretations.py   # composição de textos a partir de data/interpretations/*.yaml
  exports.py           # CSV / ICS / JSON
  web_routes.py        # APIRouter: /natal, /natal/chart, /natal/transits, /natal/progressions, /api/natal/*
config/natal.yaml
config/natal_domains.yaml
data/gazetteer/cities.sqlite            # gerado por scripts/build_gazetteer.py (GeoNames cities15000, CC BY 4.0)
data/ephemeris/natal_grid_1850_2150.npz # gerado por scripts/build_natal_grid.py
data/interpretations/{transits,progressions,cycles}.{pt,en}.yaml
data/calibration/natal_domains_reference.json   # distribuição de referência (população sintética)
src/web/templates/natal/{form,chart,transits,progressions}.html
tests/natal/test_{gazetteer,chart,transits,cycles,progressions,domains,exports,routes,performance}.py
```

Integração: `src/web/app.py` inclui o router (`app.include_router(natal_router)`), como já faz com `src/mundane/web_routes.py`. Middleware de segurança continua bloqueando `/api/natal/*` para tráfego externo; as páginas HTML são públicas (com rate limit).

### 5.2 Gazetteer offline

- Fonte: GeoNames `cities15000.txt` (~25 mil cidades, CC BY 4.0) + `admin1CodesASCII.txt` + `countryInfo.txt`. Opcional `cities500` (~200 mil) se o tamanho (≈ 40 MB) for aceitável.
- Build: `scripts/build_gazetteer.py` → SQLite com tabela `cities(id, name, ascii_name, alt_names, country_code, country_name_pt, country_name_en, admin1, lat, lon, population, tz)` + índice FTS5 em `name, ascii_name, alt_names`.
- Busca: prefixo e fuzzy leve (`unidecode`), ordenação por população; retorna 8 resultados; endpoint interno `/natal/places?q=` (HTML fragment/JSON same-origin, não sob `/api/`, com rate limit).
- Fuso: coluna `tz` do GeoNames (confiável); fallback `timezonefinder` para coordenadas manuais. Conversão local→UT via `zoneinfo` com histórico de DST; antes da primeira transição do fuso → LMT pela longitude (mesma regra proposta na Frente B).

### 5.3 Grade de efemérides para trânsitos

- `scripts/build_natal_grid.py`: para cada dia 1850-01-01 → 2150-12-31 (≈ 109.900 dias), 0h UT, calcula longitude e velocidade de Sol, Mercúrio, Vênus, Marte, Júpiter, Saturno, Urano, Netuno, Plutão, Quíron, Nodo médio (+ Lua, Lilith, asteroides opcionais em arquivo separado).
- Formato: `npz` com `jd (float64[N])`, `lon (float32[N, B])`, `speed (float32[N, B])`, `body_ids`. ≈ 110 k × 11 × 2 × 4 B ≈ 9,7 MB (≈ 15 MB com opcionais).
- Carregamento lazy em `ephemeris_cache.get_grid()`, singleton em memória.
- Fora do intervalo da grade (nascimento < 1850 ou horizonte > 2150): fallback on-the-fly com `swe.calc_ut` por dia (aviso de lentidão).

---

## 6. Algoritmos

### 6.1 Carta natal

Reuso direto: `resolve_event_instant` (local→UT, calendário), `calculate_natal_bodies`, `calculate_houses` (estendido para receber `house_system`), `calculate_strict_aspects` (parametrizado com orbes natais de `natal.yaml`, p.ex. 8° luminares/6° planetas/3° pontos — convenção moderna), `calculate_fixed_stars`/`calculate_fixed_star_aspects`. Acrescentar DSC/IC (ASC+180, MC+180) e posição de cada corpo em casa.

### 6.2 Varredura de trânsitos (núcleo)

Definições:
- Alvo `P` com longitude `L_P(t)` (constante no modo natal; função do tempo no modo progredido).
- Corpo em trânsito `T` com longitude `L_T(t)` e velocidade `v_T(t)` da grade.
- Aspecto `A ∈ {0, 60, 90, 120, 180}` (e menores opcionais). Para `A ∉ {0, 180}` verificar `A` e `360 − A`.
- Desvio: `δ(t) = wrap180(L_T(t) − L_P(t) − A)`, onde `wrap180(x) = ((x + 180) mod 360) − 180`.
- Orbe efetiva: `o = orb[T] × preset_factor + bonus(P)`.

Pseudocódigo (por corpo em trânsito, vetorizado em numpy sobre o eixo do tempo):

```
for T in transiting_bodies:
    LT, vT = grid.lon[:, T], grid.speed[:, T]              # [N]
    for P in targets:
        LP = targets.lon(P, grid.jd)                        # [N] (constante ou progredido interpolado)
        for A in aspect_angles(P):
            for a in ({A} if A in (0,180) else {A, 360-A}):
                d = wrap180(LT - LP - a)                    # [N]
                inorb = abs(d) <= o(T, P, A)                # [N] bool
                runs = contiguous_true_runs(inorb)          # [(i0, i1)]
                for (i0, i1) in runs:
                    sign_changes = where(sign(d[i0:i1]) != sign(d[i0+1:i1+1]))
                    hits = [refine(T, P, a, jd[i], jd[i+1]) for i in sign_changes]   # bisseção com swe.calc_ut
                    windows.append(TransitWindow(T, P, A, jd[i0], jd[i1], hits,
                                   applying_at_start = sign(d[i0]) != sign(vT[i0] - vP),
                                   n_passes = len(hits), max_intensity = peak(d, o)))
```

Detalhes:
- **Refinamento**: bisseção em `[jd_i, jd_{i+1}]` até 1 minuto (≈ 11 iterações) com `swe.calc_ut`; para corpos rápidos a interpolação linear diária já erra < 1 h. Custo total: ~3–6 mil hits × 11 chamadas ≈ 50 k chamadas ≈ 0,3–0,5 s. Opção `refine=fast` (interpolação) para o preview.
- **Passagens retrógradas**: `n_passes` ∈ {1, 3, 5}; cada hit carrega `retrograde = vT(hit) < 0`.
- **Janelas fragmentadas**: se o corpo sai da orbe e volta em < 10 dias (lentos) o scanner **funde** as janelas e marca `gap_days`.
- **Aplicativo/separativo**: sinal de `d · (vT − vP)` avaliado em cada dia; o painel "Agora" usa o valor do dia corrente.
- **Casas em trânsito**: ingresso de corpos lentos (Júpiter → Plutão, Nodo, Quíron) nas 12 casas natais: datas exatas por mudança de casa, com reentradas retrógradas.
- **Retornos**: quando `T == P` e `A == 0` o item recebe `cycle_label` (§6.5).

Complexidade: por vida inteira (36.525 dias) × 11 corpos × 16 alvos × 8 ângulos ≈ 51 M operações vetorizadas → ≈ 0,2–0,4 s em numpy; total com refinamento < 1,5 s (budget testado em CI).

### 6.3 Interpolação de alvos progredidos (modo `progressed`)

- Calcular posições progredidas **mensalmente** (1.200 pontos para 100 anos) com `swe.calc_ut(jd_birth + age_years)` e interpolar linearmente para o eixo diário (Lua progredida move ~1°/mês → erro de interpolação < 0,02°).
- Mesmo scanner de §6.2 com `LP(t)` variável. Alvos progredidos permitidos: todos os planetas, Lua progredida, ASC/MC progredidos (se hora conhecida).

### 6.4 Hora de nascimento desconhecida

- Carta ao **meio-dia local**, sem casas, sem ASC/MC/DSC/IC; `houses_available = false`.
- Lua natal: calcular às 00:00 e 23:59 locais → faixa `[L_min, L_max]` (≈ 12–15°). Trânsitos à Lua natal são calculados sobre o centro da faixa e marcados `approx = true`, com orbe efetiva ampliada por metade da amplitude; a UI exibe "≈" e um aviso.
- Domínios: casas não participam da classificação (apenas planeta × ponto).
- Progressões: Lua progredida herda a incerteza (faixa deslocada); ângulos progredidos indisponíveis.
- Opção "intervalo de horas provável" (ex.: 06:00–12:00) para estreitar a faixa.

### 6.5 Ciclos de vida (`cycles.py`)

| Ciclo | Detecção | Idades típicas |
| :--- | :--- | :--- |
| Retorno de Júpiter | ♃ ☌ ♃ natal | 12, 24, 36, 48, 60, 72, 84, 96 |
| Retorno de Saturno | ♄ ☌ ♄ natal | ~29,5; ~59; ~88 |
| Quadraturas/oposição de Saturno | ♄ □/☍ ♄ natal | ~7, 14–15, 21–22, 36–37, 44, 51… |
| Retorno nodal / nodal inverso | ☊ médio ☌/☍ ☊ natal | 18,6 / 9,3 + múltiplos |
| Oposição de Urano | ♅ ☍ ♅ natal | ~40–42 |
| Quadraturas de Urano | ♅ □ ♅ natal | ~21, ~63 |
| Quadratura de Netuno | ♆ □ ♆ natal | ~41 |
| Quadratura de Plutão | ♇ □ ♇ natal | variável (36–60 por geração) |
| Retorno de Quíron | ⚷ ☌ ⚷ natal | ~50 |
| Retorno solar (datas) | ☉ ☌ ☉ natal | anual (lista de datas exatas) |

Rótulos e textos específicos em `data/interpretations/cycles.*.yaml`.

### 6.6 Progressões secundárias (`progressions.py`)

- Idade em anos trópicos: `age = (jd_t − jd_birth) / 365.24219`; `jd_prog = jd_birth + age`.
- Posições progredidas: `swe.calc_ut(jd_prog, body)` para todos os corpos natais.
- MC progredido: `MC_p = MC_n + (☉_p − ☉_n)` (arco solar); opção Naibod: `MC_p = MC_n + age × 0.98565°` (convertido via AR). ASC_p: converter `MC_p` em ARMC (com obliquidade da data natal) e usar `swe.houses_armc(armc, lat_natal, eps, hsys)` → ASC_p e cúspides progredidas.
- **Lua progredida**: série mensal; ingressos de signo e de casa natal refinados por bisseção (datas exatas); fase = `wrap360(☽_p − ☉_p)` em 8 setores de 45°; aspectos ao natal com orbe 1° (scanner de §6.2 com `T = Lua progredida`, eixo mensal interpolado para diário).
- Ingressos e estações de Sol/Mercúrio/Vênus/Marte progredidos: detectar mudança de signo e `speed` cruzando zero.
- Aspectos progredido→natal para todos os planetas progredidos (orbe 1°, exatos).

### 6.7 Domínios de vida e intensidade (`domains.py`, `config/natal_domains.yaml`)

Separação entre **domínio** (onde na vida — dado pelo ponto natal e pela casa) e **processo** (como — dado pelo planeta em trânsito) e **tom** (dado pelo aspecto).

Domínios (8):

| Chave | Rótulo PT | Pontos natais / casas que o ativam |
| :--- | :--- | :--- |
| `identity` | Identidade, Vitalidade & Direção | Sol, ASC, Marte, casa 1 |
| `home_family` | Emoções, Lar & Família | Lua, IC, casa 4 |
| `mind_learning` | Mente, Estudos & Comunicação | Mercúrio, casas 3 e 9 |
| `relationships` | Amor, Vínculos & Parcerias | Vênus, DSC, casas 5 e 7, Juno |
| `career` | Carreira, Vocação & Reconhecimento | MC, Saturno, casas 10 e 6 |
| `resources` | Finanças & Recursos | casas 2 e 8, Vênus, Júpiter |
| `health_routine` | Saúde, Energia & Rotina | casa 6, Marte, Sol, Quíron |
| `purpose_transformation` | Propósito, Transformação & Interioridade | Júpiter, Netuno, Plutão, Nodo, casas 8, 9 e 12 |

Processos (planeta em trânsito): Expansão (♃), Estruturação/Maturidade (♄), Ruptura/Libertação (♅), Dissolução/Inspiração (♆), Transformação/Poder (♇), Ferida/Cura (⚷), Direção/Destino (☊), Ativação de curto prazo (☉ ☿ ♀ ♂).
Tom (aspecto): desafiador (□ ☍), fluido (△ ⚹), foco/intenso (☌); menores herdam de sua família.

Intensidade de um trânsito no dia `t`:

```
I(t) = w_transit[T] × w_point[P] × w_aspect[A] × (1 − |δ(t)| / o)
```

Pesos padrão (config): `w_transit` ♇ 1,0 · ♆ 0,9 · ♅ 0,9 · ♄ 0,85 · ⚷ 0,6 · ♃ 0,6 · ☊ 0,5 · ♂ 0,4 · ☉ 0,35 · ♀ 0,25 · ☿ 0,2; `w_point` ☉ ☽ ASC 1,0 · MC 0,95 · ♀ ♂ 0,75 · ☿ ♄ 0,7 · ♃ 0,6 · ♅ ♆ ♇ ⚷ ☊ 0,5 · Lilith/asteroides 0,3; `w_aspect` ☌ 1,0 · ☍ 0,9 · □ 0,85 · △ 0,6 · ⚹ 0,45.

Distribuição por domínio: cada ponto natal tem um vetor de pesos sobre os 8 domínios (ex.: Lua → `home_family` 0,7, `identity` 0,3); a casa natal do ponto acrescenta 0,3 ao domínio da casa; renormalizar.

Série mensal: `D[m, k] = Σ_t∈m Σ_trânsitos I(t) × dist_k / dias(m)`.

**Calibração 0–1000**: gerar uma vez 2.000 nascimentos sintéticos (datas uniformes 1940–2010, horas uniformes, cidades amostradas do gazetteer), calcular `D` para cada um, e guardar os quantis globais em `data/calibration/natal_domains_reference.json`. Na exibição, `score_1000 = 1000 × F_ref(D)` — mesma lógica do percentil 1000 do site, tornando comparáveis pessoas e períodos.

**Anos-chave**: máximos locais da soma anual de `D` com proeminência mínima (quantil 80 da referência), listando os 3 trânsitos de maior contribuição.

### 6.8 Interpretações (`interpretations.py`)

Composição em camadas, com fallback garantido:

1. **Texto manual** se existir chave exata `transit.{T}.{aspect_family}.{P}` (≈ 60 prioritários: planetas lentos × {conj, hard, soft} × {Sol, Lua, ASC, MC, Vênus, Marte, Saturno} + retornos).
2. Senão, **template**: `{processo[T].frase} {tom[A].conector} {dominio[P].frase}` + contexto de casa + duração/passagens ("3 passagens entre mar/2031 e dez/2031; exatas em 02/04, 19/08 ℞ e 10/11").
3. Diretrizes de redação: linguagem reflexiva, sem determinismo, sem conselhos médicos/financeiros/jurídicos, sem previsão de eventos concretos; PT e EN equivalentes; autoria original (referências de estilo: Greene, Sasportas, Hand, Forrest — sem cópia).
4. Arquivos: `data/interpretations/transits.pt.yaml` (+ `.en`), `progressions.*.yaml`, `cycles.*.yaml`; teste que garante paridade de chaves PT/EN.

### 6.9 Exportações (`exports.py`)

- **CSV**: uma linha por janela (`transit, aspect, natal_point, start, end, passes, exact_dates, orb_max, tone, domains, intensity_peak, age_start`) e um segundo CSV por passagem.
- **ICS**: `VEVENT` de dia inteiro por passagem exata (`SUMMARY: ♄ □ ☉ natal (exato, ℞)`, `DESCRIPTION` com janela, domínios e texto curto); opcional eventos multi-dia por janela de planetas lentos. `UID` determinístico a partir do hash dos parâmetros + índice.
- **JSON**: estrutura de §8 completa.
- **Impressão**: CSS `@media print` com linha da vida em SVG estático e lista compacta.

---

## 7. Configuração

### 7.1 `config/natal.yaml` (esboço)

```yaml
version: 1
zodiac: tropical
house_system_default: P          # P Placidus | K Koch | W Whole Sign | E Equal | O Porphyry
progression:
  year_length_days: 365.24219    # tropical | 365.25 julian
  mc_method: solar_arc           # solar_arc | naibod_ra
natal_aspect_orbs:               # para aspectos DENTRO da carta natal
  luminaries: 8.0
  planets: 6.0
  points: 3.0
transit_bodies:
  default: [sun, mercury, venus, mars, jupiter, saturn, uranus, neptune, pluto, chiron, mean_node]
  optional: [moon, lilith, ceres, pallas, juno, vesta]
transit_orbs:                    # orbe máxima por planeta em trânsito (graus)
  pluto: 1.0
  neptune: 1.0
  uranus: 1.0
  saturn: 1.5
  chiron: 1.0
  mean_node: 1.5
  jupiter: 2.0
  mars: 3.0
  sun: 4.0
  mercury: 4.0
  venus: 4.0
  moon: 3.0
orb_presets: { strict: 0.7, standard: 1.0, wide: 1.3 }
target_bonus: { sun: 0.5, moon: 0.5, asc: 0.5, mc: 0.5 }
aspects:
  major: [{name: conjunction, angle: 0}, {name: sextile, angle: 60}, {name: square, angle: 90},
          {name: trine, angle: 120}, {name: opposition, angle: 180}]
  minor: [{name: semisextile, angle: 30}, {name: semisquare, angle: 45},
          {name: sesquiquadrate, angle: 135}, {name: quincunx, angle: 150}]
  minor_orb_factor: 0.5
  minors_enabled_default: false
targets:
  natal_default: [sun, moon, mercury, venus, mars, jupiter, saturn, uranus, neptune, pluto, chiron, true_node, asc, mc, dsc, ic]
  optional: [lilith, ceres, pallas, juno, vesta]
house_transits:
  bodies: [jupiter, saturn, uranus, neptune, pluto, chiron, mean_node]
window_merge_gap_days: { slow: 10, fast: 0 }
refine: bisection                # bisection | linear
lifetime_years: 100
grid_file: data/ephemeris/natal_grid_1850_2150.npz
```

### 7.2 `config/natal_domains.yaml` (esboço)

```yaml
domains: [identity, home_family, mind_learning, relationships, career, resources, health_routine, purpose_transformation]
point_domains:
  sun:   { identity: 0.7, career: 0.15, health_routine: 0.15 }
  moon:  { home_family: 0.7, identity: 0.3 }
  asc:   { identity: 0.8, health_routine: 0.2 }
  mc:    { career: 0.85, identity: 0.15 }
  # ...
house_domains: { 1: identity, 2: resources, 3: mind_learning, 4: home_family, 5: relationships, 6: health_routine,
                 7: relationships, 8: purpose_transformation, 9: mind_learning, 10: career, 11: purpose_transformation, 12: purpose_transformation }
house_weight: 0.3
processes:
  jupiter: expansion
  saturn: structure
  uranus: rupture
  neptune: dissolution
  pluto: transformation
  chiron: wound_healing
  mean_node: direction
  sun: activation
  mercury: activation
  venus: activation
  mars: activation
weights:
  transit: { pluto: 1.0, neptune: 0.9, uranus: 0.9, saturn: 0.85, chiron: 0.6, jupiter: 0.6, mean_node: 0.5, mars: 0.4, sun: 0.35, venus: 0.25, mercury: 0.2 }
  point:   { sun: 1.0, moon: 1.0, asc: 1.0, mc: 0.95, venus: 0.75, mars: 0.75, mercury: 0.7, saturn: 0.7, jupiter: 0.6,
             uranus: 0.5, neptune: 0.5, pluto: 0.5, chiron: 0.5, true_node: 0.5, dsc: 0.6, ic: 0.6, lilith: 0.3 }
  aspect:  { conjunction: 1.0, opposition: 0.9, square: 0.85, trine: 0.6, sextile: 0.45 }
tone: { conjunction: focus, opposition: challenging, square: challenging, trine: flowing, sextile: flowing }
calibration_reference: data/calibration/natal_domains_reference.json
```

---

## 8. Modelo de dados (JSON)

```json
{
  "input": { "date": "1990-05-14", "time": "08:35", "time_known": true, "place": "São Paulo, BR",
             "lat": -23.5505, "lon": -46.6333, "tz": "America/Sao_Paulo", "house_system": "P",
             "orb_preset": "standard", "target_mode": "natal", "range": [1990, 2090] },
  "natal": { "jd_ut": 2448025.98, "bodies": [...], "houses": {...}, "aspects": [...], "precision": "exact_time" },
  "transits": [
    {
      "id": "saturn-square-sun-2031a",
      "transit_body": "saturn", "natal_point": "sun", "aspect": "square", "angle": 90,
      "orb_max": 2.0, "target_mode": "natal",
      "start": "2031-03-14", "end": "2031-12-02", "gap_days": 0,
      "hits": [ { "date": "2031-04-02", "jd": 2463000.41, "retrograde": false },
                { "date": "2031-08-19", "jd": 2463139.12, "retrograde": true },
                { "date": "2031-11-10", "jd": 2463222.77, "retrograde": false } ],
      "n_passes": 3, "applying_at_start": true,
      "age_start": 40.8, "age_end": 41.6,
      "intensity_peak": 0.72, "tone": "challenging", "process": "structure",
      "domains": { "identity": 0.55, "career": 0.30, "health_routine": 0.15 },
      "cycle_label": null,
      "text_key": "transit.saturn.hard.sun"
    }
  ],
  "house_transits": [ { "body": "pluto", "house": 10, "enter": "2044-02-11", "exit": "2060-01-03", "reentries": [...] } ],
  "cycles": [ { "label": "saturn_return_1", "date": "2019-06-21", "age": 29.1, "passes": 3 } ],
  "monthly_domains": { "months": ["1990-05", ...], "scores_1000": { "identity": [...], ... } },
  "key_years": [ { "year": 2031, "score_1000": 912, "top": ["saturn-square-sun-2031a", "..."] } ],
  "progressions": { "moon_timeline": [...], "ingresses": [...], "aspects_to_natal": [...] },
  "meta": { "engine": "swisseph 2.10.03", "grid": "natal_grid_1850_2150", "config_version": 1,
            "computed_in_ms": 870, "data_version": "6.0.0" }
}
```

---

## 9. Rotas

| Rota | Método | Público? | Descrição |
| :--- | :--- | :---: | :--- |
| `/natal` | GET | sim | Formulário |
| `/natal` | POST | sim | Valida e redireciona (303) para `/natal/transits?...` |
| `/natal/places` | GET `?q=` | sim (rate limit) | Autocomplete do gazetteer (fragment HTML ou JSON same-origin; não sob `/api/`) |
| `/natal/chart` | GET | sim | Mapa natal |
| `/natal/transits` | GET | sim | Trânsitos da vida (dados embutidos como JSON compacto gzip ≈ 100–300 KB) |
| `/natal/progressions` | GET | sim | Progressões |
| `/natal/export.{csv,ics,json}` | GET | sim (rate limit) | Exportações com os mesmos parâmetros |
| `/api/natal/chart` | GET | **interno** | JSON da carta (testes, scripts) |
| `/api/natal/transits` | GET | **interno** | JSON completo |
| `/api/natal/progressions` | GET | **interno** | JSON de progressões |

Todas as rotas aceitam `lang=pt|en`. Páginas HTML são server-rendered (Jinja) e não chamam `/api/*` do navegador (mantém a política atual); a interatividade (filtros, zoom) opera sobre o JSON embutido.

---

## 10. UI/UX

- **Componentes**: cabeçalho padrão (título, "o que esta página mostra", selo de precisão), abas Mapa / Trânsitos / Progressões, barra lateral de filtros (desktop) → drawer (mobile), cartões por trânsito, badges de tom (cores dos temas: âmbar = foco, rosa = desafiador, esmeralda = fluido), ícones Unicode astrológicos já usados no site.
- **Gráficos**: D3 (vendorizado) para linha da vida e mapa de calor (SVG acessível com `<title>`/`<desc>` e tabela equivalente); Chart.js para séries simples; roda e biwheel em SVG server-side (reuso).
- **Interações**: hover/tap mostra resumo; clique fixa o cartão; brush de década sincroniza linha da vida ↔ mapa de calor ↔ lista; botão "Hoje" centraliza; URL guarda filtros (`#f=...`).
- **Mobile**: linha da vida com rolagem horizontal e lanes colapsáveis; lista por padrão agrupada por ano com busca.
- **Temas**: paletas via tokens CSS existentes (`themes.css`); verificar contraste AA das cores de tom nos três temas.
- **i18n**: todas as strings por chave; textos interpretativos carregados do YAML do idioma.
- **Vazio/erros**: data fora da grade (aviso + cálculo lento), cidade não encontrada (campo manual), hora desconhecida (banner explicativo), parâmetros inválidos (mensagem acionável).

---

## 11. Desempenho

| Operação | Budget | Estratégia |
| :--- | ---: | :--- |
| Carta natal | < 100 ms | swe direto |
| Trânsitos ao natal, 100 anos, config padrão | < 1,5 s (p95 no servidor atual) | grade + numpy; bisseção só nos hits |
| Trânsitos ao progredido | < 2,5 s | interpolação mensal dos alvos |
| Progressões (Lua + ingressos + aspectos) | < 0,8 s | série mensal + bisseção |
| Autocomplete | < 30 ms | SQLite FTS5 |
| Página `/natal/transits` (TTFB) | < 2 s | cache LRU em memória por hash (TTL 10 min) |
| Memória residente adicional | < 60 MB | grade float32 + gazetteer em disco |

Teste de performance em CI com budget (marcado `@pytest.mark.perf`, tolerância 2× em runners lentos).

---

## 12. Segurança

- Herdar middlewares atuais (headers OWASP, bloqueio externo de `/api/*`).
- Rate limit (`slowapi` ou nginx) em `/natal/*`: 30 req/min/IP; `/natal/places`: 60 req/min/IP.
- Validação Pydantic estrita (intervalos, enums, tamanho de listas); rejeitar `range` > 120 anos.
- Sem execução de nada derivado da entrada além de números/enums; `label` escapado.
- Sem logs de parâmetros (ver §3.2); sem persistência.
- Dependências novas (`rapidfuzz`/`unidecode`, `slowapi`) fixadas em `requirements.lock`.

---

## 13. Testes

| Arquivo | Cobertura |
| :--- | :--- |
| `test_gazetteer.py` | busca por prefixo/acentos, fuso correto (São Paulo, Lisboa, Tóquio), fallback manual |
| `test_chart.py` | posições de referência (Einstein 14/03/1879 11:30 LMT Ulm — Astrodatabank AA; comparar com `swetest` dentro de 0,01°), sistemas de casas, ASC/MC, modo sem hora (sem casas, faixa da Lua) |
| `test_transits.py` | `wrap180` (propriedades), janela única vs. 3 passagens (Saturno □ Sol em período com retrogradação conhecida), 5 passagens de Plutão, orbes por planeta, bônus de alvo, aspectos simétricos (90/270), fusão de janelas, Lua excluída por padrão, `applying/separating`, datas exatas vs. `swetest` (± 1 h), limites da grade e fallback on-the-fly |
| `test_cycles.py` | retorno de Saturno ≈ 29,4–29,6 anos; oposição de Urano ≈ 40–42; nodal 18,6 |
| `test_progressions.py` | ☉ progredido ≈ ☉ natal + idade×~0,9856°; Lua progredida ≈ 1°/mês; ingressos e fases; MC por arco solar e Naibod; ASC_p consistente com `houses_armc`; trânsitos ao progredido detectam alvo móvel |
| `test_domains.py` | soma de pesos = 1 por ponto; intensidade decai linearmente com orbe; calibração monotônica; anos-chave reprodutíveis (seed) |
| `test_exports.py` | CSV colunas, ICS válido (parse com `icalendar` ou verificação estrutural), JSON schema |
| `test_routes.py` | 200 nas páginas, 303 no POST, `/api/natal/*` → 404 externo / 200 interno, i18n PT/EN, rate limit retorna 429 |
| `test_performance.py` | budgets de §11 |

Meta: ≥ 70 testes novos; cobertura de `src/natal/` ≥ 90%.

---

## 14. Enquadramento epistêmico

O AstroHistory demonstra, com seus próprios dados, que índices astrológicos mundanos não superam as taxas-base em previsão fora da amostra. O módulo pessoal **não contradiz** isso: é oferecido como leitura **simbólica e reflexiva** da astrologia moderna, com cálculo astronômico rigoroso e datas exatas, não como previsão validada.

Elementos obrigatórios na UI:
- Banner fixo e discreto em todas as páginas `/natal/*`: "Leitura simbólica (astrologia moderna). Cálculos astronômicos exatos; interpretação não validada empiricamente — veja a Metodologia."
- Link para `/methodology` e para a seção de hindcast.
- Textos interpretativos sem determinismo e sem conselhos de saúde, finanças ou direito.
- Botão "Mapa aleatório" (nascimento sintético) ao lado do resultado, como ferramenta pedagógica contra o efeito Barnum: o usuário pode comparar quão "pessoal" soa uma leitura de outra pessoa.

---

## 15. Plano de implementação (sub-fases)

| Sub-fase | Entregas | Duração | Dependências |
| :---: | :--- | :---: | :--- |
| 4.1 Infra | `natal.yaml`, `build_natal_grid.py`, `build_gazetteer.py`, `ephemeris_cache.py`, `gazetteer.py`, `chart.py`, `/natal` + `/natal/chart`, testes | 1,5 sem | Fase 0 (efemérides completas) |
| 4.2 Scanner | `transits.py`, `cycles.py`, casas em trânsito, modo sem hora, testes vs. `swetest` | 1,5 sem | 4.1 |
| 4.3 Domínios & UI | `domains.py`, calibração sintética, linha da vida, mapa de calor, anos-chave, "Agora", lista + filtros | 1,5 sem | 4.2 |
| 4.4 Exportações & i18n | `exports.py`, ICS/CSV/JSON, impressão, chaves i18n, acessibilidade, rate limit, logs | 1 sem | 4.3 |
| 5.1 Progressões | `progressions.py`, carta progredida, biwheel, Lua progredida, ingressos, aspectos ao natal | 1,5 sem | 4.2 |
| 5.2 Trânsitos ao progredido | alvos móveis no scanner, toggle de modo, testes | 1 sem | 5.1 |
| 6.1 Interpretações | templates + ~60 textos manuais PT/EN, paridade de chaves, revisão de estilo | 2 sem | 4.3, 5.1 |

Total Frente D: 9–10 semanas.

---

## 16. Questões abertas específicas do módulo

1. Vênus a 4° ou 3°? Marte a 3° ou 2,5°?
2. Incluir aspectos menores na v6.0 (desligados) ou adiar?
3. Padrão de MC progredido: arco solar ou Naibod?
4. Tamanho do gazetteer: `cities15000` (~25 mil, 5 MB) ou `cities500` (~200 mil, ~40 MB)?
5. Tom dos textos: reflexivo-psicológico ou descritivo?
6. Acesso ao módulo em beta: aberto com rate limit ou com token?
7. Mostrar intensidade calibrada 0–1000 (coerente com o site) ou escala simples 0–100?
