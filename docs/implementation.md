# Sandman Implementation Guide

## Architecture Overview
Sandman is a production-grade, autonomous code execution agent built on LangGraph, MCP, and Docker. It follows a strict **Core/Infrastructure/CLI** separation of concerns:
- **Core**: Agent state machine, prompts, retry logic, output packaging
- **Infrastructure**: Docker lifecycle, MCP server, tool definitions, config, model routing
- **CLI**: Entry point, async runner, terminal UI, live output formatting
- **Utils**: Structured logging, custom exceptions, validation helpers

## Directory Structure
```
src/
├── core/          # LangGraph state, prompts, retry, output packaging
├── infrastructure/# Docker manager/executor, MCP server & tools, config, model resolver
├── cli/           # Entry point, async runner, terminal UI formatter
└── utils/         # Logging, errors, validation
```

## Configuration
Managed via `pydantic-settings`. All limits, paths, and keys are loaded from `.env` with strict validation. See `configs/.env.example` for all variables.

## Security Model
- **Default Isolation**: `network_disabled=True`, `cap_drop=["ALL"]`, `no-new-privileges`, `read_only=False` (to support dependency installation)
- **Opt-in Network**: `allow_network=True` enables bridge routing, explicit DNS (`8.8.8.8`, `1.1.1.1`), and disables IPv6 via sysctls to prevent Windows/WSL2 hangs
- **Non-root Execution**: All code runs as `1000:1000`. Dependency installation runs as `root` only inside the ephemeral container
- **Resource Limits**: CPU quota, memory limit, and strict execution timeouts prevent runaway processes
- **Ephemeral Storage**: Only `/workspace` and `/tmp` are writable. Containers auto-remove after use

## Agent Flow
1. User input → CLI resolves model → initializes MCP client
2. LangGraph state machine routes: `agent → tools → check → retry/finalize → cleanup → END`
3. Self-healing: Errors are classified (syntax/dependency/runtime/timeout/test) and injected into retry prompts
4. Output: Validated files are copied to `/outputs/`, zipped with a portable Dockerfile, and returned to the user
5. Cleanup: Guaranteed sandbox destruction + Ollama VRAM unload (if applicable)

## Deployment & Scaling
- Run locally: `make run`
- Docker Compose ready: mount `/var/run/docker.sock`, set env vars, run `python -m src.cli.entry`
- Logging: Structured JSON logs written to `logs/sandman.jsonl` + console
- CI/CD: `make lint`, `make format`, `make test` enforce quality gates

## Development Workflow
1. `make install` → setup dependencies
2. `make run` → start interactive CLI
3. `make test` → run unit/integration tests
4. `make lint` / `make format` → enforce standards

## Known Limitations & Roadmap
- IPv6 DNS hangs on Windows/WSL2 are mitigated via sysctls + Python socket patching
- Network requests are bound by `EXEC_TIMEOUT` (default 60s). Long-running scrapers should be chunked
- Roadmap: Streaming terminal output, auto-retry on network blips, Prometheus metrics, FastAPI web UI, Firecracker/E2B adapter for untrusted workloads
