# Implementation Plan - Gemini and OpenRouter API Integration

## 1. 🔍 Analysis & Context
*   **Objective:** Refactor Auto-Claude to support Gemini and OpenRouter APIs as alternative backends to Anthropic Claude, using a new `--setup` CLI flag and a centralized provider configuration registry.
*   **Affected Files:**
    *   `apps/backend/core/provider_config.py`: **(NEW)** Central registry for URLs, models, and environment variable mappings.
    *   `apps/backend/cli/main.py`: Add `--setup` argument and command handler.
    *   `apps/backend/core/auth.py`: Update authentication logic to support multiple providers using the registry.
    *   `apps/backend/core/client.py`: Configure the SDK client using registry data.
    *   `apps/backend/cli/setup_commands.py`: **(NEW)** Handle interactive configuration for different providers.
*   **Key Dependencies:**
    *   `python-dotenv`: For managing `.env` updates.
    *   `claude-agent-sdk`: Used with custom base URLs for agentic capabilities.
    *   `openrouter`: (Optional) For direct non-agentic chat calls if needed.
*   **Risks/Unknowns:**
    *   **Tool Calling Compatibility:** Ensuring that `claude-agent-sdk` correctly translates tools when pointing to OpenRouter's OpenAI-compatible endpoint.
    *   **Rate Limits:** Handling provider-specific errors.

- [x] Step 1: Create Central Provider Registry
- [x] Step 2: Add `--setup` flag to CLI
- [x] Step 3: Implement Interactive Setup Handler
- [x] Step 4: Update Provider-Aware Authentication
- [x] Step 5: Update SDK Client Initialization
- [ ] Verification

## 3. 📝 Step-by-Step Implementation Details

### Step 1: Create Central Provider Registry
*   **Goal:** Centralize all provider-specific metadata (URLs, default models, env var names).
*   **Action:**
    *   Create `apps/backend/core/provider_config.py`.
*   **Verification:** ✅ Implemented in `apps/backend/core/provider_config.py`. Tested with import.

### Step 2: Add `--setup` flag to CLI
*   **Goal:** Enable the setup flow via CLI.
*   **Action:**
    *   Modify `apps/backend/cli/main.py`.
*   **Verification:** ✅ Implemented in `apps/backend/cli/main.py`.

### Step 3: Implement Interactive Setup Handler
*   **Goal:** Prompt user for keys and update `.env`.
*   **Action:**
    *   Create `apps/backend/cli/setup_commands.py`.
*   **Verification:** ✅ Implemented in `apps/backend/cli/setup_commands.py`. Added `.env` writer helper.

### Step 4: Update Provider-Aware Authentication
*   **Goal:** Map active provider keys to what the SDK expects.
*   **Action:**
    *   Modify `apps/backend/core/auth.py`.
*   **Verification:** ✅ Implemented in `apps/backend/core/auth.py`. Added provider mapping logic to `configure_sdk_authentication`.

### Step 5: Update SDK Client Initialization
*   **Goal:** Inject registry data into the `ClaudeSDKClient`.
*   **Action:**
    *   Modify `apps/backend/core/client.py`.
*   **Verification:** ✅ Implemented in `apps/backend/core/client.py`. Added provider logging.

## 4. 🧪 Testing Strategy
*   **Unit Tests:** Registry resolution, `.env` file management.
*   **Integration Tests:** Mock SDK calls verifying base URL and token injection.
*   **Manual Verification:** Switch between providers and run a simple spec.

## 5. ✅ Success Criteria
*   Users can configure Gemini/OpenRouter via CLI.
*   The system uses the centralized registry for all provider metadata.
*   Autonomous agent features (tools) remain functional across providers.
*   Existing Claude Code workflow is preserved as the default.
