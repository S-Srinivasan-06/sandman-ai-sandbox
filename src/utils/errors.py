"""Custom exception hierarchy for Sandman."""


class SandmanError(Exception):
    """Base exception for all Sandman errors."""


class ModelResolutionError(SandmanError):
    """Raised when a model cannot be resolved or validated."""


class SandboxError(SandmanError):
    """Raised for sandbox lifecycle or execution failures."""


class ToolExecutionError(SandmanError):
    """Raised when an MCP tool fails during execution."""


class NetworkTimeoutError(SandmanError):
    """Raised when network operations exceed allowed time."""
