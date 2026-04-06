# Fabrick — Plano de Implementação e Integração com Tear

**Versão:** v0.3-draft
**Data:** 2026-04-05

---

## 1. Visão Geral da Arquitetura

O Fabrick orquestra pipelines de IA usando **decorators Python** que mapeiam diretamente para fases de um agente autônomo. O Tear fornece a engine de agentes (planner, coder, QA, security). O Fabrick é a **cola declarativa** entre eles.

```
┌─────────────────────────────────────────────────────────┐
│                    FABRICK PIPELINE                      │
│                                                         │
│  @spec ──► @plan ──► @execute ──► @review ──► @security │
│    │         │          │           │            │       │
│    ▼         ▼          ▼           ▼            ▼       │
│  Auto-    Auto-      Auto-       Auto-        Auto-     │
│  Claude   Claude     Claude      Claude       Claude    │
│  Spec     Planner    Coder       QA Loop      Security  │
│  Pipeline            + Fixer     Reviewer     Scanner   │
│                                                         │
│  ┌─────────────────────────────────────────────────┐    │
│  │         ExecutionContext (state machine)         │    │
│  │  state_history · data · metadata · checkpoints  │    │
│  └─────────────────────────────────────────────────┘    │
│                                                         │
│  Providers: Claude API │ OpenRouter │ Gemini │ Ollama   │
└─────────────────────────────────────────────────────────┘
```

---

## 2. Sistema de Decorators

### 2.1 Decorators Base (herdados do v0.2)

| Decorator | Papel | Contrato de Retorno |
|-----------|-------|---------------------|
| `@start` | Primeiro step do pipeline | `{status, data, next_state, metadata}` |
| `@step` | Step intermediário genérico | `{status, data, next_state, metadata}` |
| `@finish` | Último step (sem `next_state`) | `{status, data, metadata}` |

### 2.2 Decorators de Agente (novos — v0.3)

Decorators especializados que encapsulam fases do Tear. Cada um é um `@step` com comportamento pré-definido, provider-aware, e integração com o Claude Agent SDK.

#### `@spec` — Criação de Especificação

```python
from fabrick import Fabrick, spec, plan, execute, review, security

@spec(
    mode="interactive",         # interactive | task | auto
    complexity="auto",          # auto | simple | moderate | complex
    transitions_to=["plan"],
)
async def create_spec(context):
    """
    Wraps: Tear spec/pipeline.py → SpecOrchestrator
    
    Recebe uma descrição de tarefa no context.input.
    Executa o pipeline de spec: discovery → research → writing → critique.
    Gera: spec.md, requirements.json, context.json
    
    Retorna:
        status: "success" | "failed"
        data:
            spec_dir: str        — caminho da spec gerada
            complexity: str      — simple | moderate | complex
            requirements: list   — lista de requisitos extraídos
        next_state: "plan"
    """
```

**Mapeamento Tear:**
- `spec/pipeline.py` → `SpecOrchestrator`
- `spec/discovery.py` → análise do projeto
- `spec/critique.py` → auto-crítica da spec
- `spec/complexity.py` → avaliação de complexidade

---

#### `@plan` — Planejamento de Implementação

```python
@plan(
    max_phases=10,              # máximo de fases no plano
    parallel_subtasks=True,     # permitir subtasks paralelas
    transitions_to=["execute"],
)
async def create_plan(context):
    """
    Wraps: Tear agents/planner.py → run_followup_planner()
    
    Lê a spec gerada pelo @spec.
    Cria um implementation_plan.json com fases e subtasks.
    
    Retorna:
        status: "success" | "failed"
        data:
            plan_path: str           — caminho do implementation_plan.json
            total_phases: int        — número de fases
            total_subtasks: int      — número total de subtasks
            estimated_complexity: str — low | medium | high
        next_state: "execute"
    """
```

**Mapeamento Tear:**
- `agents/planner.py` → `run_followup_planner()`
- `planner_lib/` → geração e parsing do plano
- `implementation_plan/` → modelos de fases/subtasks
- `prompts/planner.md` → system prompt do planner

