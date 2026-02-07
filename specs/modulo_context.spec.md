# modulo_context — Especificação Técnica (Contexto de Execução)

## 1) Visão geral

O módulo `context` define a classe `ExecutionContext`, que serve como um contêiner de dados para o estado de uma execução de pipeline do Fabrick. Ele é instanciado pelo `Fabrick.run()` e passado para cada step durante a execução, carregando informações sobre a entrada inicial, o estado atual e o histórico de transições.

**Arquivos e referências:**
- Implementação: [context.py](file:///c:/Users/User/OneDrive%20-%20Boreal/Documentos/newcode/faktory-builder/fabrick/fabrikk/context.py)
- Core do Fabrick: [core.py](file:///c:/Users/User/OneDrive%20-%20Boreal/Documentos/newcode/faktory-builder/fabrick/fabrikk/core.py)

## 2) Responsabilidades

- Manter os dados de entrada (`input`) fornecidos na chamada do `run()`.
- Rastrear o estado atual (`state`) da máquina de estados do pipeline.
- Armazenar metadados (`metadata`) que podem ser passados entre os steps.
- Manter um histórico de todos os estados (`state_history`) pelos quais a execução passou.

## 3) Dependências

**Dependências internas:**
- Nenhuma.

**Dependências externas (runtime):**
- Nenhuma.

## 4) Interfaces (Entradas/Saídas)

### 4.1 API pública (classe ExecutionContext)

**Construtor**
- `ExecutionContext(input=None, state=None, metadata=None)`
  - `input`: Os dados iniciais para a execução do pipeline.
  - `state`: O estado inicial da máquina de estados.
  - `metadata`: Um dicionário opcional para metadados. Se `None`, é inicializado como `{}`.

**Atributos**
- `input`: Armazena os dados de entrada.
- `state`: Armazena o nome do estado atual.
- `metadata`: Dicionário para dados compartilhados entre os steps.
- `state_history`: Lista que armazena a sequência de estados visitados.

## 5) Arquitetura interna

`ExecutionContext` é uma classe de dados simples (POPO - Plain Old Python Object) sem lógica de negócios complexa. Sua principal função é agregar e transportar o estado da execução.

## 6) Fluxos de dados e execução

1. Uma instância de `ExecutionContext` é criada no início de `Fabrick.run()`, recebendo o `input_data`.
2. O `Fabrick.run()` atualiza `context.state` e `context.state_history` a cada transição de estado bem-sucedida.
3. O objeto `context` é passado como o único argumento para cada função de step.
4. Os steps podem ler `context.input` e `context.metadata`, e podem modificar `context.metadata` para passar informações para os steps seguintes.

## 7) Diagramas

### 7.1 Diagrama de componentes

```mermaid
flowchart LR
  Core["Fabrick (core)"] -->|cria e gerencia| Ctx["ExecutionContext"]
  Ctx -->|é passado para| Step["Função de Step"]
```

## 8) APIs expostas (contratos e convenções)

- O `ExecutionContext` é o contrato de dados fundamental entre o runtime do Fabrick e as funções de step.
- Por convenção, os steps devem tratar o `input` e o `state` como somente leitura, modificando apenas o `metadata` quando necessário.

## 9) Algoritmos principais

- Não há algoritmos complexos neste módulo.

## 10) Casos de uso suportados

- Passar dados de entrada para o primeiro step de um pipeline.
- Permitir que steps acessem o estado atual da execução.
- Manter um histórico de execução para fins de logging ou depuração.
- Compartilhar metadados entre diferentes steps de um mesmo pipeline.

## 11) Requisitos de performance

- A criação e o acesso aos atributos de `ExecutionContext` são operações de custo `O(1)`, com impacto insignificante na performance geral do pipeline.

## 12) Testes unitários necessários

- O construtor deve inicializar `input`, `state` e `metadata` corretamente.
- `metadata` deve ser um dicionário vazio se não for fornecido.
- `state_history` deve ser uma lista vazia na inicialização.

## 13) Pontos de extensão e refatoração

- **Validação de dados:** Pydantic poderia ser usado para definir um esquema para `input` e `metadata`, garantindo que os dados passados entre os steps sigam um contrato mais estrito.
- **Agregação de dados de steps:** Conforme observado em `modulo_core.spec.md`, o contexto atualmente não agrega o campo `data` retornado por cada step. Uma futura refatoração poderia adicionar um atributo `data` ao contexto para acumular os resultados de cada step.
- **Imutabilidade:** Para evitar modificações acidentais, os atributos `input` e `state` poderiam ser expostos como propriedades somente leitura.
