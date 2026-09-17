"""
judge.py — runs a student's submitted Python code against a problem's test cases
in an isolated subprocess, with a wall-clock timeout and a memory cap.

This is a teaching-grade sandbox (subprocess + resource limits), not a
production-grade one. For a real deployment, swap `_run_in_subprocess` for
execution inside a locked-down container (gVisor/nsjail/Docker with
--network none, read-only fs, seccomp profile) — the interface below
(`run_submission`) would not need to change.
"""

import json
import subprocess
import sys
import tempfile
import textwrap
import time
from pathlib import Path

TIMEOUT_SECONDS = 5
MEMORY_LIMIT_MB = 128

# The runner script executed in the child process. It:
#  1. defines the student's function in an isolated namespace
#  2. runs each test case, capturing pass/fail + wall time
#  3. prints a single JSON blob to stdout (the only channel we trust)
_RUNNER_TEMPLATE = """
import json, resource, sys, time

# --- resource limits (best-effort; POSIX only) ---
try:
    resource.setrlimit(resource.RLIMIT_AS, ({mem_bytes}, {mem_bytes}))
except Exception:
    pass

student_ns = {{}}
try:
    exec(compile({code!r}, "<submission>", "exec"), student_ns)
except Exception as e:
    print(json.dumps({{"error": f"Code failed to define: {{type(e).__name__}}: {{e}}"}}))
    sys.exit(0)

func = student_ns.get({func_name!r})
if func is None:
    print(json.dumps({{"error": "Function {func_name} was not defined."}}))
    sys.exit(0)

results = []
test_cases = json.loads({test_cases_json!r})
for tc in test_cases:
    args = tc["args"]
    expected = tc["expected"]
    start = time.perf_counter()
    try:
        actual = func(*args)
        elapsed_ms = (time.perf_counter() - start) * 1000
        passed = actual == expected
        results.append({{"args": args, "expected": expected, "actual": actual,
                          "passed": passed, "elapsed_ms": round(elapsed_ms, 3)}})
    except Exception as e:
        elapsed_ms = (time.perf_counter() - start) * 1000
        results.append({{"args": args, "expected": expected, "actual": None,
                          "passed": False, "error": f"{{type(e).__name__}}: {{e}}",
                          "elapsed_ms": round(elapsed_ms, 3)}})

print(json.dumps({{"results": results}}))
"""


def run_submission(code: str, function_name: str, test_cases: list) -> dict:
    """Executes `code` in a subprocess and evaluates it against test_cases.
    Returns a dict: { passed_count, total, results: [...], runtime_error: str|None }
    """
    mem_bytes = MEMORY_LIMIT_MB * 1024 * 1024
    script = _RUNNER_TEMPLATE.format(
        code=code,
        func_name=function_name,
        test_cases_json=json.dumps(test_cases),
        mem_bytes=mem_bytes,
    )

    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(script)
        script_path = f.name

    try:
        start = time.perf_counter()
        proc = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
        )
        total_elapsed_ms = (time.perf_counter() - start) * 1000

        if proc.returncode != 0:
            return {
                "passed_count": 0,
                "total": len(test_cases),
                "results": [],
                "runtime_error": proc.stderr.strip()[-800:] or "Process exited with a non-zero status.",
                "total_elapsed_ms": round(total_elapsed_ms, 2),
            }

        payload = json.loads(proc.stdout.strip().splitlines()[-1])
        if "error" in payload:
            return {
                "passed_count": 0,
                "total": len(test_cases),
                "results": [],
                "runtime_error": payload["error"],
                "total_elapsed_ms": round(total_elapsed_ms, 2),
            }

        results = payload["results"]
        passed_count = sum(1 for r in results if r["passed"])
        return {
            "passed_count": passed_count,
            "total": len(results),
            "results": results,
            "runtime_error": None,
            "total_elapsed_ms": round(total_elapsed_ms, 2),
        }

    except subprocess.TimeoutExpired:
        return {
            "passed_count": 0,
            "total": len(test_cases),
            "results": [],
            "runtime_error": f"Timed out after {TIMEOUT_SECONDS}s — check for infinite loops.",
            "total_elapsed_ms": TIMEOUT_SECONDS * 1000,
        }
    finally:
        Path(script_path).unlink(missing_ok=True)
