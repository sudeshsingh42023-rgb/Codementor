"""
main.py — CodeMentor API.

Endpoints:
  GET  /api/problems              list available problems
  GET  /api/problems/{problem_id} problem detail (prompt + test case count, no hints/answers)
  POST /api/submit                run a student's code, get pass/fail + hint + complexity feedback
  GET  /api/dashboard/{problem_id} instructor view: aggregate stats across all submissions

Run with:  uvicorn app.main:app --reload
"""

from collections import defaultdict
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.hints import analyze_code, complexity_feedback, get_hint
from app.judge import run_submission
from app.problems import get_problem, list_problems

app = FastAPI(title="CodeMentor", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- in-memory stores (swap for a real DB in production) ---
# attempts[(student_id, problem_id)] = number of submissions so far
attempts: dict[tuple[str, str], int] = defaultdict(int)
# submission_log[problem_id] = list of {student_id, passed_count, total, errors: [...]}
submission_log: dict[str, list] = defaultdict(list)


class SubmitRequest(BaseModel):
    student_id: str
    problem_id: str
    code: str


class SubmitResponse(BaseModel):
    passed_count: int
    total: int
    all_passed: bool
    attempt_number: int
    results: list
    runtime_error: Optional[str] = None
    hint: Optional[str] = None
    feedback: Optional[str] = None
    complexity_signals: dict


@app.get("/api/problems")
def api_list_problems():
    return list_problems()


@app.get("/api/problems/{problem_id}")
def api_get_problem(problem_id: str):
    problem = get_problem(problem_id)
    if not problem:
        raise HTTPException(404, "Problem not found")
    return {
        "id": problem["id"],
        "title": problem["title"],
        "difficulty": problem["difficulty"],
        "prompt": problem["prompt"],
        "test_case_count": len(problem["test_cases"]),
    }


@app.post("/api/submit", response_model=SubmitResponse)
def api_submit(req: SubmitRequest):
    problem = get_problem(req.problem_id)
    if not problem:
        raise HTTPException(404, "Problem not found")

    key = (req.student_id, req.problem_id)
    attempts[key] += 1
    attempt_number = attempts[key]

    judge_result = run_submission(req.code, problem["function_name"], problem["test_cases"])
    signals = analyze_code(req.code)
    all_passed = judge_result["runtime_error"] is None and judge_result["passed_count"] == judge_result["total"]

    hint = None
    feedback = None
    if judge_result["runtime_error"]:
        hint = get_hint(problem, attempt_number)
    elif not all_passed:
        hint = get_hint(problem, attempt_number)
    else:
        feedback = complexity_feedback(problem, signals, all_passed)

    submission_log[req.problem_id].append({
        "student_id": req.student_id,
        "attempt_number": attempt_number,
        "passed_count": judge_result["passed_count"],
        "total": judge_result["total"],
        "runtime_error": judge_result["runtime_error"],
        "has_nested_loop": signals.get("has_nested_loop"),
    })

    return SubmitResponse(
        passed_count=judge_result["passed_count"],
        total=judge_result["total"],
        all_passed=all_passed,
        attempt_number=attempt_number,
        results=judge_result["results"],
        runtime_error=judge_result["runtime_error"],
        hint=hint,
        feedback=feedback,
        complexity_signals=signals,
    )


@app.get("/api/dashboard/{problem_id}")
def api_dashboard(problem_id: str):
    """Instructor-facing view: where is this cohort struggling on this problem?"""
    log = submission_log.get(problem_id, [])
    if not log:
        return {"problem_id": problem_id, "submissions": 0, "message": "No submissions yet."}

    total = len(log)
    solved_students = len({e["student_id"] for e in log if e["passed_count"] == e["total"]})
    attempted_students = len({e["student_id"] for e in log})
    runtime_errors = sum(1 for e in log if e["runtime_error"])
    nested_loop_count = sum(1 for e in log if e.get("has_nested_loop"))
    avg_attempts_to_solve = (
        sum(e["attempt_number"] for e in log if e["passed_count"] == e["total"]) / solved_students
        if solved_students else None
    )

    return {
        "problem_id": problem_id,
        "total_submissions": total,
        "students_attempted": attempted_students,
        "students_solved": solved_students,
        "solve_rate": round(solved_students / attempted_students, 2) if attempted_students else 0,
        "runtime_error_rate": round(runtime_errors / total, 2),
        "nested_loop_rate": round(nested_loop_count / total, 2),
        "avg_attempts_to_solve": round(avg_attempts_to_solve, 2) if avg_attempts_to_solve else None,
        "insight": (
            f"{round(nested_loop_count / total * 100)}% of submissions used a nested loop — "
            "worth a quick group walkthrough of the hash-map approach."
            if total and nested_loop_count / total > 0.4 else
            "No dominant misconception detected yet."
        ),
    }


app.mount("/", StaticFiles(directory="static", html=True), name="static")
