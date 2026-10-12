# AGENTS.md

## Cursor Cloud specific instructions

This is a monorepo of 10 independent lab projects for the cloud.ru AI Agents platform. Each lab is self-contained with its own virtual environment and dependencies.

### Architecture overview

| Lab | Language | Package Manager | Run Command |
|-----|----------|----------------|-------------|
| lab1-mcp-finance-lab | Python 3.12 | uv | `uv run python src/server.py` (from lab1 root) |
| lab2-adk-agent | Python 3.12 | uv | `uv run python src/start_a2a.py` (requires LLM_API_KEY) |
| lab3-langchain-agent | Python 3.12 | uv | `uv run python src/start_a2a.py` (requires LLM_API_KEY) |
| lab4-smolagents-agent | Python 3.12 | uv | `uv run python src/start_a2a.py` (requires LLM_API_KEY) |
| lab5-crewai-agent | Python 3.12 | uv | `uv run python src/start_a2a.py` (requires LLM_API_KEY) |
| lab6-strands-agent | Python 3.12 | uv | `uv run python src/start_a2a.py` (requires LLM_API_KEY) |
| lab7-mattermost-bot-for-agents | Python 3.10+ | uv | `uv run python bot.py` (requires MATTERMOST_URL, MATTERMOST_TOKEN) |
| lab8-telegram-bot-for-agents | Python 3.12 | uv | `uv run python main.py` (requires TELEGRAM_BOT_TOKEN) |
| lab9-mcp-finance-go | Go 1.21 | go modules | No `cmd/server/main.go` entry point committed yet |
| lab10-a2a-a2ui-renderer | TypeScript/React | npm | `npm start` (Node 18 required) |

### Key caveats

- **Node version**: lab10 requires Node 18 (`source ~/.nvm/nvm.sh && nvm use 18`).
- **npm install flag**: lab10 requires `npm install --legacy-peer-deps`.
- **LLM_MODEL format**: When using `ChatOpenAI` directly (labs 2-3), use `Qwen/Qwen3-Coder-480B-A35B-Instruct` (no `hosted_vllm/` prefix). When using `litellm` (labs 4-6), use `hosted_vllm/Qwen/Qwen3-Coder-480B-A35B-Instruct`.
- **Agent env vars**: `LLM_API_KEY`, `LLM_API_BASE=https://foundation-models.api.cloud.ru/v1`, `LLM_MODEL`, `MCP_URL`, `PORT`, `URL_AGENT`.
- **lab9 Go**: The `cmd/server/main.go` entry point does not exist in the repo.

### Running the full stack locally

1. Start lab1 MCP server: `cd lab1-mcp-finance-lab && uv run python src/server.py` (port 8000)
2. Start an agent (e.g. lab3): `cd lab3-langchain-agent && MCP_URL=http://localhost:8000/mcp PORT=10003 uv run python src/start_a2a.py`
3. Start lab10 frontend: `cd lab10-a2a-a2ui-renderer && npm start` (port 3000, point Server URL to agent)

### Testing

- **lab1**: `PYTHONPATH=src uv run pytest test/` — 18/18 pass
- **lab9**: `go test ./...` — all pass
- **lab10**: `npx react-scripts build` — succeeds
