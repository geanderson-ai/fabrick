# modulo_logging_config — Especificação Técnica (Configuração de Logging)

## 1) Visão geral

O módulo `logging_config` é responsável por configurar o sistema de logging estruturado para a aplicação Fabrick, utilizando a biblioteca `structlog`. Ele fornece uma configuração que se adapta ao ambiente de execução: logs coloridos e legíveis por humanos em terminais TTY (desenvolvimento) e logs em formato JSON em outros ambientes (produção/CI).

**Arquivos e referências:**
- Implementação: [logging_config.py](file:///c:/Users/User/OneDrive%20-%20Boreal/Documentos/newcode/faktory-builder/fabrick/fabrikk/logging_config.py)

## 2) Responsabilidades

- Configurar o `structlog` com uma cadeia de processadores padrão.
- Detectar se a saída está sendo direcionada para um terminal interativo (`isatty()`).
- Aplicar o `ConsoleRenderer` (logs coloridos) para ambientes de desenvolvimento.
- Aplicar o `JSONRenderer` (logs estruturados) para ambientes de produção.
- Fornecer uma função `get_logger` que retorna uma instância de logger do `structlog`.
- Incluir processadores para adicionar contexto (`contextvars`), nível de log, informações de stack, exceções e timestamp.

## 3) Dependências

**Dependências internas:**
- Nenhuma.

**Dependências externas (runtime):**
- `structlog`: A biblioteca principal para logging estruturado.
- `logging`, `sys`: Módulos padrão do Python usados para a configuração.

## 4) Interfaces (Entradas/Saídas)

### 4.1 API pública

**Funções**
- `configure_logging(log_level=logging.INFO) -> None`
  - `log_level`: O nível mínimo de log a ser processado (ex: `logging.DEBUG`, `logging.INFO`).
  - Configura o sistema de logging globalmente. Esta função deve ser chamada uma vez na inicialização da aplicação.

- `get_logger(name=None) -> BoundLogger`
  - `name`: Um nome opcional para o logger (usado para contextualização).
  - Retorna um logger `structlog` pronto para uso.

## 5) Arquitetura interna

### 5.1 Lógica de Configuração (`configure_logging`)

1.  **Processadores Compartilhados:** Define uma lista `shared_processors` com a lógica comum a todos os ambientes:
    - `structlog.contextvars.merge_contextvars`: Adiciona dados de `contextvars` ao log.
    - `structlog.processors.add_log_level`: Adiciona o nível do log (info, debug, etc.).
    - `structlog.processors.StackInfoRenderer`: Renderiza informações de stack.
    - `structlog.dev.set_exc_info`: Adiciona informações de exceção.
    - `structlog.processors.TimeStamper`: Adiciona um timestamp.

2.  **Detecção de Ambiente:** Verifica `sys.stderr.isatty()`.
    - Se `True` (terminal interativo), adiciona o `structlog.dev.ConsoleRenderer()` à lista de processadores.
    - Se `False` (pipe, arquivo, etc.), adiciona `structlog.processors.dict_tracebacks` e `structlog.processors.JSONRenderer()`.

3.  **Configuração Final:** Chama `structlog.configure()` com:
    - A lista de processadores montada.
    - `wrapper_class` para filtrar logs pelo `log_level`.
    - `logger_factory` para definir como os logs são finalmente emitidos.

## 6) Fluxos de dados e execução

1.  A aplicação principal (ou o ponto de entrada do Fabrick) chama `configure_logging()` no início do processo.
2.  Qualquer módulo que precise logar chama `logger = get_logger()` para obter uma instância do logger.
3.  Quando `logger.info("mensagem", chave="valor")` é chamado:
    - O `structlog` passa o evento e os dados através da cadeia de processadores.
    - O último processador (`ConsoleRenderer` ou `JSONRenderer`) formata a saída final.
    - O `PrintLoggerFactory` escreve a saída formatada para `stderr`.

## 7) Diagramas

### 7.1 Diagrama de fluxo da configuração

```mermaid
graph TD
    A[Chama configure_logging()] --> B{sys.stderr.isatty()?};
    B -- True --> C[Usa ConsoleRenderer];
    B -- False --> D[Usa JSONRenderer];
    C --> E[structlog.configure()];
    D --> E;
    E --> F[Logging configurado];
```

## 8) APIs expostas (contratos e convenções)

- A convenção é chamar `configure_logging()` o mais cedo possível no ciclo de vida da aplicação.
- O `get_logger()` deve ser usado em todos os módulos para obter uma instância de logger consistente.

## 9) Algoritmos principais

- A lógica principal é a seleção condicional do renderer com base na detecção de TTY, que é um padrão comum para criar ferramentas de linha de comando com boa experiência de usuário.

## 10) Casos de uso suportados

- Logging legível e colorido durante o desenvolvimento local.
- Logging em formato JSON, ideal para ingestão por sistemas de agregação de logs (como ELK, Splunk, Datadog) em produção.
- Enriquecimento automático de logs com timestamps, níveis e contexto.

## 11) Requisitos de performance

- A configuração do logging tem um custo único e baixo na inicialização.
- O `structlog` é projetado para ser eficiente, mas o logging excessivo em um pipeline de alta frequência (especialmente em nível `DEBUG`) pode impactar a performance. O nível de log deve ser ajustado adequadamente para o ambiente de produção.

## 12) Testes unitários necessários

- `configure_logging` deve configurar o `structlog` com `ConsoleRenderer` quando `isatty` for `True`.
- `configure_logging` deve configurar o `structlog` com `JSONRenderer` quando `isatty` for `False`.
- `get_logger` deve retornar uma instância de logger do `structlog`.
- Testar (com mocks) que os processadores corretos são passados para `structlog.configure` em cada cenário.

## 13) Pontos de extensão e refatoração

- **Configuração por Variável de Ambiente:** O `log_level` poderia ser lido de uma variável de ambiente (ex: `LOG_LEVEL`) para permitir a alteração da verbosidade sem modificar o código.
- **Integração com `logging` padrão:** A configuração poderia ser ajustada para rotear os logs da biblioteca padrão `logging` através do `structlog`, unificando a saída de logs de bibliotecas de terceiros.
- **Processadores Customizados:** Novos processadores poderiam ser adicionados para enriquecer os logs com informações específicas da aplicação (ex: ID da execução do pipeline).
