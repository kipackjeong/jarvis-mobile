# Work Tracker

##20251010
- [x] Set up Agent service using Microsoft Agent Framework (Phase 1–2)
  - [x] Create project skeleton (FastAPI app, settings, models)
  - [x] Implement agent factory (providers: mock, openai, azure)
  - [x] Add non-streaming and SSE streaming chat endpoints
  - [x] Add pytest tests (health, chat, streaming)
  - [x] Add docs (service README, ProjectRequirements)

- [x] Provider aliases and registry (Option B)
  - [x] Implement `normalize_provider()` and provider registry in `agents/factory.py`
  - [x] Update `.env.example`, `README.md`, and `ProjectRequirements.md`
  - [x] Add unit test `tests/test_provider_aliases.py`

- [x] Choose model provider and credentials
  - [x] Provider selected: Azure AI Foundry (alias 'azure')
  - [x] Configure .env with required keys and endpoints
  - [x] Validate live call (Chainlit) with Azure (Azure OpenAI endpoint)

- [x] Integrate Chainlit Dev UI for fast validation
  - [x] Add `chainlit` dependency and `chainlit_app.py`
  - [x] Document run instructions in service README
  - [x] Launch UI at http://localhost:8000 and validate conversation

- [x] Install stable Python and recreate venv
  - [x] Install `pyenv` and Python 3.12.7
  - [x] Set `pyenv local 3.12.7` for `backend/agent_service/`
  - [x] Recreate `venv_linux`, reinstall deps, and run Chainlit

- [x] Prompty templates (local) integration
  - [x] Add `prompts/loader.py` and `prompts/jarvis.prompty`
  - [x] Add `PyYAML` dependency
  - [x] Extend `ChatRequest` with `template` and `variables`
  - [x] Update `build_agent()` to load/merge prompty
  - [x] Pass prompty through FastAPI and Chainlit (`AGENT_PROMPTY` default)
  - [x] Add tests `tests/prompts/test_prompty_loader.py`

- [x] MCP integration scaffold
  - [x] Add MCP config models and manager (`mcp/schemas.py`, `mcp/manager.py`)
  - [x] Add sample config (`mcp/servers.yaml`) and tool registry (`tools/registry.py`)
  - [x] Wire optional MCP into `build_agent()` with safe fallback
  - [x] Add demo `echo` tool via `MCPManager.list_tools()` and expose in Chainlit
  - [x] Add docs (README, ProjectRequirements) for enabling MCP
  - [x] Add tests: `tests/mcp/test_mcp_manager.py`, `tests/tools/test_tools_registry.py`

- [ ] Define target use-cases and required tools/APIs
  - [ ] Prioritize first integrations (HTTP/domain APIs, MCP if needed)
  - [ ] Confirm mobile integration interface (SSE vs WebSocket)

- [ ] Plan workflows and checkpointing (Phase 4)
  - [ ] Design simple sequential workflow around the agent
  - [ ] Add request/response (HITL) and checkpointing if required
