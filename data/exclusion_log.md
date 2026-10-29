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
