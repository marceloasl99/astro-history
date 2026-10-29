# astro-history 🪐🏛️
### Plataforma de Pesquisa Científica Aberta e Reprodutível sobre Alinhamentos Astrológicos e Fatos Históricos

![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![Swiss Ephemeris](https://img.shields.io/badge/Swiss_Ephemeris-2.10.3-00599C)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)
![Testes](https://img.shields.io/badge/Testes-21_Passaram-10B981)
![Licença](https://img.shields.io/badge/Licen%C3%A7a-AGPL--3.0-8B5CF6)
![Marco M2](https://img.shields.io/badge/Marco_M2-Caminho_A_(Piv%C3%B4_Metodol%C3%B3gico)-blue)

> 🌍 **Idiomas / Languages**: **Português** • [English Version (README.md)](README.md)

---

## 1. Resumo Executivo & Pergunta de Pesquisa

O **astro-history** é uma bancada de testes de código aberto concebida para responder com honestidade e método à seguinte questão empírica:

> **"As geometrias de aspectos planetários e alinhamentos astronômicos distinguem grandes eventos históricos da humanidade de datas aleatórias melhor do que o mero acaso?"**

Originalmente construído como um navegador de correlações baseado no **Swiss Ephemeris (`pyswisseph`)**, o projeto passou por uma reconstrução metodológica integral para erradicar o viés de confirmação retrospectivo (*cherry-picking*), vazamentos de dados e artefatos matemáticos.

### Principal Resultado Empírico (Validação Pré-Registrada da Fase 3)
Sob hipóteses pré-registradas estritas (`docs/hipoteses.md`) e modelos nulos controlados:
- **Modelo Nulo de Deslocamento Circular (N3, 10.000 permutações)**: Tensão Cósmica observada $z = -0.506$ ($p = 0.6941$, FDR $q = 0.9772$).
- **Teste Temporal Fora da Amostra (1951–2025)**: $z = -0.851$ ($p = 0.7996$, FDR $q = 0.9772$).

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

## 3. Resultados Estatísticos Empíricos (Fase 3)

| Hipótese Testada | N | Score Obs. | Distribuição Nula (Média ± DP) | Efeito ($z$) | $p$-valor | $q$ (FDR) | Significante ($q < 0.05$)? |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **H1 Geral vs N3 Deslocamento Circular** | 59 | 481.1 | 500.6 ± 38.5 | -0.506 | 0.6941 | 0.9772 | ❌ Não significante |
| **H1 Geral vs N2 Estratificado por Década** | 61 | 477.6 | 493.7 ± 35.9 | -0.450 | 0.6715 | 0.9772 | ❌ Não significante |
| **H1 Classe: Guerra Interestadual** | 15 | 462.1 | 499.4 ± 73.3 | -0.509 | 0.6918 | 0.9772 | ❌ Não significante |
| **H1 Classe: Crise Econômica** | 10 | 547.6 | 501.9 ± 93.8 | +0.487 | 0.3112 | 0.9772 | ❌ Não significante |
| **H1 Classe: Golpe de Estado** | 12 | 538.4 | 501.6 ± 84.9 | +0.434 | 0.3327 | 0.9772 | ❌ Não significante |
| **H2 Treino Temporal (1800–1950)** | 28 | 512.4 | 499.4 ± 56.8 | +0.229 | 0.4083 | 0.9772 | ❌ Não significante |
| **H2 Teste Fora da Amostra (1951–2025)** | 33 | 456.5 | 501.6 ± 53.0 | -0.851 | 0.7996 | 0.9772 | ❌ Sem sinal preditivo |
| **Controle Negativo (Ruído Sintético)** | 61 | 427.8 | 501.5 ± 37.2 | -1.982 | 0.9772 | 0.9772 | ❌ Pipeline íntegra |

*Documentos de auditoria e relatórios*:
- Pré-registro formal: [`docs/hipoteses.md`](docs/hipoteses.md)
- Relatório de validação estatística: [`reports/phase3_validation.md`](reports/phase3_validation.md)
- Decisão do Marco M2: [`docs/decisao_M2.md`](docs/decisao_M2.md)
- Relatório técnico exaustivo: [`reports/final_report.md`](reports/final_report.md)

---

## 4. Como Executar e Reproduzir

```bash
# 1. Configurar ambiente e instalar dependências congeladas
make setup

# 2. Executar suíte completa de testes automatizados
make test

# 3. Rodar validação estatística completa (10.000 permutações sob N3)
make validate

# 4. Iniciar servidor local com a interface responsável
make run
```

---

## 5. Licença e Atribuição

- **Código-Fonte**: Licenciado sob a **[GNU Affero General Public License v3 (AGPL-3.0-or-later)](LICENSE)**.
- **Swiss Ephemeris**: Utiliza a biblioteca Swiss Ephemeris da **Astrodienst AG**. Em conformidade com os termos da Astrodienst, o projeto é distribuído sob AGPL. Uso comercial sem termos AGPL exige licença proprietária comercial da Astrodienst AG.
- **Bases de Dados Históricas**: Correlates of War (COW), UCDP Conflict Data, NBER Business Cycles, Powell & Thyne Coup Data e Polity5/V-Dem Project.
