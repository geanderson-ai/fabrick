# Fabrick

**Versão:** v0.1

O **Fabrick** é um orquestrador de pipelines leve e flexível, projetado para facilitar a criação, execução e monitoramento de fluxos de trabalho em Python. Ele foca em simplicidade para o desenvolvedor, permitindo definir pipelines complexos com decorators intuitivos e configuração declarativa.

## 🚀 Features Implementadas (v0.1)

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

## 🗺️ Roadmap

Funcionalidades planejadas para as próximas versões:

### Orquestração e Resiliência
- [ ] **Sistema de Retry:** Implementação de políticas de retentativa automática (backoff exponencial) com `tenacity`.
- [ ] **Máquinas de Estado:** Integração avançada com `transitions` para fluxos complexos.
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
