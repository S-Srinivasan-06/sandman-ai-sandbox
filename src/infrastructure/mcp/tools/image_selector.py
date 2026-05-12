"""MCP tool for custom Docker image selection & validation."""
import re
from mcp.server.fastmcp import FastMCP
from src.infrastructure.config import settings
from src.infrastructure.docker.manager import get_client
import logging

logger = logging.getLogger("sandman")
IMAGE_REGEX = re.compile(r"^[\w\.\-]+/[\w\.\-]+:[\w\.\-]+$|^[\w\.\-]+:[\w\.\-]+$")

def register_image_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    def select_custom_image_tool(image_name: str) -> dict:
        """Validate & pull a custom Docker image. Must match allowed registries & tag format."""
        if not IMAGE_REGEX.match(image_name):
            return {"valid": False, "error": "Invalid image format. Use registry/name:tag or name:tag"}
        
        allowed = settings.ALLOWED_CUSTOM_IMAGES
        if allowed and image_name.split(":")[0] not in allowed:
            return {"valid": False, "error": f"Image not in ALLOWED_CUSTOM_IMAGES list."}
        
        try:
            logger.info(f"Pulling custom image: {image_name}")
            get_client().images.pull(image_name)
            return {"valid": True, "image": image_name, "status": "pulled"}
        except Exception as e:
            return {"valid": False, "error": f"Pull failed: {str(e)[:100]}"}
