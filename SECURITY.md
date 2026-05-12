# Security Policy

## Supported Versions
| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | ✅ Yes              |
| < 1.0   | ❌ No               |

## Reporting a Vulnerability
We take security seriously. If you discover a vulnerability in Sandman:
1. **Do not open a public issue.**
2. Email your findings to `security@yourdomain.com` (or use GitHub Private Vulnerability Reporting).
3. Include steps to reproduce, impact assessment, and suggested fixes if possible.
4. You will receive an acknowledgment within 48 hours and a resolution timeline within 7 days.

## Security Design Principles
- **Default Isolation:** Sandboxes run with `network_disabled=True`, `cap_drop=["ALL"]`, `read_only=True`, and non-root users.
- **Opt-in Network:** Internet access is explicitly requested per session. IPv6 is disabled to prevent DNS hangs.
- **Ephemeral Execution:** Containers are destroyed after use. Workspaces are wiped. No persistent state.
- **Strict Validation:** All file paths, package names, and tool arguments are sanitized to prevent traversal/injection.
- **Least Privilege:** Host environment variables are not leaked to containers. API keys are never logged.

## Known Limitations
- Mounting `/var/run/docker.sock` grants the application host-level Docker control. This is required for container management but should be restricted to trusted environments.
- The CLI mode has no authentication. Do not expose it to untrusted networks.
- LLM prompt injection is mitigated via system prompts & tool validation, but cannot be fully guaranteed against adversarial inputs.

## Hardening Checklist for Production
- Run as non-root user in `docker` group
- Set `chmod 600 .env` and `chmod 700 sandbox_workspace/ outputs/ logs/`
- Pin Docker image digests in `config.py`
- Enable log rotation & restrict `logs/` access
- Add auth/rate limiting before web deployment
- Regularly update Docker Engine & Python dependencies
