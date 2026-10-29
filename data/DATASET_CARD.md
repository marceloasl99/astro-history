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
