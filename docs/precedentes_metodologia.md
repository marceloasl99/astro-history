# Metodologia do Motor de Precedentes e Similaridade Geométrica

> **Auditoria Metodológica (Etapa 4 / Experimento E5)**:  
> Avaliação formal do matcher astrológico como ferramenta preditiva vs. ferramenta de exploração geométrica.

---

## 1. Funcionamento do Algoritmo de Similaridade

A função `find_similar_events` compara uma carta astral alvo com o catálogo histórico através de quatro componentes ponderados:
1. **Proximidade Zodiacal de Corpos Celestes**: Peso hierárquico decrescente de planetas transpessoais (Plutão $w=22$, Netuno $w=18$, Urano $w=18$, Saturno $w=14$) até luminares e asteroides. A distância angular dentro do mesmo signo recebe bônus de proximidade contínuo.
2. **Aspectos Estritos Compartilhados**: Bônus para pares planetários que formam o mesmo aspecto maior clássico (orbe $\le 3,0^\circ$).
3. **Estrelas Fixas**: Conjunções simultâneas com as mesmas estrelas fixas maiores (orbe $\le 0,3^\circ$).
4. **Higiene Metodológica (Leave-One-Out P0-3)**: Exclusão estrita do próprio evento e de qualquer evento ocorrido no mesmo ano ou na janela de $\pm 1$ ano ($\text{distância} \le 1$).

---

## 2. Experimento E5: Teste de Valor Preditivo Fora da Amostra

- **Pergunta**: O precedente histórico de maior similaridade (Top-1) compartilha a mesma classe/categoria do evento alvo com frequência superior ao chute pela taxa-base?
- **Protocolo**: Validação cruzada Leave-One-Out ($N = 300$ eventos).
- **Resultados Empíricos**:
  - Taxa-base da classe majoritária (*Revolução Política*): **$32,0\%$**
  - Acurácia Top-1 observada: **$26,7\%$** ($80$ acertos em $300$)
  - $p$-valor contra a taxa-base: **$0,98$** (significativamente *pior* que predizer a classe majoritária a cegas).

---

## 3. Decisão de Projeto e Reclassificação

Conforme a regra de ouro estabelecida no plano de revisão:
> *"Se não superar a taxa-base, o recurso vira 'exploração geométrica', sem narrativa de cenário."*

1. **Desreificação Causal**: O texto síntese deixou de insinuar "momentos de ruptura de paradigmas e transformações irreversíveis futuros".
2. **Nova Nomenclatura**: O recurso é explicitamente designado como **"Exploração de Isomorfismo Geométrico"**.
3. **Unificação de Métricas**: O card e os dados exibem com clareza o **Percentual de Similaridade Geométrica Top-1** com a identificação explícita do evento comparado.
