"""@architecture — Architecture documentation generator decorator.

Generates comprehensive project architecture documentation organized in 22 sections.
Each section can be enabled/disabled and customized via options.

Generates:
  prd.md, architecture_overview.md, system_design.md, data_flow.md,
  integration_spec.md, templates/, infrastructure.md, raci_matrix.md,
  glossary_taxonomy.md, tech_stack.md, api_contracts.md, security_model.md,
  data_model.md, error_handling.md, scalability_plan.md, observability.md,
  deployment_strategy.md, testing_strategy.md, risk_assessment.md,
  adrs/, sla_slo.md, dependencies_map.md
"""

from __future__ import annotations

from typing import Any

from .base import agent_decorator


# ── Section Registry ──

SECTION_PRD = "prd"
SECTION_OVERVIEW = "overview"
SECTION_DESIGN = "design"
SECTION_DATA_FLOW = "data_flow"
SECTION_INTEGRATION = "integration"
SECTION_TEMPLATES = "templates"
SECTION_INFRASTRUCTURE = "infrastructure"
SECTION_RACI = "raci"
SECTION_GLOSSARY = "glossary"
SECTION_TECH_STACK = "tech_stack"
SECTION_API_CONTRACTS = "api_contracts"
SECTION_SECURITY_MODEL = "security_model"
SECTION_DATA_MODEL = "data_model"
SECTION_ERROR_HANDLING = "error_handling"
SECTION_SCALABILITY = "scalability"
SECTION_OBSERVABILITY = "observability"
SECTION_DEPLOYMENT = "deployment"
SECTION_TESTING = "testing"
SECTION_RISK = "risk"
SECTION_ADR = "adr"
SECTION_SLA = "sla"
SECTION_DEPENDENCIES = "dependencies"

ALL_SECTIONS: list[str] = [
    SECTION_PRD,
    SECTION_OVERVIEW,
    SECTION_DESIGN,
    SECTION_DATA_FLOW,
    SECTION_INTEGRATION,
    SECTION_TEMPLATES,
    SECTION_INFRASTRUCTURE,
    SECTION_RACI,
    SECTION_GLOSSARY,
    SECTION_TECH_STACK,
    SECTION_API_CONTRACTS,
    SECTION_SECURITY_MODEL,
    SECTION_DATA_MODEL,
    SECTION_ERROR_HANDLING,
    SECTION_SCALABILITY,
    SECTION_OBSERVABILITY,
    SECTION_DEPLOYMENT,
    SECTION_TESTING,
    SECTION_RISK,
    SECTION_ADR,
    SECTION_SLA,
    SECTION_DEPENDENCIES,
]

