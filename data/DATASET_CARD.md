# Dataset Card: Events v2 & Control Group

## 1. Visão Geral e Propósito
O dataset `events_v2` substitui o catálogo curado manualmente por um conjunto de eventos históricos estruturado segundo **critérios operacionais pré-definidos**, auditáveis e provenientes de fontes públicas reconhecidas em ciências sociais, história econômica e relações internacionais.

O objetivo é eliminar vieses de seleção e confirmação (*cherry-picking*), desequilíbrios geográficos extremos e imprecisão temporal antes da realização de qualquer teste de hipótese astrológica.

---

## 2. Taxonomia de Classes de Eventos e Critérios de Inclusão

| Classe (`event_class`) | Critério Objetivo de Inclusão | Fonte Principal | Exemplo |
| :--- | :--- | :--- | :--- |
| `war_interstate` | Início de guerra entre estados soberanos com $\ge 1.000$ mortes em combate. | Correlates of War (COW) / UCDP | Início da 1ª Guerra Mundial (1914-07-28) |
| `armed_conflict` | Início de conflito armado intraestatal ou internacionalizado com $\ge 25$ mortes/ano. | UCDP/PRIO Armed Conflict Dataset | Revolução Mexicana (1910-11-20) |
| `economic_recession` | Recessão datada por órgão oficial ou crise bancária/cambial sistêmica documentada. | NBER / FMI / Reinhart & Rogoff | Black Tuesday / Crash de Wall Street (1929-10-29) |
| `pandemic` | Declaração oficial de emergência de saúde pública global / pandemia documentada. | OMS / Historical Epidemics Data | Pandemia de Gripe Espanhola (1918-03-04), COVID-19 (2020-03-11) |
| `coup_d_etat` | Tentativa ou sucesso de deposição inconstitucional do chefe de Estado por forças armadas ou civis. | Powell & Thyne Coup Dataset | Golpe Militar no Brasil (1964-03-31), Golpe de 18 de Brumário (1799-11-09) |
| `regime_change` | Queda de regime autoritário, proclamação republicana ou transição constitucional radical. | Polity5 / V-Dem Project | Queda da Bastilha (1789-07-14), Proclamação da República (1889-11-15) |

---

## 3. Regras de Filtragem e Higiene Metodológica

1. **Momento de Início vs. Pico**:
   - O catálogo registra estritamente a data do **início/deflagração** do fenômeno (ex: declaração de guerra, primeiro combate documentado, ato de deflagração do golpe). Batalhas intermediárias ou acordos de paz intermediários não são misturados com início.
2. **Precisão da Data (`date_precision`)**:
   - `day`: Dia exato documentado historicamente por documentos contemporâneos. Apenas estes eventos são submetidos a testes de score diário.
   - `month` ou `year`: Eventos cuja data exata é incerta ou contestada por historiadores são rotulados como tal e avaliados apenas em janelas agregadas.
   - **Meta da Fase 2**: Pelo menos 80% do conjunto com precisão `day`.
3. **Equilíbrio Geográfico**:
   - Nenhum país isolado pode representar mais de 20% do dataset.
   - Distribuição continental com representação equilibrada entre Europa, Américas, Ásia e África.
4. **Campos Obrigatórios**:
   - Todo registro deve incluir `source_name`, `source_url` e `inclusion_rule` explícitos.

---

## 4. Grupo de Controle Estratificado (`control_dates`)

Devido à autocorrelação temporal extrema das posições dos planetas externos (Plutão leva ~248 anos para completar uma órbita, Netuno ~165 anos e Urano ~84 anos), testes ingênuos contra datas aleatórias uniformes geram correlações espúrias e falsos positivos.

Para neutralizar esse viés:
- O grupo de controle contém **10.000 datas aleatórias pareadas e estratificadas por década**, refletindo exatamente a distribuição temporal dos eventos do catálogo.
- Semente do gerador pseudoaleatório fixada: `seed = 42`.

---

## 5. Catálogo Geral Expandido (Fase 4 - Internacional)

Para além da amostra analítica pré-registrada de teste, o AstroHistory implementa uma **Arquitetura de Duplo Circuito (Dual-Track Architecture)**:

