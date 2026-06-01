### 1. Mapeamento de contexto estático vs dinâmico (Revisado)

| Parte | Tipo | Tokens estimados | Frequência de mudança |
| :--- | :--- | :--- | :--- |
| Identidade e Formato | Estático | ~100 tokens | Raramente (versionado como código) |
| Guardrails e Regras de Comportamento | Estático | ~150 tokens | Raramente (versionado como código) |
| Metadados do Cliente (Ex: Tier Gold/Silver/Standard) | Dinâmico / por sessão | ~40 tokens | Por sessão |
| Chunks recuperados (5 a 10 chunks de ~400 tokens) | Dinâmico / por query | ~2.000 a ~4.000 tokens | Por query |
| Pergunta | Dinâmico / por query | ~50 tokens | Por query |
| Histórico | Dinâmico, crescente | 0 a ~3.000 tokens | Acumula na sessão |
| **Total por query** | | **~2.340 a ~7.340 tokens** | |

**Análise do Orçamento de Atenção e Capacidade de Retenção**

O modelo Claude 4.6 Sonnet possui uma janela teórica extensa de até 200K tokens. Subtraindo as instruções do system prompt, os metadados do projeto (como o perfil do cliente e histórico de chamados) e o limite máximo projetado para o histórico de conversa (totalizando aproximadamente 3.500 tokens), restam cerca de 196.500 tokens úteis. 

Matematicamente, seria possível injetar centenas de chunks nesse espaço restante. No entanto, enviar o limite máximo satura o orçamento de atenção do modelo, ocasionando inevitavelmente o efeito *lost in the middle*, onde as informações posicionadas no meio do contexto são processadas com menor peso cognitivo e frequentemente ignoradas. Para garantir a rastreabilidade e a precisão das respostas, o pipeline de retrieval está configurado para retornar um recorte rigoroso de apenas 5 a 10 chunks por query, otimizando o processamento da IA e protegendo a integridade da arquitetura da solução.

---

### 2. Documentação Formal dos Testes (Ciclo de Iteração v1 → v2)

Abaixo está a documentação do ciclo de testes evidenciando a melhoria implementada após a análise da Rodada 1. O prompt **v1** gerava respostas com detalhes excessivos, então o **v2** recebeu o guardrail de objetividade: *"Seja direto e objetivo, respondendo o que foi perguntado, somente, sem adicionar métricas e/ou informações extras..."*

| Pergunta de Teste | Resposta Obtida (Prompt v1) | Resposta Obtida (Prompt v2 Iterado) | Análise da Iteração e Resultado |
| :--- | :--- | :--- | :--- |
| **1. "Qual o prazo de devolução para carga perigosa?"** | Fonte: POL-001, seção 3.2. Cargas classificadas como perigosas (classes 1 a 6) não são elegíveis... oriente-o a escalar para o supervisor... | Fonte: POL-001, seção 3.2. Cargas perigosas (classes 1 a 6) não são elegíveis para devolução. A política não se aplica a esse tipo de mercadoria. | **Sucesso (Armadilha evitada).** Ambas as versões identificaram a exceção e não inventaram prazo. A v2 foi sutilmente mais concisa, removendo a instrução redundante de escalar. |
| **2. "Meu cliente é Gold, qual o SLA de resolução?"** | Fonte: SLA-2024. Prazos: Resposta inicial Até 2 hours. Resolução Até 24 horas. | Fonte: SLA-2024. O prazo de resolução para clientes Gold é de até 24 horas. | **Melhoria Crítica (Objetividade).** A v1 falhou ao entregar o prazo de *resposta inicial* não solicitado. A v2 aplicou perfeitamente o novo guardrail, sendo cirúrgica e entregando apenas a métrica de *resolução* solicitada. |
| **3. "Quanto custa o frete para 600kg para Manaus?"** | Fonte: PROC-042-v2. Multiplicador 1,8. Cálculo... ⚠️ Atenção: não informa o valor base... escale para o supervisor. | Fonte: PROC-042-v2. Multiplicador 1,8 sobre o valor base. Porém, valor base não consta... escale para o supervisor. | **Sucesso (Gatilho de Escape).** Ambas as versões conectaram Manaus à Região Norte e aplicaram a regra de exceção corretamente (identificando a ausência do valor base), acionando o supervisor sem alucinar o valor final do frete. |