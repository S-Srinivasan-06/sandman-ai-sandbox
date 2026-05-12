"""Error classification & retry prompt generation."""


def classify_error(stderr: str, exit_code: int) -> str:
    s = stderr.lower()
    if "syntaxerror" in s:
        return "syntax"
    if "modulenotfounderror" in s or "importerror" in s:
        return "dependency"
    if "failed" in s or "assertionerror" in s or "pytest" in s:
        return "test_failure"
    if exit_code == 137:
        return "timeout"
    if exit_code != 0:
        return "runtime"
    return "unknown"


def build_retry_prompt(original_request: str, stderr: str, attempt: int, max_retries: int) -> str:
    error_type = classify_error(stderr, 1 if stderr else 0)
    return (
        f"Attempt {attempt}/{max_retries} failed. Error type: {error_type}\n"
        f"Stderr: {stderr}\n"
        f"Fix the code focusing on {error_type} issues. Do not change working logic.\n"
        f"Original request: {original_request}\n"
        f"Rewrite the file and tests, then run them again."
    )
