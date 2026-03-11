# CLAUDE.md — AIOS Codebase Guide

## Project Overview

AIOS (AI Agent Operating System) is an LLM agent operating system that embeds large language models into an OS-like abstraction layer. It manages scheduling, context switching, memory, storage, and tool management for LLM-based AI agents. The project consists of two parts: the **AIOS Kernel** (this repo) and the **AIOS SDK** ([Cerebrum](https://github.com/agiresearch/Cerebrum)).

## Repository Structure

```
aios/                    # Core kernel implementation
├── config/              # Configuration management (singleton ConfigManager, YAML-based)
├── context/             # LLM context save/restore (SimpleContextManager)
├── hooks/               # Request queue system (global queues for LLM, memory, storage, tool)
│   ├── modules/         # Hook initializers (useCore, useFactory, useScheduler, etc.)
│   ├── stores/          # Thread-safe queue stores (_global.py)
│   ├── types/           # Queue type definitions
│   └── utils/           # Hook utilities
├── llm_core/            # LLM adapter and routing (adapter.py, routing.py)
├── memory/              # Semantic memory with ChromaDB/Qdrant (MemoryNote, BaseMemoryManager)
├── scheduler/           # Task scheduling (FIFOScheduler, RRScheduler)
├── storage/             # File system management (StorageManager, LSFS)
├── syscall/             # System call abstraction (SyscallExecutor, per-type syscalls)
├── tool/                # Tool/plugin management, MCP server, virtual env
└── utils/               # Utilities (logger, id_generator, compressor, calculator)
runtime/                 # Server entry points
├── launch.py            # FastAPI server (main entry point, port 8000)
└── launch_kernel.sh     # Shell launcher: `python -m runtime.launch`
scripts/                 # Utility scripts
├── run_terminal.py      # Interactive terminal UI (rich + prompt_toolkit)
├── list_agents.py       # List available agents
├── run_agent.sh         # Run an agent via shell
├── launch_vllm.sh       # Start vLLM backend
└── launch_sglang.sh     # Start SGLang backend
tests/                   # Test suite (unittest)
├── modules/
│   ├── llm/             # Ollama and OpenAI LLM tests
│   ├── memory/          # Memory manager tests
│   ├── storage/         # Storage tests
│   ├── tool/            # Tool manager tests
│   └── agent_load/      # Agent loading tests
aios-rs/                 # Supplementary Rust implementation (optional)
docs/                    # Documentation and assets
install/                 # Installation scripts
```

## Architecture & Execution Flow

```
Agent/User Request
    ↓
FastAPI REST API (runtime/launch.py) or Terminal UI (scripts/run_terminal.py)
    ↓
SyscallExecutor.execute_request(agent_name, query)
    ↓
Routes by query type:
    ├→ LLMSyscall    → LLM Queue    → Scheduler → LLMAdapter → LLM Provider
    ├→ MemorySyscall  → Memory Queue  → Scheduler → MemoryManager (ChromaDB/Qdrant)
    ├→ StorageSyscall → Storage Queue → Scheduler → StorageManager (LSFS)
    └→ ToolSyscall    → Tool Queue    → Scheduler → ToolManager (MCP)
    ↓
Response returned to Agent/User
```

**Key abstractions:**
- `SyscallExecutor` (`aios/syscall/syscall.py`) — Central router for all system calls
- `LLMAdapter` (`aios/llm_core/adapter.py`) — Multi-backend LLM abstraction (OpenAI, Gemini, Groq, Anthropic, HuggingFace, Ollama, vLLM)
- `BaseScheduler` (`aios/scheduler/base.py`) — Abstract scheduler with FIFO and Round-Robin implementations
- `BaseMemoryManager` (`aios/memory/base.py`) — Thread-safe semantic memory with vector DB backends
- `StorageManager` (`aios/storage/storage.py`) — Linguistic Semantic File System (LSFS)
- `ToolManager` (`aios/tool/manager.py`) — Plugin management via MCP (Model Context Protocol)
- `ConfigManager` (`aios/config/config_manager.py`) — Singleton YAML-based configuration

## Getting Started

### Prerequisites
- Python 3.11+
- API keys for LLM providers (set in `.env` or `aios/config/config.yaml`)

### Installation
```bash
pip install -r requirements.txt
# For CUDA support:
pip install -r requirements-cuda.txt
```

### Configuration
1. Copy `.env.example` to `.env` and fill in API keys
2. Configuration is managed via `aios/config/config.yaml` (generated at runtime, gitignored). See `aios/config/config.yaml.example` for the template.

### Running
```bash
# Start the AIOS kernel server (FastAPI on port 8000)
python -m runtime.launch

# Or use the shell launcher
bash runtime/launch_kernel.sh

# Interactive terminal UI
python scripts/run_terminal.py
```

### Key API Endpoints
- `GET /status` — Server health check
- `POST /query` — Execute a query (LLM, tool, storage, memory)
- `POST /agents/submit` — Submit an agent for execution
- `GET /agents/{execution_id}/status` — Check agent execution status
- `GET /core/llms/list` — List configured LLMs
- `POST /core/refresh` — Reload configuration and restart kernel
- `POST /core/cleanup` — Shut down all components

## Development Workflow

### Running Tests
```bash
# Run individual test modules
python -m unittest tests/modules/llm/ollama/test_single.py
python -m unittest tests/modules/memory/test_memory.py
python -m unittest tests/modules/storage/test_memory.py
python -m unittest tests/modules/tool/test_tool.py
```

### Linting
```bash
# Ruff linter (configured via pre-commit)
ruff check .
```

### Pre-commit Hooks
The project uses pre-commit with:
- `trailing-whitespace` — Removes trailing whitespace
- `end-of-file-fixer` — Ensures files end with newline
- `check-yaml` — Validates YAML syntax
- `check-added-large-files` — Prevents large file commits
- `ruff` (v0.5.0) — Python linter

Install hooks: `pre-commit install`

### CI/CD
GitHub Actions workflows (`.github/workflows/`):
- `test-ollama.yml` — Tests with Ollama LLM backend
- `test-qdrant.yml` — Tests with Qdrant vector DB
- `cancel-workflow.yml` — Cancels redundant workflow runs

Workflows trigger on push/PR to `main`.

## Key Conventions

- **Config is YAML-based** — `aios/config/config.yaml` (gitignored). Use `ConfigManager` singleton for access. API keys are resolved from config first, then environment variables.
- **Hook pattern** — Components are initialized via `use*` functions (e.g., `useCore()`, `useFactory()`, `useStorageManager()`). These return hook-style interfaces.
- **Queue-based communication** — Each subsystem (LLM, memory, storage, tool) has a global request queue in `aios/hooks/stores/_global.py`. The scheduler processes these queues.
- **Cerebrum SDK types** — Query/Response types (`LLMQuery`, `ToolQuery`, `StorageQuery`, `MemoryQuery`) come from the external `cerebrum` package.
- **Scheduler selection** — FIFO is the default. Round-Robin is used when `use_context_manager` is enabled in config.

## Dependencies

Core libraries: `litellm` (LLM routing), `fastapi`/`uvicorn` (REST API), `chromadb`/`qdrant-client` (vector DB), `transformers`/`accelerate` (local models), `sentence-transformers`/`fastembed` (embeddings), `pydantic` (validation), `rich`/`prompt_toolkit` (terminal UI), `redis` (caching), `Cerebrum` (AIOS SDK, installed from git).

## Files Not to Modify

- `aios/config/config.yaml` — Runtime-generated, gitignored
- `.env` — Contains secrets, gitignored
- `proc/` — Runtime process info directory
