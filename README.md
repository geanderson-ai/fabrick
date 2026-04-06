# Fabrick

**Versao:** v0.6

O **Fabrick** e um orquestrador declarativo de pipelines de IA, leve e extensivel, escrito em Python puro. Permite definir fluxos complexos -- ingestao de dados, execucao de chains e agents, decisoes condicionais, retries e finalizacao -- usando funcoes Python normais decoradas de forma declarativa, sem boilerplate.

## Arquitetura

```
fabrikk/
├── __init__.py              # exports: Fabrick, decorators, constants
├── core.py                  # Fabrick engine (run, start, stop, scheduling)
├── decorators.py            # @start, @step, @finish
├── context.py               # ExecutionContext
├── machine.py               # PipelineMachine (transitions wrapper)
├── contracts.py             # StepResult (pydantic)
├── exceptions.py            # all custom exceptions
├── constants.py             # ON, OFF, states, modes
├── agents/                  # agent decorators
│   ├── base.py              # agent_decorator() factory, AgentConfig
│   ├── spec.py              # @spec
│   ├── plan.py              # @plan
│   ├── execute.py           # @execute
│   ├── review.py            # @review
│   └── security.py          # @security
├── bridge/                  # Tear adapters
│   ├── tear.py              # TearBridge (path injection, module access)
│   ├── spec_adapter.py      # @spec ↔ SpecOrchestrator
│   ├── planner_adapter.py   # @plan ↔ run_followup_planner
│   ├── coder_adapter.py     # @execute ↔ run_autonomous_agent
│   ├── qa_adapter.py        # @review ↔ run_qa_validation_loop
│   └── security_adapter.py  # @security ↔ security scanners
├── providers/               # pluggable LLM providers
│   ├── base.py              # ProviderAdapter (ABC), ProviderConfig
│   ├── claude.py            # Anthropic API
│   ├── openrouter.py        # OpenRouter
│   ├── gemini.py            # Google Gemini
│   └── ollama.py            # Ollama (local, thinking disabled)
├── observability/           # tracing & metrics
│   ├── structlog_config.py  # dev/prod log setup
│   ├── langsmith.py         # LangSmith pipeline/step tracing
│   └── metrics.py           # PipelineMetrics, cost estimation
├── persistence/             # checkpoint stores
│   ├── base.py              # CheckpointStore (ABC)
│   ├── sqlite.py            # SQLite (dev)
│   ├── postgres.py          # PostgreSQL (prod, JSONB)
│   └── redis.py             # Redis (sorted sets, TTL)
├── scheduling/              # pipeline scheduling
│   ├── base.py              # SchedulerAdapter (ABC)
│   ├── apscheduler.py       # APScheduler (cron, interval, date)
│   └── cloud.py             # Google Cloud Scheduler
└── execution/               # execution modes
    ├── local.py             # run_sync, run_async
    ├── background.py        # run_in_background, run_in_thread
    ├── rq_worker.py         # Redis Queue
    └── celery_worker.py     # Celery distributed
```

## Instalacao

```bash
pip install -r requirements.txt
```

## Exemplos

### 1. Pipeline basico — execucao unica

O caso mais simples: definir steps com decorators e rodar uma vez.

```python
from fabrikk import Fabrick, start, step, finish

@start
def ingest(context):
    return {
        "status": "success",
        "data": {"raw": context.input},
        "next_state": "process"
    }

@step
def process(context):
    raw = context.data.get("raw", "")
    return {
        "status": "success",
        "data": {"processed": raw.upper()},
        "next_state": "save"
    }

@finish
def save(context):
    print(f"Resultado: {context.data}")
    return {"status": "success"}

pipeline = Fabrick(name="Basico")
pipeline.register(ingest, process, save)
result = pipeline.run(input="hello world")
# result.state == "completed"
# result.data == {"raw": "hello world", "processed": "HELLO WORLD"}
```

### 2. Escolhendo provider e modelo

O `provider` define qual LLM o pipeline usa. O provider resolve API keys via env vars
e configura o ambiente antes da execucao.

Providers disponiveis: `"ollama"` (padrao), `"claude"`, `"openrouter"`, `"gemini"`

```python
# Ollama local (padrao) — nao precisa de API key
pipeline = Fabrick(name="Local", provider="ollama", model="qwen2.5-coder:7b")

# Claude via Anthropic API — requer ANTHROPIC_API_KEY no .env
pipeline = Fabrick(name="Com Claude", provider="claude", model="sonnet")

# OpenRouter — requer OPENROUTER_API_KEY no .env
pipeline = Fabrick(name="Com OpenRouter", provider="openrouter", model="anthropic/claude-3.5-sonnet")

# Google Gemini — requer GOOGLE_API_KEY no .env
pipeline = Fabrick(name="Com Gemini", provider="gemini", model="gemini-2.0-flash")
```

O provider e o model ficam disponiveis no contexto de cada step:

