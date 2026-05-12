# Sandman Permissions & Access Control

This document details every permission, system access, and external dependency required by Sandman. It is intended for security reviews, deployment planning, and least-privilege configuration.

## 🔹 Filesystem Permissions
| Path | Access | Purpose | Security Note |
|------|--------|---------|---------------|
| `sandbox_workspace/` | Read/Write | Ephemeral sandbox mounts & generated code | Auto-cleaned on destroy. Must not be symlinked. |
| `outputs/` | Read/Write | Final validated scripts, ZIP bundles, Dockerfiles | User-accessible artifacts. No execution permissions. |
| `logs/` | Write | Structured JSON logs (`sandman.jsonl`) | May contain stderr/output. Rotate & restrict access. |
| `.env` | Read | API keys, timeouts, paths | Must be `chmod 600`. Never committed to VCS. |
| `/tmp` (inside container) | Read/Write | Container temp space (`tmpfs`) | Mounted as `size=500m,mode=1777`. Isolated per container. |

## 🐳 Docker Daemon Permissions
| Permission | Purpose | Risk Level | Mitigation |
|------------|---------|------------|------------|
| `docker.sock` access | Create/stop/remove containers, mount volumes, exec commands | 🔴 Critical (Host Root Equivalent) | Run Sandman as a dedicated user in `docker` group. Never expose socket to network. |
| Container `exec_run` | Run code, install deps, fetch data inside sandbox | 🟠 High | Runs as non-root (`1000:1000`). Deps install as root only inside ephemeral container. |
| Volume Mount (`/workspace`) | Share host workspace with container | 🟡 Medium | Strict path traversal validation enforced. Read-only root FS. |
| Network Attach (`bridge`) | Outbound internet when `allow_network=True` | 🟡 Medium | DNS forced to `8.8.8.8`/`1.1.1.1`. IPv6 disabled. No inbound ports. |

## 🌐 Network Permissions
| Direction | Endpoint | Purpose | Security Note |
|-----------|----------|---------|---------------|
| Outbound | `api.openai.com`, `api.ollama.com`, `generativelanguage.googleapis.com` | LLM inference | TLS 1.2+. Keys never logged. |
| Outbound | `pypi.org`, `registry.npmjs.org`, `proxy.golang.org` | Dependency installation | Only when `install_dependencies_tool` is called. |
| Outbound | User-requested URLs (e.g., APIs, RSS, Yahoo Finance) | Data fetching | Only when `allow_network=True`. IPv4 enforced. |
| Inbound | `localhost:8080` (optional web UI) | FastAPI/SSE interface | Bound to loopback only. No auth in CLI mode. |

## 🔑 Environment & Secrets Access
| Variable | Used By | Sensitivity | Handling |
|----------|---------|-------------|----------|
| `GOOGLE_API_KEY`, `OPENAI_API_KEY`, `BYOK_API_KEY` | LLM routing | 🔴 High | Read once at startup. Never passed to containers. |
| `OLLAMA_BASE_URL` | Local model routing | 🟡 Medium | Defaults to `http://localhost:11434`. |
| `WORKSPACE_BASE`, `OUTPUT_DIR`, `LOG_DIR` | Path resolution | 🟢 Low | Validated & resolved to absolute paths. |
| `EXEC_TIMEOUT`, `DEP_INSTALL_TIMEOUT` | Execution limits | 🟢 Low | Enforced via shell `timeout` & Docker exec. |

## ⚙️ Subprocess & Execution Permissions
| Action | Purpose | Security Note |
|--------|---------|---------------|
| Spawn MCP server (`sys.executable -m src.infrastructure.mcp.server`) | Tool routing via stdio | Runs with minimal env dict. No host secrets inherited. |
| Shell `timeout` utility | Enforce execution limits | Commands passed as lists where possible. `shlex.quote` applied to user inputs. |
| `requests.post` to Ollama `/api/generate` | VRAM cleanup on exit | Fire-and-forget. Fails silently if Ollama unavailable. |

## 🛡️ Least-Privilege Recommendations
1. **Never run Sandman as root.** Use a dedicated user with Docker group access.
2. **Do not mount `/var/run/docker.sock` in multi-tenant or shared environments.** This grants host-level root access.
3. **Restrict `sandbox_workspace/` and `outputs/` to the Sandman user only.** (`chmod 700`)
4. **Rotate API keys regularly.** Sandman does not cache or store them.
5. **For public/web deployments:** Add authentication, rate limiting, and per-user network isolation before exposing the MCP or FastAPI endpoints.

## ⚠️ Multi-Tenant / Public Deployment Warning
Sandman is designed for **single-user, local, or trusted-team usage**. Deploying it as a public SaaS or multi-tenant service requires:
- Authentication & session isolation
- Rate limiting & quota enforcement
- Custom Docker networks per session (`--internal` or dedicated bridges)
- Prompt injection filtering & output sanitization
- Container resource quotas & cgroup hardening
- Audit logging & secret redaction

Do not expose the CLI, MCP stdio, or FastAPI endpoints to untrusted users without implementing these controls.
