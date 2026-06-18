# Árvore de Skills — NovaTech Assistant

> Documento gerado na fase de estruturação do projeto. Define as skills que governam a geração de artefatos ao longo do desenvolvimento, organizadas na hierarquia Foundation → Domain → Artifact.

---

## Visão geral

| Camada | Local | Propósito |
|---|---|---|
| **Foundation** | `skills/foundation/` | Convenções globais — todo agente consulta antes de gerar código |
| **Domain** | `skills/domain/` | Padrões por camada técnica — específicos de cada área do sistema |
| **Artifact** | `skills/artifact/` | Receitas de geração — composições das camadas anteriores |

---

## Foundation

Pré-condições não opcionais. Todo agente que gera código TypeScript deve carregar `typescript-conventions` + `error-handling` antes de escrever qualquer artefato de código.

### `typescript-conventions.md`

| Campo | Valor |
|---|---|
| **Frase-ativação** | "Crie / modifique qualquer arquivo TypeScript" |
| **Cria** | Tech Lead |
| **Consulta** | Dev, Copilot, Claude Code |
| **Frequência** | ●●●●● Toda geração de código |

Strict mode, nomenclatura, imports, uso de tipos utilitários, regras de exports. Base de todos os artefatos de código.

---

### `error-handling.md`

| Campo | Valor |
|---|---|
| **Frase-ativação** | "Adicione tratamento de erro" / "o endpoint pode falhar" |
| **Cria** | Tech Lead |
| **Consulta** | Dev, Copilot, Claude Code |
| **Frequência** | ●●●●● Toda geração de código |

Custom errors (`AppError`, `ValidationError`, `UpstreamError`), padrão de logging em `catch`, retries com backoff, tipagem de `Result<T, E>`.

---

### `logging.md`

| Campo | Valor |
|---|---|
| **Frase-ativação** | "Adicione logs" / "preciso rastrear essa operação" |
| **Cria** | Tech Lead |
| **Consulta** | Dev, Copilot, Claude Code |
| **Frequência** | ●●●●○ Frequente |

Pino como logger, campos obrigatórios (`traceId`, `userId`, `duration`), níveis por ambiente, sanitização de PII antes de logar.

---

### `env-config.md`

| Campo | Valor |
|---|---|
| **Frase-ativação** | "Acesse configuração de ambiente" / "variável de ambiente" |
| **Cria** | Tech Lead |
| **Consulta** | Dev, Copilot, Claude Code |
| **Frequência** | ●●●○○ Moderada |

Padrão de leitura via `src/shared/config.ts`, validação com Zod na inicialização, nunca hardcodar segredos, nomes de variáveis por módulo.

---

### `project-structure.md`

| Campo | Valor |
|---|---|
| **Frase-ativação** | "Onde esse arquivo deve ficar?" / "crie um novo módulo" |
| **Cria** | Tech Lead |
| **Consulta** | Dev, Product Specialist, Copilot |
| **Frequência** | ●●●○○ Onboarding e novas features |

Mapa da árvore do Anexo C, regras de onde cada tipo de artefato vive, convenções de nomeação de pastas e arquivos.

---

## Domain

Representam as camadas da arquitetura. Cada skill é a "gramática" da sua camada: como um endpoint Azure Function é organizado, como o Search é consultado, como um componente React é estruturado.

### `azure-functions-endpoint.md`

| Campo | Valor |
|---|---|
| **Frase-ativação** | "Crie um endpoint" / "Azure Function" / "HTTP trigger" |
| **Cria** | Tech Lead + Dev Sênior |
| **Consulta** | Dev, Copilot, Claude Code |
| **Frequência** | ●●●●● Toda nova Function |

Estrutura de `handler.ts` + `validator.ts` + `response-builder.ts`, padrão de contexto Azure, cabeçalhos obrigatórios, integração com logger e custom errors.

---

### `azure-ai-search-integration.md`

| Campo | Valor |
|---|---|
| **Frase-ativação** | "Consulte o índice" / "busca semântica" / "retrieval" |
| **Cria** | Tech Lead + Dev Sênior |
| **Consulta** | Dev, Copilot, Claude Code |
| **Frequência** | ●●●●○ Frequente — core do RAG |