```python
@step
def call_llm(context):
    print(context.provider)  # "CLAUDE"
    print(context.model)     # "claude-3-5-sonnet-20241022"
    # use context.provider/model para chamar a API que quiser
    return {"status": "success", "data": {}, "next_state": "next"}
```

### 3. Agendamento com cron

Passe `scheduler` com uma expressao cron e chame `.start()` em vez de `.run()`.
O pipeline roda em background via APScheduler.

```python
from fabrikk import Fabrick, start, step, finish

@start
def check_api(context):
    # chamada a uma API externa
    return {"status": "success", "data": {"healthy": True}, "next_state": "notify"}

@step
def notify(context):
    if not context.data.get("healthy"):
        print("ALERTA: API fora do ar!")
    return {"status": "success", "next_state": "done"}

@finish
def done(context):
    return {"status": "success"}

# Executa a cada 5 minutos
monitor = Fabrick(
    name="API Monitor",
    scheduler="*/5 * * * *",   # cron: minuto hora dia mes dia_semana
    provider="ollama",
)
monitor.register(check_api, notify, done)
monitor.start()   # nao bloqueia — roda em background thread
# monitor.stop()  # para o scheduler quando quiser
```

### 4. Execucao em background (sem cron)

Para rodar uma vez mas sem bloquear a thread principal:

```python
pipeline = Fabrick(
    name="Heavy Processing",
    execution_mode="background",   # "local" (padrao) | "background"
)
pipeline.register(ingest, process, save)
pipeline.start()  # retorna imediatamente, roda em thread separada
```

Ou usando a API direta para ter acesso ao Future:

```python
from fabrikk.execution import run_in_background

future = run_in_background(pipeline, input="data")
# ... faz outras coisas ...
result = future.result()  # bloqueia ate terminar
```

### 5. Retry automatico

```python
pipeline = Fabrick(
    name="Com Retry",
    retry=True,         # ativa retry em steps que retornam status="failed"
    max_retries=3,      # tentativas antes de falhar o pipeline (padrao: 3)
)
```

Se um step retorna `{"status": "failed", ...}`, o Fabrick re-executa aquele step
ate `max_retries` vezes antes de levantar `StepFailedError`.

### 6. Persistencia e observabilidade

Checkpoints sao salvos automaticamente apos cada step. Por padrao usa SQLite.

```python
pipeline = Fabrick(
    name="Prodution Pipeline",
    persistence="sqlite",       # "sqlite" (padrao) | "postgres" | "redis" | "none"
    observability="langsmith",  # "langsmith" | "none" (padrao)
)
```

Com `persistence="postgres"`, configure `DATABASE_URL` no .env.
Com `persistence="redis"`, configure `REDIS_URL` no .env.
Com `observability="langsmith"`, configure `LANGSMITH_API_KEY` no .env.

Metricas ficam no contexto apos a execucao:

```python
result = pipeline.run(input="data")
print(result.metadata["metrics"])  # total_elapsed, steps, cost estimate
print(result.total_tokens)         # total de tokens consumidos
print(result.total_cost)           # estimativa de custo em USD
```

### 7. Modo estrito (transicoes declaradas)

Por padrao qualquer step pode ir para qualquer outro. Ao usar `transitions_to`,
o Fabrick ativa modo estrito e valida cada transicao.

```python
from fabrikk import Fabrick, start, step, finish

@start(transitions_to=["validate"])
def ingest(context):
    return {"status": "success", "data": {}, "next_state": "validate"}

@step(transitions_to=["transform", "reject"])
def validate(context):
    is_valid = context.data.get("valid", True)
    return {
        "status": "success",
        "data": {},
        "next_state": "transform" if is_valid else "reject"
    }

@step(transitions_to=["save"])
def transform(context):
    return {"status": "success", "data": {}, "next_state": "save"}

@step(transitions_to=["save"])
def reject(context):
    return {"status": "success", "data": {"rejected": True}, "next_state": "save"}

@finish
def save(context):
    return {"status": "success"}

pipeline = Fabrick(name="Strict Pipeline")
pipeline.register(ingest, validate, transform, reject, save)
pipeline.run()
# Se validate tentar ir para "save" direto → InvalidTransitionError
```

### 8. Agent decorators — pipeline de IA completo

Os agent decorators (`@spec`, `@plan`, `@execute`, `@review`, `@security`) sao
`@step` especializados com metadata extra. Funcionam com qualquer provider.