SECTION_META: dict[str, dict[str, Any]] = {
    SECTION_PRD: {
        "title": "Product Requirements Document",
        "output": "prd.md",
        "description": "Business goals, user stories, acceptance criteria, scope, and constraints.",
        "prompt_hint": (
            "Generate a PRD covering: executive summary, problem statement, "
            "goals & objectives, user personas, user stories with acceptance criteria, "
            "functional requirements, non-functional requirements, scope (in/out), "
            "success metrics, and constraints."
        ),
    },
    SECTION_OVERVIEW: {
        "title": "Architecture Overview",
        "output": "architecture_overview.md",
        "description": "High-level system architecture, components, boundaries, and communication patterns.",
        "prompt_hint": (
            "Generate an architecture overview covering: system context diagram (C4 Level 1), "
            "container diagram (C4 Level 2), component boundaries, communication patterns "
            "(sync/async), key architectural decisions, and technology radar."
        ),
    },
    SECTION_DESIGN: {
        "title": "System Design",
        "output": "system_design.md",
        "description": "Detailed system design with modules, patterns, and internal structure.",
        "prompt_hint": (
            "Generate a system design covering: module decomposition, design patterns used, "
            "class/component diagrams, sequence diagrams for critical flows, "
            "state management strategy, and concurrency model."
        ),
    },
    SECTION_DATA_FLOW: {
        "title": "Data Flow",
        "output": "data_flow.md",
        "description": "How data moves through the system — ingestion, transformation, storage, and output.",
        "prompt_hint": (
            "Generate data flow documentation covering: data flow diagrams (DFD Level 0-2), "
            "data transformation pipeline, data validation points, "
            "event/message flows, data lineage, and data retention policies."
        ),
    },
    SECTION_INTEGRATION: {
        "title": "Integration Spec",
        "output": "integration_spec.md",
        "description": "External integrations, third-party APIs, webhooks, and protocols.",
        "prompt_hint": (
            "Generate an integration spec covering: external service catalog, "
            "integration patterns (REST, gRPC, webhooks, queues), authentication flows, "
            "rate limits, retry policies, circuit breaker config, "
            "data format mappings, and SLA expectations per integration."
        ),
    },
    SECTION_TEMPLATES: {
        "title": "Templates",
        "output": "templates/",
        "description": "Reusable templates for PRs, issues, RFCs, ADRs, and runbooks.",
        "prompt_hint": (
            "Generate project templates: PR template, issue templates (bug/feature/task), "
            "RFC template, ADR template, incident runbook template, "
            "release checklist, and onboarding checklist."
        ),
    },
    SECTION_INFRASTRUCTURE: {
        "title": "Infrastructure",
        "output": "infrastructure.md",
        "description": "Cloud resources, IaC, networking, compute, and storage architecture.",
        "prompt_hint": (
            "Generate infrastructure documentation covering: cloud provider and regions, "
            "compute resources (containers, serverless, VMs), networking (VPC, subnets, LB), "
            "storage (databases, object storage, caches), IaC tool and structure, "
            "environment topology (dev/staging/prod), and cost estimation."
        ),
    },
    SECTION_RACI: {
        "title": "RACI Matrix",
        "output": "raci_matrix.md",
        "description": "Responsibility assignment — who is Responsible, Accountable, Consulted, Informed.",
        "prompt_hint": (
            "Generate a RACI matrix covering: key deliverables and decisions, "
            "team roles, responsibility assignments (R/A/C/I) per deliverable, "
            "escalation paths, and decision-making authority levels."
        ),
    },
    SECTION_GLOSSARY: {
        "title": "Glossary & Taxonomy",
        "output": "glossary_taxonomy.md",
        "description": "Domain terms, abbreviations, ubiquitous language, and entity taxonomy.",
        "prompt_hint": (
            "Generate a glossary covering: domain-specific terms with definitions, "
            "abbreviations and acronyms, ubiquitous language (DDD), "
            "entity taxonomy and relationships, and naming conventions used in code."
        ),
    },
    SECTION_TECH_STACK: {
        "title": "Tech Stack",
        "output": "tech_stack.md",
        "description": "Technology choices, versions, justifications, and alternatives considered.",
        "prompt_hint": (
            "Generate tech stack documentation covering: languages and runtimes, "
            "frameworks and libraries (with versions), databases and data stores, "
            "infrastructure tools, dev tools and DX, "
            "justification for each choice, and alternatives considered with trade-offs."
        ),
    },
    SECTION_API_CONTRACTS: {
        "title": "API Contracts",
        "output": "api_contracts.md",
        "description": "API endpoints, request/response schemas, versioning, and pagination.",
        "prompt_hint": (
            "Generate API contract documentation covering: REST/gRPC/GraphQL endpoints, "
            "request/response schemas (with examples), authentication headers, "
            "error response format, pagination strategy, "
            "versioning strategy, rate limiting, and OpenAPI/protobuf references."
        ),
    },
    SECTION_SECURITY_MODEL: {
        "title": "Security Model",
        "output": "security_model.md",
        "description": "Authentication, authorization, encryption, compliance, and threat model.",
        "prompt_hint": (
            "Generate security model documentation covering: authentication mechanism "
            "(OAuth2, JWT, API keys), authorization model (RBAC/ABAC), "
            "data encryption (at rest, in transit), secrets management, "
            "OWASP top 10 mitigations, threat model (STRIDE), "
            "compliance requirements (GDPR, SOC2, HIPAA), and audit logging."
        ),
    },
    SECTION_DATA_MODEL: {
        "title": "Data Model",
        "output": "data_model.md",
        "description": "Entity-relationship diagrams, schemas, migrations, and indexing strategy.",
        "prompt_hint": (
            "Generate data model documentation covering: ER diagram, "
            "table/collection schemas with types, relationships and cardinality, "
            "indexing strategy, migration strategy, "
            "seed data, and data partitioning/sharding approach."
        ),
    },
    SECTION_ERROR_HANDLING: {
        "title": "Error Handling",
        "output": "error_handling.md",
        "description": "Error strategy, error codes, fallbacks, circuit breakers, and retry policies.",
        "prompt_hint": (
            "Generate error handling documentation covering: error classification taxonomy, "
            "error code registry, retry policies (per service/operation), "
            "circuit breaker configuration, fallback strategies, "
            "dead letter queues, graceful degradation patterns, "
            "and user-facing error messages mapping."
        ),
    },
    SECTION_SCALABILITY: {
        "title": "Scalability Plan",
        "output": "scalability_plan.md",
        "description": "Scaling strategy, bottlenecks, caching, and capacity planning.",
        "prompt_hint": (
            "Generate scalability plan covering: current capacity baseline, "
            "horizontal vs vertical scaling strategy, auto-scaling rules, "
            "identified bottlenecks and mitigations, caching strategy (layers, TTL, invalidation), "
            "database read replicas / sharding, CDN strategy, "
            "load testing plan, and capacity projections (6/12/24 months)."
        ),
    },
    SECTION_OBSERVABILITY: {
        "title": "Monitoring & Observability",
        "output": "observability.md",
        "description": "Logging, metrics, tracing, alerts, and dashboards.",
        "prompt_hint": (
            "Generate observability documentation covering: logging strategy (structured, levels, retention), "
            "metrics catalog (business + infrastructure), distributed tracing setup, "
            "alerting rules and escalation, dashboard inventory, "
            "health check endpoints, SLI definitions, and on-call runbook references."
        ),
    },
    SECTION_DEPLOYMENT: {
        "title": "Deployment Strategy",
        "output": "deployment_strategy.md",
        "description": "CI/CD pipeline, deployment patterns, rollback, and environment promotion.",
        "prompt_hint": (
            "Generate deployment strategy covering: CI/CD pipeline stages, "
            "deployment pattern (blue-green, canary, rolling), "
            "environment promotion flow (dev -> staging -> prod), "
            "rollback procedure, feature flags strategy, "
            "database migration during deploy, smoke tests, and release cadence."
        ),
    },
    SECTION_TESTING: {
        "title": "Testing Strategy",
        "output": "testing_strategy.md",
        "description": "Test pyramid, coverage targets, test types, and QA process.",
        "prompt_hint": (
            "Generate testing strategy covering: test pyramid (unit/integration/e2e ratios), "
            "coverage targets per layer, testing frameworks and tools, "
            "test data management, mocking strategy, "
            "performance/load testing plan, security testing (SAST/DAST), "
            "accessibility testing, and QA sign-off process."
        ),
    },
    SECTION_RISK: {
        "title": "Risk Assessment",
        "output": "risk_assessment.md",
        "description": "Technical risks, impact analysis, mitigations, and contingency plans.",
        "prompt_hint": (
            "Generate risk assessment covering: risk registry (ID, description, probability, impact), "
            "risk matrix (probability x impact), mitigation strategies per risk, "
            "contingency plans, risk owners, "
            "technical debt inventory, and review cadence."
        ),
    },
    SECTION_ADR: {
        "title": "Architecture Decision Records",
        "output": "adrs/",
        "description": "Key architecture decisions with context, options, trade-offs, and rationale.",
        "prompt_hint": (
            "Generate ADR documents covering key decisions. Each ADR should include: "
            "title, status (proposed/accepted/deprecated), context, "
            "decision drivers, considered options with pros/cons, "
            "decision outcome, consequences (positive/negative), and references."
        ),
    },
    SECTION_SLA: {
        "title": "SLA / SLO / SLI",
        "output": "sla_slo.md",
        "description": "Service level targets — availability, latency, throughput, and recovery.",
        "prompt_hint": (
            "Generate SLA/SLO documentation covering: SLI definitions (latency, error rate, throughput), "
            "SLO targets per service, SLA commitments, "
            "error budget policy, RTO and RPO targets, "
            "measurement methodology, and breach response procedure."
        ),
    },
    SECTION_DEPENDENCIES: {
        "title": "Dependencies Map",
        "output": "dependencies_map.md",
        "description": "External services, libraries, licenses, versions, and update policy.",
        "prompt_hint": (
            "Generate dependencies map covering: runtime dependency tree, "
            "external service dependencies (with SLA), "
            "library inventory (name, version, license, last audit), "
            "license compatibility matrix, update/patch policy, "
            "vendor lock-in assessment, and supply chain security measures."
        ),
    },
}


architecture = agent_decorator(
    agent_type="architecture",
    default_options={
        "sections": ALL_SECTIONS,       # which sections to generate
        "output_dir": "docs/architecture",  # base output directory
        "format": "markdown",           # markdown | json | both
        "depth": "detailed",            # overview | standard | detailed
        "diagrams": True,               # include mermaid/plantuml diagrams
        "interactive": False,           # ask clarifying questions per section
    },
)