SDK de Search, construção de query híbrida (keyword + vector), parâmetros de top-k, tratamento de resultados vazios, campo de `source` para citação.

---

### `azure-openai-completion.md`

| Campo | Valor |
|---|---|
| **Frase-ativação** | "Chame o LLM" / "gere uma completion" / "monte o prompt" |
| **Cria** | Tech Lead + Dev Sênior |
| **Consulta** | Dev, Copilot, Claude Code |
| **Frequência** | ●●●●○ Frequente — core do RAG |

Cliente OpenAI, montagem do `messages` array, injeção de system prompt versionado, parâmetros de temperatura, parse da resposta, fallback em caso de timeout.

> **Nota:** separada de `azure-ai-search-integration.md` intencionalmente — há cenários de completion sem retrieval e vice-versa.

---

### `testing-patterns.md`

| Campo | Valor |
|---|---|
| **Frase-ativação** | "Escreva um teste" / "como testar isso?" |
| **Cria** | QA + Tech Lead |
| **Consulta** | Dev, Copilot, Claude Code |
| **Frequência** | ●●●●● Todo novo artefato de código |

Vitest como runner, padrão AAA (Arrange/Act/Assert), mocks para Azure SDK com `vi.mock`, fixtures de chunks e queries de `src/tests/fixtures/`, cobertura mínima por camada.

---

### `react-components.md`

| Campo | Valor |
|---|---|
| **Frase-ativação** | "Crie um componente React" / "card do painel" / "formulário web" |
| **Cria** | Dev Sênior (Front) |
| **Consulta** | Dev, Copilot |
| **Frequência** | ●●●○○ Painel web |

Estrutura funcional com hooks, Tailwind para estilo, acessibilidade mínima (`aria-label`, `role`), padrão de props tipadas, onde vive em `src/web/src/components/`.

---

### `spec-sdd-template.md`

| Campo | Valor |
|---|---|
| **Frase-ativação** | "Escreva um requirements" / "crie um plan.md" / "liste as tasks" |
| **Cria** | Product Specialist + Tech Lead |
| **Consulta** | Product Specialist, Tech Lead, Dev |
| **Frequência** | ●●●○○ Cada novo módulo |

Estrutura canônica de `requirements.md` (problema, critérios de aceite, restrições), `plan.md` (arquitetura, dependências, riscos) e `tasks.md` (lista atômica com estimativas).

---

### `adr-template.md`

| Campo | Valor |
|---|---|
| **Frase-ativação** | "Documente essa decisão" / "crie um ADR" |
| **Cria** | Tech Lead |
| **Consulta** | Tech Lead, Product Specialist, Dev Sênior |
| **Frequência** | ●●○○○ Decisões arquiteturais |

Formato: Contexto, Decisão, Consequências, Alternativas Consideradas. Nomenclatura `NNNN-slug.md`. Guarda o raciocínio, não só o resultado.

---

## Artifact

Composições das camadas Foundation e Domain. Não redefinem regras — orquestram skills existentes e adicionam apenas a sequência e os detalhes específicos do artefato final.

### `create-rag-endpoint.md`

| Campo | Valor |
|---|---|
| **Frase-ativação** | "Crie o endpoint de query RAG" / "implemente o fluxo de busca + completion" |
| **Cria** | Dev Sênior + Tech Lead |
| **Consulta** | Dev, Copilot, Claude Code |
| **Frequência** | ●●○○○ Criação de novos endpoints RAG |

**Composição:** `azure-functions-endpoint` + `azure-ai-search-integration` + `azure-openai-completion` + `error-handling`

Checklist de geração: `validator` → `search` → `prompt-builder` → `completion` → `response-builder`.

---

### `create-integration-test.md`

| Campo | Valor |
|---|---|
| **Frase-ativação** | "Crie um teste de integração para esse endpoint" / "teste o fluxo search→completion" |
| **Cria** | QA + Dev Sênior |
| **Consulta** | Dev, Copilot, Claude Code |
| **Frequência** | ●●●●○ Após cada endpoint |

**Composição:** `testing-patterns` + fixtures de chunks/queries

Uso de `msw` para mock do Azure SDK. Cenários obrigatórios: happy path, resultado vazio, timeout, payload inválido.

---

### `create-react-card.md`