```python
from fabrikk import Fabrick, spec, plan, execute, review, security

@spec(mode="task", transitions_to=["create_plan"])
def create_spec(context):
    return {
        "status": "success",
        "data": {"spec": "Criar endpoint /users com CRUD"},
        "next_state": "create_plan"
    }

@plan(transitions_to=["code"])
def create_plan(context):
    return {
        "status": "success",
        "data": {"plan": ["models.py", "routes.py", "tests.py"]},
        "next_state": "code"
    }

@execute(transitions_to=["qa"])
def code(context):
    return {
        "status": "success",
        "data": {"files_created": 3},
        "next_state": "qa"
    }

@review(transitions_to=["audit"])
def qa(context):
    return {
        "status": "success",
        "data": {"tests_passed": True},
        "next_state": "audit"
    }

@security(transitions_to=[])
def audit(context):
    return {
        "status": "success",
        "data": {"vulnerabilities": 0}
    }

pipeline = Fabrick(
    name="AI Dev Pipeline",
    provider="claude",
    model="sonnet",
    persistence="sqlite",
    observability="langsmith",
    retry=True,
)
pipeline.register(create_spec, create_plan, code, qa, audit)
result = pipeline.run(input="Criar sistema de autenticacao")
```

### 9. Exemplo completo — tudo junto

```python
from fabrikk import Fabrick, start, step, finish, ON

@start(transitions_to=["enrich"])
def ingest(context):
    return {
        "status": "success",
        "data": {"records": context.input},
        "next_state": "enrich"
    }

@step(transitions_to=["save"])
def enrich(context):
    records = context.data.get("records", [])
    enriched = [f"{r} [enriched]" for r in records]
    return {
        "status": "success",
        "data": {"enriched": enriched},
        "next_state": "save"
    }

@finish
def save(context):
    print(f"Salvou {len(context.data.get('enriched', []))} registros")
    return {"status": "success"}

pipeline = Fabrick(
    name="ETL Completo",
    provider="ollama",               # LLM local
    model="qwen2.5-coder:7b",       # modelo especifico
    scheduler="0 */2 * * *",        # a cada 2 horas
    persistence="sqlite",           # checkpoints locais
    observability="langsmith",      # tracing ativo
    retry=True,                     # retry em falhas
    max_retries=5,                  # ate 5 tentativas
)

pipeline.register(ingest, enrich, save)
pipeline.start()  # agenda e roda em background
```

## API do Fabrick()

| Parametro | Tipo | Padrao | Descricao |
|---|---|---|---|
| `name` | `str` | `"Fabrick Pipeline"` | Nome do pipeline (usado em logs e metricas) |
| `provider` | `str` | `"ollama"` | Provider LLM: `"ollama"`, `"claude"`, `"openrouter"`, `"gemini"` |
| `model` | `str` | `""` | Modelo especifico (ex: `"sonnet"`, `"qwen3:8b"`) |
| `scheduler` | `str \| None` | `None` | Expressao cron (ex: `"*/5 * * * *"`) |
| `start_at` | `str \| None` | `None` | Data/hora para execucao unica (ex: `"2025-01-15 14:00:00"`) |
| `execution_mode` | `str` | `"local"` | Modo: `"local"`, `"background"` |
| `persistence` | `str` | `"sqlite"` | Backend: `"sqlite"`, `"postgres"`, `"redis"`, `"none"` |
| `observability` | `str` | `"none"` | Tracing: `"langsmith"`, `"none"` |
| `retry` | `bool` | `False` | Ativa retry automatico em steps com falha |
| `max_retries` | `int` | `3` | Tentativas antes de falhar o pipeline |
| `machine_mode` | `str` | `"flexible"` | Modo da state machine: `"flexible"`, `"strict"` |

**Metodos:**

| Metodo | Descricao |
|---|---|
| `register(*fns)` | Registra funcoes decoradas como steps do pipeline |
| `run(input=None)` | Executa o pipeline sincronamente, retorna `ExecutionContext` |
| `start()` | Inicia com scheduler ou execution_mode configurado |
| `stop()` | Para o scheduler se estiver rodando |

## Variaveis de Ambiente

| Variavel | Provider/Feature |
|---|---|
| `ANTHROPIC_API_KEY` | Claude |
| `OPENROUTER_API_KEY` | OpenRouter |
| `GOOGLE_API_KEY` | Gemini |
| `OLLAMA_URL` | Ollama (padrao: `http://localhost:11434`) |
| `OLLAMA_MODEL` | Ollama (padrao: `qwen2.5-coder:7b`) |
| `DATABASE_URL` | Postgres persistence |
| `REDIS_URL` | Redis persistence |
| `LANGSMITH_API_KEY` | LangSmith observability |

## Dependencias Core

| Pacote | Uso |
|---|---|
| `pydantic` | Validacao de contratos (StepResult) |
| `transitions` | Maquinas de estado |
| `APScheduler` | Agendamento local |
| `structlog` | Logging estruturado |

## Principios de Design

- **Code-as-Configuration**: fluxo emerge do codigo e decorators, nao de YAML
- **State machine first**: todo pipeline tem ciclo de vida explicito
- **Adapters, nao acoplamento**: scheduler, cloud, DB e filas sao plugaveis
- **JSON como contrato**: cada step retorna payload padronizado
- **Cloud-agnostic**: integra com cloud sem lock-in
- **Observabilidade nativa**: tracing nao e opcional
