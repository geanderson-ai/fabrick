# Fabrick — Orquestrador Declarativo de Pipelines de IA em Python

## Visão Geral

**Fabrick** é um orquestrador leve, extensível e cloud-agnostic para pipelines de Inteligência Artificial, escrito em **Python puro** e orientado a **code-as-configuration**.  
O objetivo é permitir que desenvolvedores definam fluxos complexos de IA — ingestão de dados, execução de chains e agents, decisões condicionais, retries e finalização — usando **funções Python normais**, decoradas de forma declarativa, sem boilerplate excessivo.

O controle do fluxo é feito por **máquinas de estado explícitas**, o agendamento é desacoplado via adapters, e a observabilidade é tratada como requisito de primeira classe.

---

## Problema que o projeto resolve

- Orquestradores existentes são **pesados**, **opinionados** ou **config-driven demais**
- Dificuldade de integrar **IA (LLMs, agents, chains)** com pipelines tradicionais
- Falta de **controle fino em código** sobre estado, retry e decisões
- Baixa transparência e rastreabilidade em pipelines de IA em produção

O Fabrick resolve isso mantendo tudo **explícito, testável e versionável em Python**.

---

## Princípios de Design

- **Code-as-Configuration**: o fluxo emerge do código e decorators, não de YAML
- **State machine first**: todo pipeline tem ciclo de vida explícito
- **Adapters, não acoplamento**: scheduler, cloud, DB e filas são plugáveis
- **JSON como contrato**: cada step retorna um payload padronizado
- **Cloud-agnostic por padrão**: integra com cloud sem lock-in
- **Observabilidade nativa**: tracing não é opcional

---

## Como funciona (alto nível)

1. O desenvolvedor escreve funções Python comuns
2. Usa decorators (`@start`, `@step`, `@finish`)
3. Cada função retorna um JSON com `status`, `data`, `next_state`, `metadata`
4. O `Fabrick` executa o pipeline guiado por uma máquina de estados
5. Um scheduler (local ou cloud) dispara a execução
6. Estado e checkpoints são persistidos para retry e recuperação
7. Toda execução é rastreada via LangSmith

---

## Bibliotecas Utilizadas

### Core e Contratos
- **pydantic** — validação e contratos de entrada/saída
- **typing-extensions** — typing avançado

### Orquestração e Estado
- **transitions** — máquinas de estado explícitas
- **APScheduler** — agendamento local (cron, interval, date)

### Inteligência Artificial
- **langchain** — chains, tools e abstrações de LLM
- **langgraph** — fluxos e grafos de execução de agents
- **langsmith** — observabilidade, tracing, replay e métricas

### Persistência e Retry
- **sqlalchemy** — camada agnóstica de banco
- **psycopg2-binary** — PostgreSQL (produção)
- **redis** — cache, locks e retry rápido
- **tenacity** — backoff e políticas de retry

### Escala e Execução
- **rq** — filas simples
- **celery** — execução distribuída em larga escala
- **kombu** — messaging layer

### Observabilidade e DX
- **structlog** — logs estruturados
- **rich** — logs legíveis em desenvolvimento

### Cloud (opcional)
- **google-cloud-scheduler** — triggers externos
- **google-cloud-functions** — eventos serverless
- **google-cloud-run** — execução stateless escalável
- **google-genai** — integração com modelos de IA

---

## Entregas do Projeto

### 1. Core do Orquestrador
- Classe `Fabrick`
- Registro automático de steps via decorators
- Execução baseada em state machine
- Contrato JSON padronizado

### 2. Decorators Declarativos
- `@start`, `@step`, `@finish`
- Registro de metadados sem lógica acoplada
- Fluxo controlado por `next_state`

### 3. Adapter de Scheduler
- Adapter base
- Implementação com APScheduler
- Suporte a cron, interval e date
- Substituível por Cloud Scheduler

### 4. Camada de Persistência
- Checkpoints de execução
- Armazenamento de input/output
- Registro de erros
- Base para retry confiável e replay

### 5. Observabilidade
- Integração nativa com LangSmith
- Tracing de chains e agents
- Métricas e debugging de execução

### 6. Escalabilidade
- Execução local, background ou via filas
- Integração com RQ e Celery
- Pronto para Docker e Kubernetes

---

## O que o Fabrick **não** é

- Não é um replacement de Airflow
- Não é low-code
- Não esconde complexidade
- Não toma decisões mágicas pelo desenvolvedor

---

## Público-alvo

- Engenheiros de IA
- Desenvolvedores Python sênior
- Times que precisam colocar **pipelines de IA em produção com controle**
- Empresas que querem IA observável, auditável e escalável

---

## Resultado Final

Um orquestrador **simples de começar**, **difícil de quebrar** e **honesto sobre o que está acontecendo**, feito para pipelines de IA reais — não demos.

