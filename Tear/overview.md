# Auto-Claude Overview: Entry Points & Execution Flow

### 1. Entry Points
*   **Desktop UI (Electron):** The main entry point for the desktop application is located in `apps/frontend`. 
    *   **Main Process:** `apps/frontend/src/main/index.ts`
    *   **Renderer Process (React):** `apps/frontend/src/renderer/main.tsx`
*   **CLI (Python Backend):** The direct entry point for the agent engine is `apps/backend/run.py`.
    *   **Command Orchestration:** `run.py` calls `apps/backend/cli/main.py`, which parses arguments (e.g., `--spec`, `--merge`, `--qa`) and dispatches them to specific command handlers.

### 2. Propagation Flow
*   **Initialization:** The `handle_build_command` (in `cli/build_commands.py`) validates the environment, checks permissions, and configures the workspace (isolated via Git worktrees or direct).
*   **Autonomous Agent Loop:** 
    *   The core execution happens in `apps/backend/agents/coder.py` via `run_autonomous_agent`.
    *   The agent loads the **Implementation Plan** (generated previously via the `/spec` command).
    *   It iterates through subtasks, triggering individual sessions managed by `apps/backend/agents/session.py`.
*   **Claude SDK Integration:** Each session uses the `ClaudeSDKClient` to communicate with the AI, sending focused prompts and executing system tools to read, write, and test code.
*   **Post-Processing & Memory:** After each session, `post_session_processing` runs to update project memory (via **Graphiti** or local files), perform automatic commits, and track progress in the plan.

### 3. Validation & Delivery
*   **QA Loop:** Once technical subtasks are finished, the flow enters `run_qa_validation_loop` (in `apps/backend/qa_loop.py`). A QA agent verifies acceptance criteria and attempts to fix issues autonomously.
*   **Workspace Finalization:** If using an isolated workspace, the system prompts for user confirmation to merge, review, or discard changes.
*   **External Integrations:** Status updates are propagated to external tools like **Linear** or notification systems throughout the process.

### 4. Running CLI Independently
You can run the engine directly from the command line without the Electron frontend:
*   **Command:** `python apps/backend/run.py --spec <spec-name>`
*   **Requirements:** Needs an existing spec (created via `claude /spec`) and active authentication (`CLAUDE_CODE_OAUTH_TOKEN` or `claude /login`).
*   **Capabilities:** All core operations (build, merge, review, QA, discard) are fully functional via CLI flags.

### 5. Dependency on Claude Code
Auto-Claude acts as an autopilot for the **Claude Code CLI**:
*   **Underlying Engine:** It uses Claude Code's tool-calling capabilities and environment.
*   **Mandatory Setup:** `claude` must be installed (`npm install -g @anthropic-ai/claude-code`) and authenticated (`claude /login`).
*   **Workflow:** Use `claude /spec` to generate the initial plan, then let Auto-Claude handle the autonomous implementation and QA cycles.

### 6. LLM Configuration
The framework is optimized for **Anthropic's Claude** family:
*   **Switching Models:** Use the `--model` flag (e.g., `sonnet`, `haiku`, `opus`) to choose the reasoning engine.
*   **Custom IDs:** Override default models via environment variables like `ANTHROPIC_DEFAULT_SONNET_MODEL`.
*   **Ollama Support:** Local models via Ollama are used for **Embeddings** and long-term memory retrieval, ensuring semantic search without external API calls.
*   **Constraint:** The main coding engine must remain Claude-based to maintain compatibility with the system tools and prompt architecture.

**Summary:** `UI/CLI` → `Workspace Orchestrator` → `Coding Agent Loop` → `QA Validator` → `Merge/Final Result`.
