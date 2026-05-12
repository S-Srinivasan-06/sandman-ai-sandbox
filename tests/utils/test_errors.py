from src.utils.errors import SandmanError, ModelResolutionError, SandboxError, ToolExecutionError


def test_exception_hierarchy():
    assert issubclass(ModelResolutionError, SandmanError)
    assert issubclass(SandboxError, SandmanError)
    assert issubclass(ToolExecutionError, SandmanError)
    assert issubclass(SandmanError, Exception)
