# TypeScript Conventions — NovaTech Assistant API

## Contexto

Esta skill define as convenções obrigatórias de TypeScript para o backend Node.js do NovaTech Assistant API, especialmente em Azure Functions v4.

Frase de ativação: **crie/modifique qualquer arquivo `.ts`**.

Agentes de IA devem ler este documento antes de gerar ou alterar qualquer código TypeScript.

## Regras prescritivas

1. Tipagem estrita sempre.
   - `noImplicitAny: true`
   - `strictNullChecks: true`
   - `strictPropertyInitialization: true`
   - `alwaysStrict: true`

2. Preferir `interface` para contratos de objeto públicos e `type` apenas quando necessário.
   - Use `interface` para objetos de entrada/saída e modelos de dados.
   - Use `type` para aliases, uniões, interseções e tipos mapeados.

3. Exports explícitos e nomeados.
   - Nunca use `export default` em Azure Functions v4 nem em bibliotecas internas do backend.
   - Exporte tudo com `export const`, `export function`, `export interface`, `export type`.

4. Proibido `any`, `unknown` sem validação, e `as any`.
   - Não use `any` em variáveis, parâmetros ou retornos.
   - Se precisar lidar com tipos dinâmicos, use validação com Zod ou mapeie para tipos fortemente tipados.

5. Async/await com tipo explícito de retorno.
   - Em funções assíncronas, declare `Promise<T>` como tipo de retorno.
   - Não deixe o retorno implícito em `async` functions.

6. Não use `Object` nem `[]` como tipos de objeto.
   - Use `Record<string, unknown>`, `unknown` validado ou interfaces específicas.

7. Parâmetros de função devem ser tipados de forma explícita.
   - Nunca dependa de inferência implícita para parâmetros de entrada.

8. Tipos de erros devem ser tratados e tipados.
   - Não use `catch (error)` sem tipagem e sem re-lançar ou registrar.

## Exemplos concretos

### DO: tipar variável simples

```ts
const userId: string = request.query.userId as string;
```

### DON'T: usar tipagem implícita/ny

```ts
const userId = request.query.userId;
const item: any = response.body;
```

### DO: usar interface para contrato público

```ts
export interface CreateOrderRequest {
  customerId: string;
  items: Array<{ sku: string; quantity: number }>;
}

export interface CreateOrderResponse {
  orderId: string;
  status: 'created' | 'pending';
}
```

### DON'T: usar `type` quando `interface` é a escolha correta

```ts
type CreateOrderRequest = {
  customerId: string;
  items: Array<{ sku: string; quantity: number }>;
};
```

### DO: async function com retorno tipado

```ts
export async function getOrderById(orderId: string): Promise<Order | null> {
  const order = await orderRepository.findById(orderId);
  return order;
}
```

### DON'T: async function sem tipo explícito

```ts
export async function getOrderById(orderId: string) {
  return orderRepository.findById(orderId);
}
```

### DO: resposta HTTP tipada e segura

```ts
export interface HttpJsonResponse<T> {
  status: number;
  jsonBody: T;
}

export function createHttpResponse<T>(body: T, status = 200): HttpJsonResponse<T> {
  return {
    status,
    jsonBody: body,
  };
}
```

### DON'T: tipar o body do HTTP response como objeto JSON genérico

```ts
export function createHttpResponse(body: object, status = 200) {
  return {
    status,
    body,
  };
}
```

### DO: tipar corretamente o catch

```ts
try {
  return await fetchOrderData();
} catch (error: unknown) {
  const safeError = normalizeError(error);
  logger.error('Falha ao buscar pedido', { error: safeError });
  throw safeError;
}
```

### DON'T: engolir erros em catch

```ts
try {
  return await fetchOrderData();
} catch (error) {
  console.error(error);
  return null;
}
```

## Anti-padrões proibidos

1. `export default` em Azure Functions v4.
   - Azure Functions v4 exige exports nomeados para triggers e handlers.

2. Tipar a resposta HTTP usando `body` em vez de `jsonBody`.
   - Use o contrato de resposta do projeto: `status` + `jsonBody`, não `body` genérico.

3. Declarar `any` ou `as any` sem validação.
   - `any` oculta erros e quebra a segurança do tipo.

4. Ignorar validação de payloads de entrada.
   - Todo payload externo deve passar por validação de schema antes de ser usado.

5. Engolir erros dentro de `try/catch` sem lançar ou registrar.
   - Isso mascara falhas e produz comportamentos silenciosos.

6. Usar `Object`, `[]`, `Record<string, any>` ou tipos amplos semelhantes para dados estruturados.
   - Prefira interfaces e tipos explicitos.

7. Usar inferência implícita para parâmetros de função importantes.
   - Parâmetros de entrada devem ser declarados explicitamente.

8. Declarar `unknown` sem conversão ou validação.
   - Para dados externos, valide e transforme para tipos seguros antes de usar.

## Observações rápidas

- Mantenha o código alinhado com `tsconfig.json` do projeto e com o estilo de exportação de módulos ES/Node.js.
- Todos os arquivos `.ts` deste backend devem ser gerados com tipos explícitos e sem atalhos de `any`.
- Este documento é prescritivo: siga-o exatamente ao gerar código TypeScript para o NovaTech Assistant API.