---

#### `@execute` — Execução do Código

```python
@execute(
    max_retries=3,                    # retentativas por subtask
    retry_delay="exponential",        # exponential | fixed | linear
    parallel_agents=1,                # agentes paralelos (worktrees)
    auto_commit=True,                 # commit automático a cada subtask
    transitions_to=["review", "execute"],  # pode re-entrar (loop de subtasks)
)
async def build_code(context):
    """
    Wraps: Tear agents/coder.py → run_autonomous_agent()
    
    Executa o loop principal do coder:
      1. Pega próxima subtask pendente
      2. Gera prompt com contexto
      3. Executa agente (Claude/Ollama)
      4. Valida resultado
      5. Commita
      6. Repete até todas subtasks completas
    
    Retorna:
        status: "success" | "failed" | "partial"
        data:
            completed_subtasks: int
            total_subtasks: int
            commits: list[str]      — hashes dos commits
            errors: list[dict]      — erros encontrados
        next_state: "review" | "execute"  — "execute" se subtasks restantes
    """
```

**Mapeamento Tear:**
- `agents/coder.py` → `run_autonomous_agent()`
- `agents/session.py` → `run_agent_session()`
- `agents/base.py` → retry, rate limit, recovery
- `prompts/coder.md` → system prompt do coder
- `prompts/coder_recovery.md` → prompt de recuperação
- `recovery.py` → `RecoveryManager`

---

#### `@review` — Revisão de Qualidade (QA)

```python
@review(
    max_iterations=50,              # máximo de ciclos review→fix
    auto_fix=True,                  # rodar fixer automaticamente se rejeitado
    escalate_after=3,               # escalar para humano após N issues recorrentes
    transitions_to=["security", "execute"],  
)
async def qa_review(context):
    """
    Wraps: Tear qa/loop.py → run_qa_validation_loop()
    
    Executa o loop de QA:
      1. QA Reviewer valida contra acceptance criteria
      2. Se rejeitado → QA Fixer corrige
      3. Re-review
      4. Loop até aprovado ou max_iterations
    
    Retorna:
        status: "approved" | "rejected" | "escalated"
        data:
            iterations: int          — quantas rodadas de review
            issues_found: list[dict] — issues encontrados
            issues_fixed: list[dict] — issues corrigidos
            recurring_issues: list   — issues que voltaram 3+ vezes
            qa_report_path: str      — caminho do qa_report.md
        next_state: "security" (se approved) | "execute" (se precisa mais code)
    """
```

**Mapeamento Tear:**
- `qa/loop.py` → `run_qa_validation_loop()`
- `qa/reviewer.py` → `run_qa_agent_session()`
- `qa/fixer.py` → `run_qa_fixer_session()`
- `qa/criteria.py` → `get_qa_signoff_status()`
- `qa/report.py` → tracking de iterações, issues recorrentes
- `prompts/qa_reviewer.md` / `prompts/qa_fixer.md`

---

#### `@security` — Validação de Segurança

```python
@security(
    scan_secrets=True,              # escanear por secrets expostos
    validate_commands=True,         # validar comandos bash executados
    check_dependencies=True,        # checar vulnerabilidades em deps
    fail_on="critical",             # critical | high | medium | low
    transitions_to=["finish"],
)
async def security_scan(context):
    """
    Wraps: Tear security/ + analysis/security_scanner.py
    
    Executa validações de segurança:
      1. Scan de secrets no código (scan_secrets.py)
      2. Validação de comandos contra allowlist (validator.py)
      3. Análise de risco do código (risk_classifier.py)
      4. Scan de vulnerabilidades em dependências
    
    Retorna:
        status: "pass" | "warn" | "fail"
        data:
            secrets_found: list[dict]     — secrets expostos
            risky_commands: list[dict]    — comandos perigosos
            vulnerabilities: list[dict]   — CVEs em dependências
            risk_level: str               — critical | high | medium | low
            report_path: str              — caminho do security_report.md
        next_state: "finish"
    """
```

