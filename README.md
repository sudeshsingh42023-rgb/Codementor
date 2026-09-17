# CodeMentor

An automated code review and progressive-hint feedback tool — built to mirror what a DSA
instructor actually does when grading submissions: run the code, judge correctness,
flag inefficient-but-correct solutions, and give a hint that gets stronger with each
failed attempt instead of handing over the answer immediately.

## Features

- **Sandboxed judge** — runs student Python code in an isolated subprocess with a
  5-second wall-clock timeout and a memory cap, against a bank of test cases per problem.
  Cleanly handles syntax errors, runtime exceptions, wrong answers, and infinite loops.
- **Static complexity analysis** — an AST pass over the submitted code detects nested
  loops, hash map / set usage, and stack patterns *without executing the code*, so a
  "correct but O(n²) when O(n) exists" solution gets flagged rather than just marked pass.
- **Progressive hint ladder** — each problem has 3 hints, from a conceptual nudge to a
  near-solution. The API tracks attempt count per (student, problem) and serves a
  stronger hint on each wrong attempt — the same way an instructor avoids giving away
  the answer on attempt #1.
- **Instructor dashboard** — `/api/dashboard/{problem_id}` aggregates submissions across
  all students on a problem: solve rate, how many hit runtime errors, what fraction used
  a nested loop (a proxy for "haven't seen the optimal pattern yet"), and average attempts
  to solve. This is the "where is this cohort actually stuck" view an SDI needs when
  running a batch through a problem set.

## Architecture

```
app/
  main.py       FastAPI app — routes, request/response models, in-memory submission log
  judge.py      Subprocess-based sandboxed code runner
  hints.py      AST-based static analysis + progressive hint lookup
  problems.py   Problem bank: prompts, test cases, ideal complexity, hint ladders
static/
  index.html    Minimal frontend for testing locally (code editor + results panel)
  app.js        Frontend logic — calls the API, renders pass/fail + hints
requirements.txt
```

**Design note on the sandbox:** this uses `subprocess` + `resource.setrlimit` for
memory, which is fine for a portfolio/demo project but is not a hard security boundary
(no network isolation, no filesystem isolation). `judge.py`'s `run_submission()` is
written as a clean interface specifically so it can be swapped for execution inside a
locked-down container (Docker with `--network none` + read-only fs, nsjail, gVisor)
without touching `main.py` or `hints.py`.

## Running locally

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Then open `http://127.0.0.1:8000` — pick a problem, write code, hit "Run against test cases".

Try this to see the hint ladder in action on Two Sum:
1. Submit `return [0, 0]` — you'll get hint #1 (nudge toward "remember what you've seen").
2. Submit it again — you'll get hint #2 (the hash map approach, spelled out).
3. Submit a brute-force O(n²) double loop that's actually correct — it'll pass, but
   the feedback panel will flag it as correct-but-inefficient and point at the O(n) solution.

## Extending it

- **Add a new problem:** append to `PROBLEMS` in `problems.py` with a prompt, test cases,
  ideal complexity, and a 3-step hint ladder.
- **Smarter hints:** replace `get_hint()` in `hints.py` with a call to an LLM (e.g. the
  Claude API) that reads the student's actual code and the specific failing test case,
  and generates a hint tailored to *that* mistake — while keeping the same "don't reveal
  the answer immediately" ladder structure.
- **Persistence:** swap the in-memory `attempts` / `submission_log` dicts in `main.py`
  for a real database (Postgres/SQLite) to survive restarts and scale past one process.
- **Multi-language support:** `judge.py`'s runner template is Python-specific; add a
  parallel runner script per language and dispatch on a `language` field in the request.

## Resume bullet (starting point — edit to match what you actually built/changed)

> Built an automated code evaluation and mentoring API that sandboxes and judges
> submissions against test cases, statically detects inefficient patterns via AST
> analysis, and serves progressively stronger hints per attempt; added an instructor
> dashboard aggregating cohort-wide solve rates and common mistakes.
