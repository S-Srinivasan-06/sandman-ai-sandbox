# Sandman — Autonomous Sandbox Code Runner

Secure, self-healing AI agent that writes, tests, and packages code in isolated Docker containers.

## Quick Start
```bash
git clone <repo>
cd sandman
cp configs/.env.example .env  # Add your API keys
pip install -e .
make run
```

## Features
- LangGraph agent with self-healing retries
- MCP tools for sandbox lifecycle, files, execution
- Opt-in network access with IPv4 enforcement
- Multi-language support (Python, Node, Go)
- Structured JSON logging & strict typing
- Production-ready isolation (non-root, cap-drop, read-only FS)

## Commands
`make run` • `make test` • `make lint` • `make format` • `make clean`
