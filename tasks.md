# Tasks — Query Endpoint

> Gerado a partir de `specs/query-endpoint/plan.md`.  
> Convenção de tamanho: **P** ≤ 2h · **M** 2–4h · **G** 4–8h (1 dev, sem bloqueios externos).

---

## Índice de tarefas

| ID | Descrição resumida | Tamanho | Depende de |
|----|--------------------|---------|------------|
| QE-01 | Scaffold da Azure Function (HTTP trigger POST /api/query) | P | — |
| QE-02 | Schema de validação de input com Zod | P | QE-01 |
| QE-03 | Configuração e tipagem de ambiente (`src/shared/config.ts`) | P | — |
| QE-04 | Cliente Azure OpenAI com retry/backoff (embedding) | M | QE-03 |
| QE-05 | Cliente Azure AI Search com retry/backoff (top-5 chunks) | M | QE-03 |
| QE-06 | Serviço `prompt-builder` (monta prompt com context budget) | M | QE-03 |
| QE-07 | Serviço `completion` (chama GPT-4o, retorna resposta + source) | M | QE-04, QE-06 |
| QE-08 | `response-builder` (serializa resposta HTTP final) | P | QE-07 |
| QE-09 | Handler completo integrando validação → search → completion → response | M | QE-02, QE-05, QE-07, QE-08 |
| QE-10 | Testes unitários: validator, prompt-builder, response-builder | M | QE-02, QE-06, QE-08 |
| QE-11 | Testes de integração: handler end-to-end com mocks MSW | G | QE-09, QE-10 |
| QE-12 | Structured logging com pino em todos os serviços | P | QE-09 |
| QE-13 | Health check endpoint (`/api/health`) | P | QE-01, QE-03 |

---

## Detalhamento

---

### QE-01 · Scaffold da Azure Function (HTTP trigger POST /api/query)

**Descrição**  
Criar a estrutura mínima do handler em `src/functions/query/handler.ts` registrado como Azure Function v4 com HTTP trigger no método POST e rota `/api/query`. Sem lógica de negócio — apenas recebe a requisição e retorna 200 com corpo vazio para confirmar o roteamento.

**Critérios de aceite**
- Arquivo `src/functions/query/handler.ts` existe e exporta a função registrada via `app.http(...)` do SDK v4.
- `func start` sobe sem erros e `POST /api/query` com corpo qualquer retorna HTTP 200.
- Build TypeScript passa sem erros (`tsc --noEmit`).
- Lint passa sem warnings (`eslint src/functions/query/`).

**Dependências**  
Nenhuma.

**Estimativa:** P

---

### QE-02 · Schema de validação de input com Zod

**Descrição**  
Implementar `src/functions/query/validator.ts` com schema Zod que valide o corpo da requisição. Campo obrigatório: `question` (string, 1–500 chars). Exportar tipo inferido `QueryInput` e função `parseQueryInput(body: unknown): QueryInput` que lança `ZodError` em caso de falha.

**Critérios de aceite**
- `parseQueryInput` retorna `QueryInput` para payload válido.
- `parseQueryInput` lança `ZodError` para payload sem `question`, com `question` vazio ou acima de 500 chars.
- Tipo `QueryInput` exportado e utilizável downstream sem `any`.
- Nenhum `any` explícito no arquivo.

**Dependências**  
QE-01

**Estimativa:** P

---

### QE-03 · Configuração e tipagem de ambiente (`src/shared/config.ts`)

**Descrição**  
Criar `src/shared/config.ts` que leia variáveis de ambiente necessárias ao endpoint (endpoints Azure OpenAI e AI Search, nomes de índice/deployment, api-keys) e as exponha como objeto tipado. Lançar erro descritivo na inicialização caso alguma variável obrigatória esteja ausente.

**Critérios de aceite**
- Todas as variáveis necessárias às tasks QE-04, QE-05 e QE-06 estão centralizadas aqui — nenhuma chamada a `process.env` espalhada em outros módulos.
- Aplicação falha em startup com mensagem clara ao remover qualquer variável obrigatória do `.env`.
- Arquivo `.env.example` na raiz lista todas as variáveis com valores fictícios.
- Sem `any` explícito.

**Dependências**  
Nenhuma.

**Estimativa:** P

---

### QE-04 · Cliente Azure OpenAI com retry/backoff (geração de embedding)

**Descrição**  
Implementar em `src/services/search.ts` (ou módulo auxiliar) a função `generateEmbedding(text: string): Promise<number[]>` que chama o deployment de embedding configurado em QE-03. Implementar retry com exponential backoff (máx. 3 tentativas) para erros 429 e 5xx.

