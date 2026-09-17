const API = ""; // same-origin; set to backend URL if hosted separately
const STUDENT_ID = "demo-student"; // swap for real auth in production

let currentProblem = null;

async function loadProblems() {
  const res = await fetch(`${API}/api/problems`);
  const problems = await res.json();
  const list = document.getElementById("problemList");
  list.innerHTML = "";
  problems.forEach((p, i) => {
    const btn = document.createElement("button");
    btn.className = "problem-btn";
    btn.innerHTML = `${p.title} <span class="diff-tag">· ${p.difficulty}</span>`;
    btn.addEventListener("click", () => selectProblem(p.id, btn));
    list.appendChild(btn);
    if (i === 0) selectProblem(p.id, btn);
  });
}

async function selectProblem(id, btnEl) {
  document.querySelectorAll(".problem-btn").forEach(b => b.classList.remove("active"));
  btnEl.classList.add("active");
  const res = await fetch(`${API}/api/problems/${id}`);
  currentProblem = await res.json();
  document.getElementById("prompt").textContent = currentProblem.prompt;
  document.getElementById("resultsList").innerHTML = "";
  document.getElementById("hintBox").innerHTML = "";
  document.getElementById("scoreLine").textContent = `0 / ${currentProblem.test_case_count} test cases passed`;
}

async function runSubmission() {
  const code = document.getElementById("codeInput").value;
  if (!currentProblem || !code.trim()) return;

  const res = await fetch(`${API}/api/submit`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ student_id: STUDENT_ID, problem_id: currentProblem.id, code }),
  });
  const data = await res.json();

  document.getElementById("attemptLabel").textContent = `attempt ${data.attempt_number}`;
  document.getElementById("scoreLine").textContent = `${data.passed_count} / ${data.total} test cases passed`;

  const resultsList = document.getElementById("resultsList");
  resultsList.innerHTML = "";

  if (data.runtime_error) {
    const row = document.createElement("div");
    row.className = "result-row fail";
    row.textContent = `Error: ${data.runtime_error}`;
    resultsList.appendChild(row);
  } else {
    data.results.forEach((r, i) => {
      const row = document.createElement("div");
      row.className = `result-row ${r.passed ? "pass" : "fail"}`;
      row.textContent = r.passed
        ? `✓ case ${i + 1} — got ${JSON.stringify(r.actual)} (${r.elapsed_ms}ms)`
        : `✗ case ${i + 1} — expected ${JSON.stringify(r.expected)}, got ${JSON.stringify(r.actual ?? r.error)}`;
      resultsList.appendChild(row);
    });
  }

  const hintBox = document.getElementById("hintBox");
  hintBox.innerHTML = "";
  if (data.hint) {
    const box = document.createElement("div");
    box.className = "hint-box";
    box.textContent = `Hint: ${data.hint}`;
    hintBox.appendChild(box);
  }
  if (data.feedback) {
    const box = document.createElement("div");
    box.className = "feedback-box";
    box.textContent = data.feedback;
    hintBox.appendChild(box);
  }
}

document.getElementById("btnRun").addEventListener("click", runSubmission);
loadProblems();
