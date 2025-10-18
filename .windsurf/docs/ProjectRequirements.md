
## MCP integration (scaffold)
- Enable via `.env` keys:
  - `MCP_ENABLED=true|false`
  - `MCP_CONFIG_PATH=backend/agent_service/mcp/servers.yaml`
  - `MCP_AUTO_CONNECT=true|false`
- When enabled, the factory (`agents/factory.build_agent`) will:
  - Load the MCP manager from the YAML path (with `${ENV}` substitution)
  - Optionally connect
  - Collect tools via `tools.registry.collect_tools_from_mcp()`
  - Attach them to the agent via `tools.registry.attach_tools_to_agent()` (non-breaking; stored in `agent._mcp_tools` for now)
- Demo tool: `MCPManager.list_tools()` returns an `echo` tool until real discovery is added.
# Project Requirements
## Prompty templates
- Store `.prompty` files in `backend/agent_service/prompts/`.
- Format: YAML front matter (config) + Markdown body (instructions). `${ENV_VAR}` in front matter is substituted from the environment.
- Default template can be selected via `.env` key `AGENT_PROMPTY`.
- API supports `template` and `variables` fields in `ChatRequest`.

### Merge precedence
1. Request fields (e.g., `provider`, `instructions`)
2. Prompty front matter/body
3. `.env` via `Settings`
4. Settings defaults

## Overview
- **Framework**: Microsoft Agent Framework (Python) for agents and workflows.
- **Service**: `backend/agent_service/` FastAPI service that exposes non-streaming and SSE streaming chat endpoints.
- **Goal**: Hybrid approach (Option C). Ship a single agent now; add workflow orchestration next.

## Tech Stack
- **Language**: Python 3.10+
- **AI**: `agent-framework` (Public Preview)
- **Auth (optional)**: `azure-identity` for Azure OpenAI
- **Config**: `pydantic` + `python-dotenv` (`load_dotenv()`)
- **Testing**: `pytest`, `pytest-asyncio`, `httpx`
- **Formatting**: `black` (PEP8)
- **Dev UI**: Chainlit
- **Templates**: Prompty (local `.prompty` files parsed via PyYAML)
 - **MCP (optional)**: Config-driven MCP manager + tool registry scaffold

## Directory Structure (service)
- `backend/agent_service/app/`
  - `main.py`: FastAPI app; endpoints `/v1/chat`, `/v1/chat/stream`, `/healthz`
  - `models.py`: Pydantic request/response models
  - `factory.py`: Agent factory supporting `openai`, `azure`, `mock`
- `backend/agent_service/config/`
  - `settings.py`: Pydantic `BaseSettings`; case-insensitive env vars; `load_dotenv()`
- `backend/agent_service/tests/`: Pytest suite (health, chat, streaming)
- `backend/agent_service/requirements.txt`: Dependencies
- `backend/agent_service/.env.example`: Example env
- `backend/agent_service/README.md`: Service usage
 - `backend/agent_service/chainlit_app.py`: Chainlit chatbot UI for fast validation
 - `backend/agent_service/prompts/loader.py`: Prompty loader (front matter YAML + Markdown body)
 - `backend/agent_service/prompts/jarvis.prompty`: Sample prompty template
 - `backend/agent_service/mcp/schemas.py`: MCP config models
 - `backend/agent_service/mcp/manager.py`: MCP manager (YAML loader, lifecycle, demo tool)
 - `backend/agent_service/mcp/servers.yaml`: Example servers config
 - `backend/agent_service/tools/registry.py`: AgentTool abstraction and MCP tool mapping

## Coding Conventions
- **PEP8**; format with `black`.
- **Type hints** everywhere; keep files < 500 LOC; refactor when approaching limit.
- **Docstrings** (Google style) for all functions and classes.
- **Separation of concerns**: keep API, agents, tools, workflows, config modular.
- **Imports at top** of file; prefer relative imports within a package.

## Environment & Secrets
- Use `.env` loaded via `python-dotenv`. Example keys:
  - Provider: `PROVIDER=mock|openai|azure`
  - OpenAI: `OPENAI_API_KEY`, `OPENAI_MODEL` (e.g., `gpt-4o-mini`)
  - Azure OpenAI: `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_DEPLOYMENT_NAME`, `AZURE_OPENAI_API_VERSION`, `AZURE_OPENAI_API_KEY` or `AZURE_OPENAI_USE_CLI_CREDENTIAL=true` (requires `az login`)
- Do not commit secrets; use local `.env`. CI/CD should use secret stores.

## Virtual Environment
- Always use `venv_linux` for Python commands.
  ```bash
  python3 -m venv venv_linux
  source venv_linux/bin/activate
  pip install --upgrade pip
  pip install --pre -r backend/agent_service/requirements.txt
  ```

## Testing
- Tests live in `backend/agent_service/tests/` mirroring app structure.
- Minimum per feature: one happy path, one edge case, one failure case.
- Run with:
  ```bash
  source backend/agent_service/venv_linux/bin/activate
  pytest -q backend/agent_service
  ```

## Endpoints
- `POST /v1/chat`: non-streaming chat returning `{ "text": "..." }`.
- `POST /v1/chat/stream`: SSE streaming events `data: {"text":"..."}`.
- `GET /healthz`: health check.

## Providers
- **mock**: local echo for fast dev and tests.
- **openai**: `OpenAIResponsesClient` via API key.
- **azure**: `AzureOpenAIResponsesClient` via Azure CLI credential or API key. This covers Azure AI Foundry / Azure OpenAI.

### Provider aliases
- Aliases are normalized to canonical ids via `agents/factory.normalize_provider()`
  - `azure_foundry`, `azure-openai`, `azure-ai`, `azureai` -> `azure`
  - `oai` -> `openai`

## Next Steps (Workflows)
- Introduce `workflows/` with executors and edges for sequential/conditional/parallel orchestration.
- Enable checkpointing and request/response for human-in-the-loop.

## Mobile Integration Guidance
- Default streaming: **SSE** for simplicity and wide client support.
- If bi-directional or robust reconnection is needed, add **WebSocket** endpoint.

## Observability (Planned)
- Middleware-based logging/metrics/filters; OpenTelemetry as needed.