**Critérios de aceite**
- Função retorna vetor de floats com a dimensão correta para o modelo configurado.
- Em simulação de falha 429, a função retenta até 3 vezes antes de lançar erro tipado.
- Nenhuma chave de API hardcoded — lida exclusivamente de `config.ts`.
- Timeout configurável via variável de ambiente (default 10s).

**Dependências**  
QE-03

**Estimativa:** M

---

### QE-05 · Cliente Azure AI Search com retry/backoff (busca top-5 chunks)

**Descrição**  
Implementar `src/services/search.ts` com função `searchChunks(embedding: number[]): Promise<Chunk[]>` que executa busca vetorial no índice configurado e retorna os top-5 chunks ordenados por score. O tipo `Chunk` (com campos `id`, `content`, `source_document`, `vigencia`) deve viver em `src/shared/types.ts`. Incluir retry com exponential backoff análogo ao QE-04.

**Critérios de aceite**
- Retorna exatamente 5 chunks (ou menos se o índice tiver menos resultados) com todos os campos tipados.
- Metadado `vigencia` está presente em cada chunk retornado (conforme ADR-0003).
- Retry funciona para erros 503 do Search.
- Score mínimo configurável via variável de ambiente (default 0.75); chunks abaixo do threshold são filtrados antes de retornar.

**Dependências**  
QE-03

**Estimativa:** M

---

### QE-06 · Serviço `prompt-builder` (monta prompt respeitando context budget)

**Descrição**  
Implementar `src/services/prompt-builder.ts` com função `buildPrompt(question: string, chunks: Chunk[]): string` que:
1. Lê o system prompt de `/prompts/system-prompt.md` (ou variável de ambiente equivalente).
2. Concatena chunks até o limite de ~8K tokens para contexto (ADR-0002).
3. Inclui `vigencia` de cada chunk para que o modelo priorize documentos vigentes (ADR-0003).
4. Appende a pergunta do usuário.

**Critérios de aceite**
- Com chunks que somam mais de 8K tokens, o builder trunca preservando os de maior score.
- O system prompt é lido do arquivo versionado, não hardcoded.
- Função é pura (sem side effects) e testável sem mocks de rede.
- Retorna string com estrutura de seções clara (system / context / question).

**Dependências**  
QE-03

**Estimativa:** M

---

### QE-07 · Serviço `completion` (chama GPT-4o, retorna resposta + source_document)

**Descrição**  
Implementar `src/services/completion.ts` com função `getCompletion(prompt: string, chunks: Chunk[]): Promise<CompletionResult>` onde `CompletionResult = { answer: string; source_document: string }`. O `source_document` deve ser o chunk de maior score utilizado no prompt.

**Critérios de aceite**
- `answer` é a resposta textual do modelo (sem metadados extras).
- `source_document` aponta para o identificador do chunk de maior relevância entre os incluídos no prompt.
- Retry com backoff para 429/5xx (máx. 3 tentativas), mesmo padrão de QE-04.
- Erros do modelo (content filter, context length exceeded) lançam custom errors tipados definidos em `src/shared/errors.ts`.

**Dependências**  
QE-04, QE-06

**Estimativa:** M

---

### QE-08 · `response-builder` — serialização da resposta HTTP

**Descrição**  
Implementar `src/functions/query/response-builder.ts` com função `buildResponse(result: CompletionResult): HttpResponseInit` que serializa a resposta no formato JSON `{ answer, source_document }` com `Content-Type: application/json` e status 200. Implementar também `buildErrorResponse(error: unknown): HttpResponseInit` com mapeamento de erros para status HTTP adequados (400 para ZodError, 502 para falhas upstream, 500 para demais).

**Critérios de aceite**
- Resposta de sucesso tem shape `{ answer: string; source_document: string }` e status 200.
- ZodError mapeia para 400 com mensagem de validação legível.
- Erros de serviços Azure mapeiam para 502.
- Nenhum stack trace ou detalhe interno vaza no corpo de resposta de produção.

**Dependências**  
QE-07

**Estimativa:** P

---

### QE-09 · Handler completo integrando todos os serviços

**Descrição**  
Atualizar `src/functions/query/handler.ts` para orquestrar o fluxo completo:  
`parse input → generateEmbedding → searchChunks → buildPrompt → getCompletion → buildResponse`.  
Erros em qualquer etapa devem ser capturados e encaminhados para `buildErrorResponse`.

**Critérios de aceite**
- `POST /api/query` com `{ "question": "..." }` válido retorna `{ answer, source_document }` e status 200 (em ambiente com serviços Azure mockados).
- `POST /api/query` sem campo `question` retorna 400 com mensagem de validação.
- `POST /api/query` quando Azure AI Search falha retorna 502.
- Nenhum `console.log` direto — toda saída via logger (QE-12 pode ser feito em paralelo; o handler só precisa importar o logger e chamá-lo).

