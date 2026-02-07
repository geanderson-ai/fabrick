# Fabrick

**Versão:** v0.2

O **Fabrick** é um orquestrador de pipelines leve e flexível, projetado para facilitar a criação, execução e monitoramento de fluxos de trabalho em Python. Ele foca em simplicidade para o desenvolvedor, permitindo definir pipelines complexos com decorators intuitivos e configuração declarativa.

## 🚀 Features Implementadas (v0.2)

### Core Runtime
- **Definição Declarativa:** Criação de pipelines claros e legíveis.
- **Decorators Intuitivos:** `@start`, `@step` e `@finish` para marcar as funções do pipeline.
- **Gerenciamento de Contexto:** Objeto `ExecutionContext` para passar dados entre os passos de forma segura.
- **Validação de Fluxo:** Garantia de integridade do pipeline (validação de `next_state` e presença de steps obrigatórios).

### Agendamento (Scheduling)
- **Integração com APScheduler:** Suporte nativo para agendamento de tarefas.
- **Tipos de Triggers Suportados:**
    - **Cron:** Estilo crontab UNIX (ex: `"0 12 * * *"`).
    - **Intervalo:** Execução periódica.
    - **Data Fixa:** Execução única em data/hora específica.

### Máquina de Estados
- **Integração com `transitions`:** Backbone formal de máquina de estados via `PipelineMachine`.
- **Ciclo de vida explícito:** Estados `idle` → steps → `completed` / `failed` com transições validadas.
- **Modo Flexível (padrão):** Qualquer step pode transicionar para qualquer outro — comportamento idêntico ao v0.1.
- **Modo Estrito (opt-in):** Transições restritas às declaradas via `@step(transitions_to=[...])`. Ativado automaticamente quando qualquer step usa `transitions_to`.
- **Decorators dual-mode:** `@step` (bare) continua funcionando; `@step(transitions_to=["next"])` ativa validação de transições.
- **Rastreamento de estado:** `context.state` reflete o estado atual e `context.state_history` registra a sequência completa.
- **`InvalidTransitionError`:** Exceção específica (subclasse de `RuntimeError`) para transições inválidas em modo estrito.
- **Re-execução:** Machine reseta automaticamente para `idle` ao chamar `run()` novamente.

### Observabilidade
- **Logging Estruturado:** Sistema de logs robusto utilizando `structlog`.
    - **Desenvolvimento:** Logs coloridos e formatados para fácil leitura no console.
    - **Produção:** Logs em formato JSON estruturado para ingestão em ferramentas de monitoramento.
- **Rastreamento de Execução:** Logs detalhados de início, fim, transições de estado e erros em cada step.

## 📦 Instalação

```bash
pip install -r requirements.txt
```

## 🛠️ Exemplo de Uso

```python
from fabrikk import Fabrick, start, step, finish, ON

# 1. Defina os steps do seu pipeline
@start
def ingest_data(context):
    return {
        "status": "success",
        "data": {"raw": context.input},
        "next_state": "process_data"
    }

@step
def process_data(context):
    # Lógica de processamento...
    return {
        "status": "success",
        "data": {"processed": True},
        "next_state": "save_result"
    }

@finish
def save_result(context):
    print(f"Salvando: {context.data}")
    return {"status": "success"}

# 2. Configure o Pipeline
workflow = Fabrick(
    name="Data Pipeline",
    scheduler="*/5 * * * *",  # Executa a cada 5 minutos
    execution_mode="local"
)

# 3. Registre e Execute
workflow.register(ingest_data, process_data, save_result)
workflow.start()
```

### Modo Estrito (Transições Declaradas)

```python
from fabrikk import Fabrick, start, step, finish

@start(transitions_to=["validate"])
def ingest(context):
    return {"status": "success", "data": {}, "next_state": "validate"}

@step(transitions_to=["transform", "reject"])
def validate(context):
    is_valid = True  # lógica de validação
    next_step = "transform" if is_valid else "reject"
    return {"status": "success", "data": {}, "next_state": next_step}

@step(transitions_to=["save"])
def transform(context):
    return {"status": "success", "data": {}, "next_state": "save"}

@step(transitions_to=["save"])
def reject(context):
    return {"status": "success", "data": {}, "next_state": "save"}

@finish
def save(context):
    return {"status": "success", "data": {"result": "done"}}

pipeline = Fabrick(name="Strict Pipeline")
pipeline.register(ingest, validate, transform, reject, save)
pipeline.run()  # transições validadas pela máquina de estados
```

## 🗺️ Roadmap

Funcionalidades planejadas para as próximas versões:

### Orquestração e Resiliência
- [ ] **Sistema de Retry:** Implementação de políticas de retentativa automática (backoff exponencial) com `tenacity`.
- [x] **Máquinas de Estado:** Integração com `transitions` — modo flexível e estrito, rastreamento de estado, callbacks de observabilidade.
- [ ] **Persistência de Estado:**
    - [ ] SQLite (Desenvolvimento local)
    - [ ] PostgreSQL (Produção via `sqlalchemy`/`psycopg2`)
    - [ ] Redis (Cache e Locks)

### Execução Escalável
- [ ] **Filas de Tarefas:** Suporte a execução assíncrona via `rq` (Redis Queue).
- [ ] **Execução Distribuída:** Integração com `celery` para cargas de trabalho pesadas.
- [ ] **Cloud Native:** Adaptadores para Google Cloud Functions e Cloud Run.

### IA e Observabilidade Avançada
- [ ] **Integração com LangChain/LangGraph:** Suporte nativo para orquestração de agentes de IA.
- [ ] **LangSmith:** Integração profunda para tracing e debug de chains de IA.