**Mapeamento Tear:**
- `security/main.py` → facade de segurança
- `security/validator.py` → validação de comandos
- `security/scan_secrets.py` → detecção de secrets
- `analysis/security_scanner.py` → scan de código
- `analysis/risk_classifier.py` → classificação de risco
- `security/profile.py` → perfis de segurança por projeto

---

## 3. Pipeline Completo — Exemplo de Uso

```python
from fabrick import Fabrick, spec, plan, execute, review, security, finish, ON

@spec(mode="task", transitions_to=["create_plan"])
async def create_spec(context):
    result = await run_spec_pipeline(context.data["project_dir"], context.input)
    return {
        "status": "success",
        "data": {"spec_dir": result.spec_dir, "complexity": result.complexity},
        "next_state": "create_plan",
    }

@plan(transitions_to=["build"])
async def create_plan(context):
    success = await run_planner(context.data["project_dir"], context.data["spec_dir"])
    return {
        "status": "success" if success else "failed",
        "data": {"plan_ready": success},
        "next_state": "build",
    }

@execute(max_retries=3, parallel_agents=2, transitions_to=["qa", "build"])
async def build(context):
    result = await run_coder(context.data["project_dir"], context.data["spec_dir"])
    next_step = "qa" if result.all_complete else "build"
    return {
        "status": "success",
        "data": {"completed": result.completed, "total": result.total},
        "next_state": next_step,
    }

@review(max_iterations=10, auto_fix=True, transitions_to=["scan", "build"])
async def qa(context):
    approved = await run_qa_loop(context.data["project_dir"], context.data["spec_dir"])
    return {
        "status": "approved" if approved else "rejected",
        "data": {"approved": approved},
        "next_state": "scan" if approved else "build",
    }

@security(scan_secrets=True, fail_on="high", transitions_to=["done"])
async def scan(context):
    report = await run_security_scan(context.data["project_dir"])
    return {
        "status": "pass" if report.passed else "fail",
        "data": {"risk_level": report.risk_level},
        "next_state": "done",
    }

@finish
async def done(context):
    return {"status": "success", "data": {"pipeline": "complete"}}


# --- Configuração e execução ---

pipeline = Fabrick(
    name="Tear Full Pipeline",
    execution_mode="local",
    observability="langsmith",
    retry=ON,
)

pipeline.register(create_spec, create_plan, build, qa, scan, done)
pipeline.run(input="Criar sistema de autenticação com OAuth2")
```

---

## 4. Máquina de Estados

```
                    ┌──────────────────────────┐
                    │                          │
  idle ──► spec ──► plan ──► execute ──► review ──► security ──► completed
                              ▲    │      │   │
                              │    │      │   │
                              └────┘      └───┘
                           (subtasks     (fix →
                            restantes)   re-review)
                            
  Qualquer estado ──► failed (em caso de erro não-recuperável)
```

**Modo Flexível (padrão):** Qualquer transição é válida.
**Modo Estrito:** Apenas transições declaradas via `transitions_to=[]` são permitidas.

---

## 5. ExecutionContext

O contexto compartilhado entre todos os steps:

```python
@dataclass
class ExecutionContext:
    # Identidade
    pipeline_name: str
    run_id: str                    # UUID único por execução
    
    # Entrada
    input: Any                     # dado inicial do pipeline
    
    # Estado
    state: str                     # estado atual da máquina
    state_history: list[str]       # histórico completo de transições
    
    # Dados acumulados (cada step pode ler/escrever)
    data: dict[str, Any]           # payload compartilhado
    metadata: dict[str, Any]       # metadados (timing, tokens, custos)
    
    # Configuração do provider
    provider: str                  # CLAUDE | OPENROUTER | GEMINI | OLLAMA
    model: str                     # modelo resolvido
    
    # Caminhos
    project_dir: Path
    spec_dir: Path | None
    
    # Observabilidade
    start_time: datetime
    step_timings: dict[str, float] # tempo de cada step em segundos
    total_tokens: int              # tokens consumidos no pipeline
    total_cost: float              # custo estimado (USD)
    
    # Checkpoints (para retry/recovery)
    last_checkpoint: str | None
    checkpoint_data: dict[str, Any]
```