**Dependências**  
QE-02, QE-05, QE-07, QE-08

**Estimativa:** M

---

### QE-10 · Testes unitários: validator, prompt-builder, response-builder

**Descrição**  
Criar testes unitários em `tests/unit/query/` cobrindo os três módulos puros:
- `validator.spec.ts` — casos válidos e inválidos para `parseQueryInput`.
- `prompt-builder.spec.ts` — truncagem de chunks, inclusão de vigência, leitura do system prompt.
- `response-builder.spec.ts` — serialização de sucesso, mapeamento de erros.

Usar Vitest. Sem chamadas de rede; mocks apenas onde necessário (leitura de arquivo do system prompt).

**Critérios de aceite**
- Cobertura de linhas ≥ 90% nos três módulos medida pelo relatório Vitest.
- Nenhum teste faz chamada de rede real.
- `vitest run` completa em menos de 10s.
- Todos os casos de erro documentados nos critérios de QE-02, QE-06 e QE-08 têm ao menos um teste correspondente.

**Dependências**  
QE-02, QE-06, QE-08

**Estimativa:** M

---

### QE-11 · Testes de integração: handler end-to-end com mocks MSW

**Descrição**  
Criar `tests/integration/query/handler.integration.spec.ts` usando Vitest + MSW para interceptar chamadas HTTP para Azure OpenAI e Azure AI Search. Testar o fluxo completo do handler com payloads das fixtures (`tests/fixtures/queries.ts` e `tests/fixtures/chunks.ts`).

Cenários obrigatórios:
1. Fluxo feliz — resposta correta com `source_document` populado.
2. Azure AI Search retorna 503 — handler retorna 502.
3. Pergunta inválida (campo ausente) — handler retorna 400.
4. Nenhum chunk acima do score mínimo — handler retorna resposta indicando ausência de contexto (não alucinação).

**Critérios de aceite**
- Todos os 4 cenários têm testes verdes.
- Nenhuma chamada real a Azure é feita (MSW intercepta tudo).
- Fixtures reutilizadas de `tests/fixtures/` — sem dados inline nos testes.
- `vitest run` do arquivo completa em menos de 30s.

**Dependências**  
QE-09, QE-10

**Estimativa:** G

---

### QE-12 · Structured logging com pino em todos os serviços

**Descrição**  
Garantir que `src/shared/logger.ts` exporta instância pino configurada com nível via variável de ambiente (`LOG_LEVEL`, default `info`). Adicionar chamadas de log nos pontos-chave do fluxo: recebimento da requisição, início/fim de cada chamada externa, erros capturados. Logs devem incluir `request_id` propagado do handler.

**Critérios de aceite**
- Toda chamada a serviços externos (embedding, search, completion) emite log `debug` de início e `info` de conclusão com duração em ms.
- Erros emitem log `error` com stack trace (apenas em `LOG_LEVEL=debug`).
- Em produção (`NODE_ENV=production`), saída é JSON puro (sem pretty-print).
- Nenhum `console.log` / `console.error` remanescente em `src/`.

**Dependências**  
QE-09

**Estimativa:** P

---

### QE-13 · Health check endpoint (`/api/health`)

**Descrição**  
Criar `src/functions/health/handler.ts` com HTTP trigger GET `/api/health` que retorna `{ status: "ok", version: "<package.json version>" }` e status 200. Sem dependências externas — deve responder mesmo se Azure AI Search estiver indisponível.

**Critérios de aceite**
- `GET /api/health` retorna 200 com shape `{ status: "ok", version: string }`.
- `version` bate com o campo `version` do `package.json` em tempo de execução.
- Responde em menos de 100ms (sem I/O externo).
- Coberto por ao menos 1 teste unitário em `tests/unit/health/`.

**Dependências**  
QE-01, QE-03

**Estimativa:** P

---

## Ordem de execução sugerida

```
QE-01 ──► QE-02 ──┐
                   ├──► QE-09 ──► QE-11
QE-03 ──► QE-04 ──┤
       ├──► QE-05 ──┤
       └──► QE-06 ──► QE-07 ──► QE-08 ──┘
                                          QE-10 ──► QE-11
QE-01 + QE-03 ──► QE-13
QE-09 ──► QE-12
```

Tasks sem dependências (QE-01, QE-03) podem começar em paralelo. QE-10 pode ser escrito junto com QE-02/QE-06/QE-08 (TDD recomendado).