```
+--------------------------------------------------------------------------+
|                     ARQUITETURA DE DUPLO CIRCUITO                        |
+------------------------------------+-------------------------------------+
| TRACK A: Catálogo Geral Expandido  | TRACK B: Amostra Analítica Fidedigna|
| (Exploração & Historical Analogues)| (Teste de Hipótese Pré-Registrado)  |
+------------------------------------+-------------------------------------+
| • Tabela: events (N = 3.406)       | • Tabela: events_v2 (N = 61)        |
| • Categorias: 6 canônicas          | • Categorias: 6 analíticas          |
| • Arquivo: historical_events.json  | • Arquivo: events_v2.csv            |
| • Fontes: COW v4.0, UCDP v24.1,    | • Controle: control_dates (10.000)  |
|   Powell & Thyne, USGS, NOAA NCEI, | • Critérios: Inclusão restrita,     |
|   Smithsonian GVP, NBER,           |   pareamento temporal decenal,      |
|   Curados (Antiguidade, LatAm,     |   análise cega a hipóteses.         |
|   Ciência, Diplomacia, Sociedade)  | • Status: Rígido e Imutável         |
| • Alcance: 9650 a.C. a 2026 d.C.   |   (preserva validações v2/v3).      |
| • Objetivo: Pesquisa de análogos,  | • Objetivo: Avaliação objetiva de   |
|   educação, timeline e consultas.  |   capacidade preditiva estatística. |
+------------------------------------+-------------------------------------+
```

### 6 Categorias Canônicas do Catálogo Expandido (Track A):
1. **Revolução & Conflito Interno** ($N=765$): Golpes de Estado (Powell & Thyne), insurreições populares, guerras civis e revoluções.
2. **Guerra & Conflito** ($N=229$): Guerras interestatais (COW v4.0) e conflitos armados internacionais (UCDP/PRIO v24.1).
3. **Desastre & Saúde Pública** ($N=203$): Grandes terremotos globais ($M \ge 7.8$, USGS) e pandemias históricas documentadas.
4. **Crise Financeira & Econômica** ($N=59$): Picos de recessão macroeconômica (NBER) e quebras bancárias sistêmicas.
5. **Ciência & Tecnologia** ($N=58$): Marcos da revolução científica, exploração espacial, física e computação.
6. **Política, Tratados & Cultura** ($N=28$): Tratados fundamentais de paz internacional, renascimentos culturais e reformas jurídicas.
```

### Fontes Acadêmicas Oficiais Integradas no Track A:
1. **Correlates of War (COW) Inter-State War Dataset v4.0**:
   - 94 guerras interestatais entre soberanos documentadas desde 1823 com beligerantes e baixas militares de combate.
2. **Uppsala Conflict Data Program (UCDP/PRIO) Armed Conflict Dataset v24.1**:
   - 251 conflitos armados intra e interestatais com datação precisa de início (níveis de precisão 1 a 3).
3. **Powell & Thyne Coup d'État Dataset (v2026.08)**:
   - 462 episódios de golpe de Estado (bem-sucedidos e tentativas) em todos os continentes desde 1950.
4. **USGS Earthquake Hazards Program Comprehensive Catalog (ComCat)**:
   - 190 grandes terremotos globais de magnitude de momento $M \ge 7.8$ com coordenadas epicentrais e hora UTC exata.
5. **National Bureau of Economic Research (NBER)**:
   - 34 picos de ciclo econômico marcando início oficial de recessões nos EUA (1857-2020).
6. **Curated Historical Milestones**:
   - 39 marcos históricos verificados (tratados de paz de Westfália a Versalhes, fundações, revolução científica e conquistas espaciais).

### Deduplicação Fuzzy e Higiene:
- Critério de deduplicação: eventos candidatos com mesma data ($\pm 3$ dias) e alta similaridade léxica ou mesmo país/categoria foram comparados, resultando em 76 potenciais duplicatas descartadas.
- Todas as 3.406 efemérides foram calculadas integralmente pela Swiss Ephemeris (`calculated = 1`), com posições zodiacais, aspectos estritos e índices de tensão gerados no banco SQLite.