---

## 6. Integração com Providers (Ollama incluso)

Cada decorator herda a configuração de provider do `Fabrick()`:

```python
# Ollama local
pipeline = Fabrick(
    name="Local Pipeline",
    provider="ollama",              # auto-configura OLLAMA_URL + OLLAMA_MODEL
    model="qwen3:14b",
)

# OpenRouter
pipeline = Fabrick(
    name="Cloud Pipeline",
    provider="openrouter",
    model="kimi",
)

# Claude direto
pipeline = Fabrick(
    name="Claude Pipeline",
    provider="claude",
    model="sonnet",
)
```

A resolução de modelo segue a cadeia:

```
Fabrick(model=) → resolve_model_id() → provider.models → OLLAMA_MODEL env → default
```

Para Ollama, thinking tokens são automaticamente desabilitados (`max_thinking_tokens=None`).

---

## 7. Plano de Implementação — Fases

### Fase 1: Core `fabrick` (pacote Python)

```
fabrick/
├── __init__.py              # exports públicos
├── core.py                  # classe Fabrick
├── decorators.py            # @start, @step, @finish
├── context.py               # ExecutionContext
├── machine.py               # PipelineMachine (wrapper do transitions)
├── contracts.py             # StepResult (pydantic model do retorno)
├── exceptions.py            # InvalidTransitionError, StepFailedError
└── constants.py             # ON, OFF, estados default
```

**Entrega:** Pipeline funcional com decorators base, state machine, contexto, modo flexível e estrito.

### Fase 2: Decorators de Agente

```
fabrick/
├── agents/
│   ├── __init__.py
│   ├── base.py              # AgentDecorator (classe base)
│   ├── spec.py              # @spec
│   ├── plan.py              # @plan
│   ├── execute.py           # @execute
│   ├── review.py            # @review
│   └── security.py          # @security
```

**Entrega:** Decorators agente que wrappam funções do Tear. Cada um configura automaticamente o client, provider, model, e thinking tokens.

### Fase 3: Bridge com Tear

```
fabrick/
├── bridge/
│   ├── __init__.py
│   ├── tear.py       # adapter principal
│   ├── spec_adapter.py      # bridge @spec ↔ SpecOrchestrator
│   ├── planner_adapter.py   # bridge @plan ↔ run_followup_planner
│   ├── coder_adapter.py     # bridge @execute ↔ run_autonomous_agent
│   ├── qa_adapter.py        # bridge @review ↔ run_qa_validation_loop
│   └── security_adapter.py  # bridge @security ↔ security scanners
```

**Entrega:** Adapters que traduzem o contrato JSON do Fabrick para as interfaces async do Tear e vice-versa.

### Fase 4: Provider Layer

```
fabrick/
├── providers/
│   ├── __init__.py
│   ├── base.py              # ProviderAdapter (interface)
│   ├── claude.py            # Claude via SDK
│   ├── openrouter.py        # OpenRouter via ANTHROPIC_BASE_URL
│   ├── gemini.py            # Gemini
│   └── ollama.py            # Ollama (OLLAMA_URL + OLLAMA_MODEL)
```

**Entrega:** Providers plugáveis. O Ollama provider configura automaticamente `ANTHROPIC_BASE_URL`, token dummy, e desabilita thinking tokens.

### Fase 5: Observabilidade e Persistência

```
fabrick/
├── observability/
│   ├── __init__.py
│   ├── structlog_config.py  # setup do structlog (dev/prod)
│   ├── langsmith.py         # tracing via LangSmith
│   └── metrics.py           # tokens, custo, timing por step
├── persistence/
│   ├── __init__.py
│   ├── base.py              # interface de checkpoint
│   ├── sqlite.py            # SQLite (dev)
│   ├── postgres.py          # PostgreSQL (prod)
│   └── redis.py             # Redis (cache/locks)
```

