"""Docker container lifecycle manager with security & network hardening."""

import docker
import uuid
import shutil
import time
from pathlib import Path
from src.infrastructure.config import settings
from src.utils.errors import SandboxError
import logging

logger = logging.getLogger("sandman")
_client = None


def get_client():
    """Lazy-initialize the Docker client to avoid import-time crashes."""
    global _client
    if _client is None:
        _client = docker.from_env()
    return _client


def create_sandbox(
    language: str = "python",
    custom_command: str | None = None,
    env_vars: dict | None = None,
    allow_network: bool = False,
) -> dict:
    """Spin up an isolated, hardened Docker container."""
    session_id = str(uuid.uuid4())
    workspace = settings.WORKSPACE_BASE / session_id
    workspace.mkdir(parents=True, exist_ok=True)

    image = settings.ALLOWED_IMAGES.get(language, settings.ALLOWED_IMAGES["python"])
    command = custom_command or "tail -f /dev/null"
    labels = {
        "sandman_managed": "true",
        "created_at": str(int(time.time())),
        "session_id": session_id,
    }

    network_kwargs = {"network_disabled": not allow_network}
    if allow_network:
        network_kwargs["dns"] = settings.CONTAINER_DNS
        network_kwargs["network"] = "bridge"
        if settings.DISABLE_IPV6:
            network_kwargs["sysctls"] = {"net.ipv6.conf.all.disable_ipv6": "1"}

    try:
        container = get_client().containers.run(
            image=image,
            command=command,
            detach=True,
            mem_limit=settings.MEM_LIMIT,
            cpu_quota=settings.CPU_QUOTA,
            user=settings.SANDBOX_USER,
            cap_drop=settings.CONTAINER_CAP_DROP,
            security_opt=settings.CONTAINER_SECURITY_OPT,
            read_only=settings.CONTAINER_READ_ONLY_ROOT,
            tmpfs={"/tmp": f"size={settings.TMPFS_SIZE},mode=1777"},
            environment=env_vars or {},
            volumes={str(workspace.absolute()): {"bind": "/workspace", "mode": "rw"}},
            working_dir="/workspace",
            labels=labels,
            auto_remove=settings.CONTAINER_AUTO_REMOVE,
            **network_kwargs,
        )
        logger.info(
            "sandbox_created",
            extra={"sandbox_id": container.id, "session_id": session_id, "network": allow_network},
        )
        return {
            "sandbox_id": container.id,
            "session_id": session_id,
            "workspace": str(workspace),
            "network_enabled": allow_network,
        }
    except Exception as e:
        raise SandboxError(f"Failed to create sandbox: {e}") from e


def destroy_sandbox(sandbox_id: str, session_id: str) -> str:
    """Stop, remove container, and wipe workspace."""
    try:
        container = get_client().containers.get(sandbox_id)
        container.stop(timeout=5)
        try:
            container.remove(force=True)
        except Exception as e:
            logger.warning(
                "container_remove_failed", extra={"sandbox_id": sandbox_id, "error": str(e)}
            )
    except docker.errors.NotFound:
        pass
    except Exception as e:
        logger.warning("sandbox_stop_failed", extra={"sandbox_id": sandbox_id, "error": str(e)})
    shutil.rmtree(settings.WORKSPACE_BASE / session_id, ignore_errors=True)
    logger.info("sandbox_destroyed", extra={"sandbox_id": sandbox_id, "session_id": session_id})
    return "Sandbox destroyed"


def cleanup_stale_sandboxes(max_age_seconds: int = 86400) -> None:
    """Remove containers older than max_age_seconds."""
    now = int(time.time())
    try:
        for c in get_client().containers.list(all=True, filters={"label": "sandman_managed=true"}):
            if (now - int(c.labels.get("created_at", 0))) > max_age_seconds:
                try:
                    c.stop(timeout=2)
                except:
                    pass
    except Exception as e:
        logger.warning("stale_cleanup_failed", extra={"error": str(e)})
