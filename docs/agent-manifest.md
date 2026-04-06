flowchart LR

subgraph CP["Agent Control Plane"]
    A1["Agent Registry"]
    A2["Agent Manifest (YAML / JSON)"]
    A3["Versioning and Build System"]
    A4["Policy Engine (Security, Data, Tools)"]
    A5["Dependency Catalog (Models, Tools, Datasets)"]
    A6["Cost and Quota Manager"]
    A7["Audit and Lineage Store"]
    A8["Observability and Logs"]
    A9["Environment Manager (dev, staging, prod)"]
end

subgraph EP["Agent Runtime Engine"]
    B1["Manifest Interpreter"]
    B2["Schema Validator"]
    B3["Dependency Resolver"]
    B4["Agent Runtime Initializer"]
    B5["Tool Binding Engine"]
    B6["Execution Graph Builder"]
    B7["Agent Executor"]
    B8["Runtime Metrics Collector"]
end

A1 --> A2
A2 --> A3
A3 --> A4
A4 --> A5
A5 --> A6
A6 --> A9

A3 -->|"Build Request"| B1
B1 --> B2
B2 --> B3
B3 --> B4
B4 --> B5
B5 --> B6
B6 --> B7

B7 -->|"Execution Events"| B8
B8 -->|"Metrics and Errors"| A8
B8 -->|"Usage Data"| A6
B8 -->|"Lineage Events"| A7

A7 --> A1
A8 --> A3
A6 --> A3
