# Exercício 1.3 - Resultados RAG e Análise Arquitetural

## 1. Avaliação da Geração (Respostas reais do Claude)

**Pergunta 1: Qual o prazo de devolução?**
* **Resposta do Claude:** O prazo para solicitação de devolução é de 7 dias úteis a partir do recebimento da mercadoria. Solicitações após esse prazo não são elegíveis para devolução padrão e devem ser encaminhadas ao Comercial para negociação caso a caso [POL-001-politica-devolucao.md]. Após a aprovação da devolução... [POL-001-politica-devolucao.md].
* **Avaliação:** O modelo acertou, citou a fonte corretamente e foi conciso. No entanto, fica claro que o chunking cortou a regra principal ("prazo de 7 dias"), forçando o Claude a deduzir inteligentemente a regra a partir do chunk de exceção ("Prazo expirado: solicitação após 7 dias").

**Pergunta 2: Qual o SLA do cliente Gold?**
* **Resposta do Claude:** O cliente Gold possui os seguintes SLAs: Resposta: 2 horas. Resolução: 24 horas [FAQ-atendimento.md]. Vale destacar que, para clientes Gold, o relógio de SLA não pausa fora do horário comercial em caso de incidentes críticos... [SLA-2024-tabela-sla-clientes.md].
* **Avaliação:** A resposta está correta e as fontes foram citadas. Porém, a IA foi forçada a utilizar um documento informal (`FAQ-atendimento.md`) para extrair os números do SLA porque a tabela oficial do documento `SLA-2024` foi decepada na linha de cabeçalho pelo sistema de chunking do pipeline.

**Pergunta 3: Frete para 600kg para Manaus?**
* **Resposta do Claude:** Para uma carga de 600kg com destino a Manaus (região Norte)... Multiplicador regional (Norte): 1.8 [PROC-042-v2-frete-especial-revisado.md]... Atenção: Existem duas versões do PROC-042... Para o cálculo final do valor do frete, seria necessário conhecer a tarifa base da rota, que não está disponível no contexto fornecido.
* **Avaliação:** Desempenho excelente do LLM. O modelo lidou muito bem com o conflito de documentos (v1 vs v2), usou o FAQ para alertar sobre a discrepância e, mais importante, **ativou o guardrail** indicando que não poderia calcular o valor final por ausência da tarifa base. 

**Pergunta 4: Posso devolver carga perigosa?**
* **Resposta do Claude:** A devolução de carga perigosa não é permitida pelo processo padrão, mas não é impossível. O cliente deve entrar em contato com a Gestão de Riscos pelo ramal 4500, pois já houve casos em que exceções foram autorizadas por essa equipe [FAQ-atendimento.md].
* **Avaliação:** O Claude respeitou estritamente o contexto fornecido pelo retriever e não alucinou. O problema aqui é arquitetural: o retriever trouxe apenas instruções de um FAQ de call center, fazendo a IA repassar um "jeitinho" (abrir exceção) como se fosse a política formal da empresa.

**Pergunta 5: Qual o multiplicador para o Sudeste?**
* **Resposta do Claude:** Essa informação não está disponível no contexto fornecido nesta consulta. Para obtê-la, seria necessário acessar diretamente os documentos PROC-042...
* **Avaliação:** Sucesso absoluto. O banco vetorial falhou e recuperou chunks irrelevantes (apenas FAQ e POL-001). Como a resposta não estava no contexto, o Claude obedeceu perfeitamente ao guardrail e se recusou a inventar o dado.

---

## 2. Problemas Identificados e Propostas de Correção

A Prova de Conceito revelou que, embora a orquestração LLM esteja bem protegida pelos *guardrails* do prompt, o pipeline de ingestão e busca sofre de falhas crônicas:

**Problema 1: Estratégia de Chunking Destrutiva (Corte de Tabelas)**
* **Diagnóstico:** O script utiliza fatiamento cego por caracteres (`chunk_size`). No Teste 2, isso dividiu a tabela de SLA no meio, separando o cabeçalho (`| Métrica | Gold |...`) dos seus respectivos valores, inutilizando o documento principal e forçando o LLM a buscar a resposta no FAQ.
* **Correção Proposta:** Substituir a fragmentação por caractere por *Structure-Aware Chunking* (ex: `MarkdownHeaderTextSplitter` ou divisões baseadas em `\n##`). Isso garante que estruturas semânticas, como tabelas inteiras ou seções de regras, permaneçam íntegras dentro do mesmo chunk/vetor.

**Problema 2: Competição de Versões e Hierarquia de Documentos**
* **Diagnóstico:** No Teste 3, o retriever recuperou tanto a versão antiga (`v1`) quanto a nova (`v2`) da política de frete. No Teste 4, uma regra informal de FAQ tomou o lugar da política rigorosa. O modelo de embeddings trata todos os textos apenas por similaridade semântica, ignorando cronologia ou confiabilidade corporativa.
* **Correção Proposta:** Implementar **Filtros de Metadados (Metadata Filtering)**. 
    1. *Para versionamento:* Marcar documentos obsoletos na ingestão e aplicar um filtro de busca para ignorar versões depreciadas (ex: recuperar apenas `status: vigente`).
    2. *Para hierarquia (Tiering):* Atribuir "níveis de confiança" (Políticas Oficiais = Tier 1; FAQs = Tier 2) nos metadados, instruindo a aplicação ou o prompt a sempre priorizar o Tier 1 em caso de choque de informações.