| Campo | Valor |
|---|---|
| **Frase-ativação** | "Crie o card de resposta do assistente" / "componente de feedback" |
| **Cria** | Dev Sênior (Front) |
| **Consulta** | Dev, Copilot |
| **Frequência** | ●●●○○ Componentes do painel |

**Composição:** `react-components` + `typescript-conventions`

Props: `query`, `answer`, `sources[]`, `feedbackCallback`. Renderiza fonte clicável, botões de thumbs up/down, estado de loading.

---

### `create-pipeline-stage.md`

| Campo | Valor |
|---|---|
| **Frase-ativação** | "Implemente o extractor" / "crie o chunker" / "indexe no Search" |
| **Cria** | Dev Sênior + Tech Lead |
| **Consulta** | Dev, Copilot, Claude Code |
| **Frequência** | ●●○○○ Desenvolvimento do pipeline |

**Composição:** `azure-ai-search-integration` + `error-handling` + `logging`

Cada stage (`extractor`, `chunker`, `embedder`, `indexer`) tem contrato de entrada/saída tipado em `src/shared/types.ts`.

---

### `create-adr.md`

| Campo | Valor |
|---|---|
| **Frase-ativação** | "Documente a decisão sobre X" / "gere o ADR de arquitetura" |
| **Cria** | Tech Lead |
| **Consulta** | Tech Lead, Product Specialist |
| **Frequência** | ●●○○○ Decisões arquiteturais |

**Composição:** `adr-template` + `project-structure`

Preenche automaticamente Contexto (problema de negócio) + Decisão (o que foi escolhido) + Consequências + Alternativas. Nomeia o arquivo seguindo `NNNN-slug.md` e o posiciona em `docs/adr/`.

---

### `create-spec-module.md`

| Campo | Valor |
|---|---|
| **Frase-ativação** | "Inicie o spec do módulo X" / "gere requirements + plan + tasks" |
| **Cria** | Product Specialist + Tech Lead |
| **Consulta** | Product Specialist, Tech Lead, Dev |
| **Frequência** | ●●●○○ Cada novo módulo do projeto |

**Composição:** `spec-sdd-template` + `project-structure`

Orquestra a criação dos três artefatos SDD (`requirements.md`, `plan.md`, `tasks.md`) na pasta correta de `/specs/<slug>/`.

---

## Mapa de dependências

```
Foundation
├── typescript-conventions  ◄── base de todo artefato de código
├── error-handling          ◄── base de todo artefato de código
├── logging                 ◄── consumida por domain e artifact
├── env-config              ◄── consumida por domain
└── project-structure       ◄── consumida por artifact e documentação

Domain
├── azure-functions-endpoint     ← typescript-conventions, error-handling, logging
├── azure-ai-search-integration  ← typescript-conventions, error-handling, env-config
├── azure-openai-completion      ← typescript-conventions, error-handling, env-config
├── testing-patterns             ← typescript-conventions
├── react-components             ← typescript-conventions
├── spec-sdd-template            ← (independente de código)
└── adr-template                 ← (independente de código)

Artifact
├── create-rag-endpoint      ← azure-functions-endpoint, azure-ai-search-integration,
│                               azure-openai-completion, error-handling
├── create-integration-test  ← testing-patterns
├── create-react-card        ← react-components, typescript-conventions
├── create-pipeline-stage    ← azure-ai-search-integration, error-handling, logging
├── create-adr               ← adr-template, project-structure
└── create-spec-module       ← spec-sdd-template, project-structure
```

---

## Quem cria cada camada

| Papel | Camada | Skills |
|---|---|---|
| Tech Lead | Foundation | Todas (5) |
| Tech Lead + Dev Sênior | Domain | azure-functions-endpoint, azure-ai-search-integration, azure-openai-completion |
| QA + Tech Lead | Domain | testing-patterns |
| Dev Sênior (Front) | Domain | react-components |
| Product Specialist + Tech Lead | Domain | spec-sdd-template |
| Tech Lead | Domain | adr-template |
| Dev Sênior + Tech Lead | Artifact | create-rag-endpoint, create-pipeline-stage |
| QA + Dev Sênior | Artifact | create-integration-test |
| Dev Sênior (Front) | Artifact | create-react-card |
| Tech Lead | Artifact | create-adr |
| Product Specialist + Tech Lead | Artifact | create-spec-module |