### Fase 6: Scheduling e Escala

```
fabrick/
├── scheduling/
│   ├── __init__.py
│   ├── base.py              # SchedulerAdapter (interface)
│   ├── apscheduler.py       # APScheduler (local)
│   └── cloud.py             # Google Cloud Scheduler
├── execution/
│   ├── __init__.py
│   ├── local.py             # execução síncrona/async local
│   ├── background.py        # threading/asyncio
│   ├── rq_worker.py         # Redis Queue
│   └── celery_worker.py     # Celery
```

---

## 8. Dependência entre Decorators e Tear

| Decorator Fabrick | Módulo Tear | Função Principal | Async |
|---|---|---|---|
| `@spec` | `spec/pipeline.py` | `SpecOrchestrator.run()` | Sim |
| `@plan` | `agents/planner.py` | `run_followup_planner()` | Sim |
| `@execute` | `agents/coder.py` | `run_autonomous_agent()` | Sim |
| `@review` | `qa/loop.py` | `run_qa_validation_loop()` | Sim |
| `@security` | `security/` + `analysis/` | `bash_security_hook()` + scanners | Não |

---

## 9. Configuração via `.env`

```bash
# Provider (escolha um)
AUTO_BUILD_PROVIDER=OLLAMA        # CLAUDE | OPENROUTER | GEMINI | OLLAMA

# Ollama
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=qwen3:8b

# Observabilidade
LANGSMITH_API_KEY=ls_xxx
LANGSMITH_PROJECT=fabrick-pipeline

# Persistência
FABRICK_PERSISTENCE=sqlite        # sqlite | postgres | redis
FABRICK_DB_URL=sqlite:///fabrick.db

# Scheduling
FABRICK_SCHEDULER=apscheduler     # apscheduler | cloud | none
```

---

## 10. Benchmark com Aider

Para validação, cada pipeline Fabrick pode ser comparado com o Aider rodando a mesma task:

```python
@execute(
    engine="aider",               # usa Aider como engine alternativa
    model="ollama/qwen3:8b",
    transitions_to=["review"],
)
async def build_with_aider(context):
    """Executa via: aider --model ollama/MODEL --message TASK"""
    ...
```

Métricas de comparação:
- **Tokens consumidos** por task
- **Tempo de execução** (wall clock)
- **Taxa de sucesso** no QA review
- **Commits gerados** vs. edits necessários
- **Score no Terminal-Bench** / SWE-bench

---

## 11. Estrutura Final do Pacote

```
fabrick/
├── __init__.py
├── core.py
├── decorators.py
├── context.py
├── machine.py
├── contracts.py
├── exceptions.py
├── constants.py
├── agents/
│   ├── __init__.py
│   ├── base.py
│   ├── spec.py
│   ├── plan.py
│   ├── execute.py
│   ├── review.py
│   └── security.py
├── bridge/
│   ├── __init__.py
│   ├── tear.py
│   ├── spec_adapter.py
│   ├── planner_adapter.py
│   ├── coder_adapter.py
│   ├── qa_adapter.py
│   └── security_adapter.py
├── providers/
│   ├── __init__.py
│   ├── base.py
│   ├── claude.py
│   ├── openrouter.py
│   ├── gemini.py
│   └── ollama.py
├── observability/
│   ├── __init__.py
│   ├── structlog_config.py
│   ├── langsmith.py
│   └── metrics.py
├── persistence/
│   ├── __init__.py
│   ├── base.py
│   ├── sqlite.py
│   ├── postgres.py
│   └── redis.py
├── scheduling/
│   ├── __init__.py
│   ├── base.py
│   ├── apscheduler.py
│   └── cloud.py
└── execution/
    ├── __init__.py
    ├── local.py
    ├── background.py
    ├── rq_worker.py
    └── celery_worker.py
```
