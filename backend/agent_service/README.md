# Agent Service (Microsoft Agent Framework)

This service exposes a baseline AI agent using Microsoft Agent Framework (Python), with both non-streaming and streaming (SSE) chat endpoints.

## Endpoints
- **POST `/v1/chat`**: Non-streaming; returns `{ "text": "..." }`.
- **POST `/v1/chat/stream`**: Streaming via SSE; emits `data: {"text":"..."}` events.
- **GET `/healthz`**: Liveness probe.

## Quick start

1) Create virtual environment (venv_linux) and install
```bash
python3 -m venv venv_linux
source venv_linux/bin/activate
pip install --upgrade pip
pip install --pre -r requirements.txt
```

2) Configure environment
- Copy `.env.example` to `.env` and adjust. Common settings:
  - `PROVIDER=mock | openai | azure` (aliases: `azure_foundry`, `azure-openai`, `azure-ai` map to `azure`)
  - OpenAI: `OPENAI_API_KEY`, `OPENAI_MODEL` (e.g., `gpt-4o-mini`)
  - Azure (Azure AI Foundry / Azure OpenAI): `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_DEPLOYMENT_NAME`, `AZURE_OPENAI_API_VERSION`, and either `AZURE_OPENAI_API_KEY` or authenticate with `az login` and keep `AZURE_OPENAI_USE_CLI_CREDENTIAL=true`.

3) Run the service
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

4) Test
```bash
pytest -q
```

## Notes
- Streaming uses SSE for compatibility with many clients. If you prefer WebSocket streaming, we can add it.
- Providers are pluggable via `agents/factory.py`. Default is `mock` for local/dev. Provider aliases are normalized via `normalize_provider()` and dispatched through a registry.
- Settings are in `config/settings.py` (pydantic + dotenv; case-insensitive env vars).

## Chainlit (Dev UI)
Run a local chatbot UI powered by the same agent:

```bash
source venv_linux/bin/activate
chainlit run backend/agent_service/chainlit_app.py -w --host 0.0.0.0 --port 8000
```

Notes:
- Chainlit loads `.env` via the same `Settings`; run the command from repo root or `backend/agent_service/` so `.env` is picked up.
- If using Azure, ensure your `.env` has the correct endpoint, deployment, and API version.

## Prompty templates (local)
- Store `.prompty` files in `backend/agent_service/prompts/`. Example: `jarvis.prompty`.
- Format: YAML front matter (config) + Markdown body (instructions). `${ENV_VAR}` in front matter will be substituted from the environment.
- Default template for Chainlit/app can be set via `.env`:
  - `AGENT_PROMPTY=jarvis`

API usage:
```bash
curl -s http://localhost:8080/v1/chat \
  -H 'Content-Type: application/json' \
  -d '{
    "message": "Hello",
    "template": "jarvis"
  }'
```

Precedence (most specific wins):
1. Request fields (e.g., `provider`, `instructions`)
2. Prompty front matter/body
3. `.env` via `Settings`
4. Settings defaults

## MCP integration (scaffold)
- Location: `backend/agent_service/mcp/` and `backend/agent_service/tools/`
  - `mcp/schemas.py`: Pydantic config models
  - `mcp/manager.py`: Loads YAML, manages lifecycle, returns tool specs
  - `mcp/servers.yaml`: Example config (stdio + sse entries)
  - `tools/registry.py`: `AgentTool` abstraction, MCP -> tool mapping, and `attach_tools_to_agent()` hook

Enable via `.env` (or pass flags to `build_agent()`):
```env
MCP_ENABLED=true
MCP_CONFIG_PATH=backend/agent_service/mcp/servers.yaml
MCP_AUTO_CONNECT=true
```

Behavior today:
- When enabled, tools discovered by the MCP manager are attached in-memory to the agent under `agent._mcp_tools`.
- A demo `echo` tool is emitted by `MCPManager.list_tools()` until real MCP client discovery is wired.

Notes:
- This is a non-breaking scaffold. You can safely enable it; if config load fails, the agent continues without MCP tools.
