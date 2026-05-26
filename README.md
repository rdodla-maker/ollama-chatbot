# Ollama Agentic AI Chatbot

Educational Agentic AI project with **FastAPI**, **React**, **Ollama**, **PDF RAG (ChromaDB)**, and a **LangGraph ReAct agent** with tools, memory, and codebase search.

## Features

- Local LLM via [Ollama](https://ollama.com)
- **React UI** — PDF chat (with streaming), autonomous agent, PDF upload
- PDF RAG with ChromaDB + recursive chunking
- **LangGraph ReAct agent** — LLM tool calling (calculator, PDF, files, codebase)
- **Memory retrieval** — recent + semantic recall from `agent_memory.json`
- **Codebase RAG** — index `backend/` + `frontend/src/` for semantic code search
- Legacy keyword agent fallback if LangGraph fails
- Terminal chat (`advanced_chat.py`) with streaming

## Project structure

```
ollama-chatbot/
├── backend/
│   ├── main.py
│   ├── agent/               # LangGraph + legacy fallback
│   ├── planner.py
│   ├── executor.py
│   ├── api/
│   ├── core/
│   ├── tools/
│   ├── rag/
│   ├── memory/
│   ├── services/            # async httpx Ollama
│   └── models/
├── frontend/src/            # React UI
├── tests/
├── advanced_chat.py
├── requirements.txt
└── .env.example
```

## Setup

### 1. Ollama

```bash
ollama pull llama3
ollama serve
```

### 2. Python backend

```bash
cd ollama-chatbot
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
copy .env.example .env       # edit paths if needed
cd backend
uvicorn main:app --reload
```

API docs: http://127.0.0.1:8000/docs

### 3. Frontend

```bash
cd frontend
copy .env.example .env
npm install
npm run dev
```

Open http://localhost:5173

### 4. Index codebase (for agent code search)

Use the **Index codebase** button in the Agent tab, or:

```bash
curl -X POST http://127.0.0.1:8000/index-codebase
```

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Health check |
| POST | `/upload-pdf` | Upload PDF for RAG indexing |
| POST | `/chat` | RAG Q&A over uploaded PDFs |
| POST | `/chat/stream` | RAG chat with SSE token streaming |
| POST | `/agent` | LangGraph agent (tools + reasoning + plan) |
| POST | `/agent/stream` | Agent SSE stream (plan, steps, tokens) |
| POST | `/index-codebase` | Index project source for code search |
| GET | `/pending-changes` | List proposed file edits |
| POST | `/pending-changes/{id}/approve` | Apply proposed edit |

### Example: chat

```json
POST /chat
{ "message": "What is this document about?" }
```

### Example: agent

```json
POST /agent
{ "message": "scan folder backend" }
```

## Configuration (`.env`)

| Variable | Description |
|----------|-------------|
| `OLLAMA_BASE_URL` | Ollama server URL |
| `OLLAMA_MODEL` | Model name (e.g. `llama3`) |
| `ALLOWED_FS_ROOT` | Sandbox for file/folder tools |
| `CHROMA_PATH` | ChromaDB storage directory |
| `UPLOAD_DIR` | PDF upload directory |
| `CORS_ORIGINS` | Comma-separated allowed origins |
| `MAX_UPLOAD_MB` | Max PDF upload size |
| `MAX_FILE_READ_BYTES` | Max bytes for file reader tool |

## Security (Wave 1)

- **Safe calculator** — AST-based math only (no `eval()`)
- **Path sandbox** — file tools restricted to `ALLOWED_FS_ROOT`
- **Ignored dirs** — `venv`, `node_modules`, `.git`, etc. skipped in scans
- **Upload validation** — PDF only, size limits, safe filenames

## Agent flow

1. User message → `ask_agent()`
2. Planner creates execution plan (LangChain + Ollama)
3. Keyword router selects tool or LLM reasoning
4. Result saved to `agent_memory.json`

## Terminal chat

```bash
python advanced_chat.py
```

Commands: `/exit`, `/clear`, `/history`

## Wave 2 highlights

- Async **httpx** Ollama client
- **LangGraph** ReAct agent with tool registry
- **Memory** injected into agent prompts
- **Codebase** semantic index + search tool
- **React** dark UI with streaming chat

## Wave 3 highlights

- **Agent SSE streaming** — `POST /agent/stream` (plan, reasoning, tokens)
- **Human-in-the-loop edits** — `propose_file_edit` tool + `/pending-changes` approval API
- **Restricted shell tool** — `run_command` (opt-in via `ENABLE_SHELL_TOOL=true`)
- **LangSmith tracing** — set `LANGCHAIN_TRACING=true` + API key
- **Docker Compose** — `docker compose up` (ollama + api + frontend)

### Agent streaming

```bash
curl -N -X POST http://127.0.0.1:8000/agent/stream \
  -H "Content-Type: application/json" \
  -d '{"message":"What is 12 * 8?"}'
```

### Pending file approvals

| Method | Path | Description |
|--------|------|-------------|
| GET | `/pending-changes` | List pending edits |
| POST | `/pending-changes/{id}/approve` | Apply edit |
| POST | `/pending-changes/{id}/reject` | Reject edit |

### Docker

```bash
docker compose up --build
# Pull model once:
docker compose exec ollama ollama pull llama3
```

- API: http://localhost:8000  
- Frontend: http://localhost:5173  
- Ollama: http://localhost:11434  

### LangSmith (optional)

```env
LANGCHAIN_TRACING=true
LANGCHAIN_API_KEY=your-key
LANGCHAIN_PROJECT=ollama-agentic-ai
```

## Next improvements (Wave 4+)

- Persistent pending changes store
- True Docker-isolated shell sandbox
- Multi-user auth and sessions
- Agent tool streaming UI polish
