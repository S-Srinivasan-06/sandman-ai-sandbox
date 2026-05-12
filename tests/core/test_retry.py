import pytest
from src.core.retry import classify_error, build_retry_prompt


def test_classify_syntax():
    assert classify_error("SyntaxError: invalid syntax", 1) == "syntax"


def test_classify_dependency():
    assert classify_error("ModuleNotFoundError: No module named 'x'", 1) == "dependency"


def test_classify_test_failure():
    assert classify_error("FAILED test_foo.py::test_bar", 1) == "test_failure"


def test_classify_timeout():
    assert classify_error("", 137) == "timeout"


def test_classify_runtime():
    assert classify_error("ZeroDivisionError: division by zero", 1) == "runtime"


def test_retry_prompt_structure():
    prompt = build_retry_prompt("calc fib", "SyntaxError: bad", 2, 3)
    assert "Attempt 2/3 failed" in prompt
    assert "syntax" in prompt
    assert "calc fib" in prompt
    assert "SyntaxError: bad" in prompt
