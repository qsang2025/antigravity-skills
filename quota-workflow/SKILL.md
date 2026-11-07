---
name: quota-workflow
description: Work on a large task without dying when the strong model's quota runs out. Use this skill for any task estimated at more than 30 minutes or with 3+ dependent steps, especially when the strong model (e.g. Gemini 4) has scarce quota and a cheaper model (e.g. Gemini 3.8) has plenty. Plan with the strong model outside the agent (in the Gemini web app), save the plan as a file in the repo, then execute it step by step with the cheap model, with sub-agents reporting back to a master agent through files.
---

# quota-workflow

## The idea in one line

Use the strong model **only to plan** — do that outside the agent, in the
Gemini web app — then let the cheap model **execute the plan file** inside the
agent. The plan file is the contract between planner and executor.

## When to use this skill

- The task is estimated at **> 30 minutes** or has **≥ 3 dependent steps**.
- The strong model's quota is scarce; the cheap model's quota is plentiful.
- The task must survive interruptions (quota cut, session error, context
  limit): progress is saved to files, so any session can resume it.

Do **not** use this workflow for small tasks (< 30 minutes, 1–2 simple
steps) — do those directly, the planning overhead is not worth it.

## Principles

1. **Hard thinking → strong model, few times.** Reasoning, decomposition,
   architecture decisions: strong model.
2. **Heavy doing → cheap model, many times.** Writing code to spec, running
   commands, running tests, fixing small errors: cheap model.
3. **Never pass context by memory — only by FILE.** The plan file is the
   contract. A session that dies loses nothing if progress is in files.
4. **Every execution step must be verifiable.** No step is "trust me, it's
   done".
5. **Running out of quota is a signal to STOP, SAVE PROGRESS, and REPORT —
   not to retry in a loop.**

## The 6-step workflow

### Step 0 — Verify once (before trusting the workflow)

Do this once, before relying on the workflow for real work. Record the
results in the project workflow file.

1. Open `https://gemini.google.com/app` in the browser, signed in with the
   Google account that has Gemini access.
2. Confirm the strong model is available there (record the exact model name
   shown in the UI — names change over time; use what the UI shows).
3. Confirm that account's limits in the Gemini app (free or paid, roughly
   how many prompts per day). If the limit is very low, record the number.
4. Confirm the agent can **copy a long text** (~2,000 words) out of the
   Gemini app and **save it as a file** in the repo.
5. Confirm the agent can switch models in Antigravity (strong ↔ cheap) and
   that the cheap model's quota is sufficient for execution work.
6. Confirm whether Antigravity allows a **different model per sub-agent**
   (master on strong, sub-agents on cheap at the same time). If not, use
   the two-phase model-switching fallback (see "Master / sub-agent" below).

If Step 0 fails (e.g. the Gemini app is unreachable, or the account has no
strong model), stop, report it, and use the fallback: ask another strong
agent to plan (for example Muse), then execute with the cheap model.

### Step 1 — Take the task (any model)

1. The user gives the task.
2. Record it in `<repo>/.agents/plans/<date>-<task>-REQUEST.md`: goal, repo,
   branch, definition of done, and what must NOT be done.
3. **Do not start coding yet.** The first thing after taking a task is to
   plan, not to write code.

### Step 1.5 — Prepare a context bundle (before Step 2)

The planner (Gemini web app) cannot read the repo. Prepare a short
**context bundle** file, `<repo>/.agents/plans/<task>-CONTEXT.md`, at most
1–2 pages, containing:

- The repo layout that matters (paths, what each file/folder does).
- The project's house rules (the mandatory ones, with paths to the source
  files). See "Project adapter" below — read the project's own rule files
  and summarise them here; do not hard-code one project's rules into this
  skill.
- Verified facts (URLs, numbers, observed behaviour of external sites).
- Constraints (files that must not be touched, routes already tried and
  blocked, secrets that must never be pasted anywhere).

If the Gemini app supports file upload, upload the bundle (and the rule
files) instead of pasting text.

### Step 2 — Plan with the strong model (in the Gemini web app)

1. Open `https://gemini.google.com/app` in the browser.
2. Paste the planning prompt (see `templates/planning-prompt.md`) with the
   task description and the context bundle.
3. The strong model returns a plan following the plan template (see
   `templates/plan-template.md`). Ask for the plan in **several numbered
   parts, each ending with a clear marker** (e.g. `--- END OF PART 1 ---`),
   so a long plan can be saved and checked part by part.
4. Save the plan to `<repo>/.agents/plans/<date>-<task>.md` and **commit
   the plan file immediately** (so it survives quota cuts and session
   errors).
5. Do not edit the plan yourself — if it is incomplete or wrong, ask the
   strong model again for the missing part (one more strong-model call is
   still cheaper than executing a wrong plan).

### Step 3 — Review the plan (short, mandatory)

1. Review the plan against the review checklist (see `WORKFLOW.md`).
2. If the plan is missing steps, missing verification, or contradicts the
   project's house rules, go back to Step 2.
3. Only a plan that passes the checklist may be executed. This review costs
   a few minutes and saves hours of rework.

### Step 4 — Execute with the cheap model (in Antigravity)

1. Switch the Antigravity model to the **cheap model**.
2. Read the plan file and do the steps **in order**, without adding steps,
   changing scope, or "improving" the plan.
3. Before each step, **echo** it ("Doing Step N per the plan; rule
   applied: ...") so non-compliance is visible.
4. After each step: update the **Progress** section of the plan file (what
   was done, evidence, time) and **commit the progress** — so if quota runs
   out mid-task, the next session resumes from exactly that step.
5. If something in the plan is ambiguous → **STOP and ask**. Do not guess;
   a weak model guessing wrong costs more quota to fix than asking.
6. If an error is outside the plan → record it in the plan file, stop at
   that step, report. Do not expand scope to "fix it anyway".

### Step 5 — Verify (a gate, never skipped)

1. After each step: run exactly the verification written in the plan.
2. At the end: run the full verification and review the diff before the
   final commit.
3. Errors inside the plan's scope → fix per the plan. Errors outside the
   scope or unfixable → record in the plan file, stop, report.

### Step 6 — Commit, push, report

1. `git pull --rebase` before pushing; if the push is rejected, pull
   --rebase again and retry once; never force-push.
2. Report: commit hash, verification results (with real evidence, not
   claims), and what is still open.
3. Add anything newly learned to the "Lessons learned" section of the
   project workflow file.

## Quota rules (memorise these)

1. **Never start a large task directly on the strong model inside the
   agent.** Always plan first (via the Gemini app), then execute on the
   cheap model.
2. **Strong-model quota exhausted → do not retry in a loop.** Switch to the
   cheap model and work from an existing plan, or plan small tasks on the
   cheap model (note clearly that the plan is lower quality and needs a
   human review).
3. **Cheap-model quota exhausted mid-task → save progress to the plan file,
   commit, stop, report.** Do not spin, do not switch accounts silently.
4. **Split work into small chunks** so a mid-task cut loses as little as
   possible.
5. **A second agent account is only a fallback with the user's approval.**
   Switching accounts mid-task loses context — resuming from the plan file
   is fine, starting over is not.
6. **Every quota exhaustion is a lesson:** record it in the workflow file
   (what error, when, which model, how to avoid it next time).
7. **Do not use teamwork (many sub-agents) when quota is weak.** Teamwork
   multiplies quota consumption — one real case produced 18 coordination
   documents, 0 lines of code, then died on quota. Use teamwork only when
   quota is plentiful, or the task is large enough to justify it.
8. **Always commit progress after each step.** The plan file + progress is
   the save point — without a save point, a quota cut loses everything.
9. **Never paste secrets, credentials, tokens, passwords, or API keys into
   the Gemini web app.** Only code, rules, and task descriptions.
10. **If a session fills its context or starts forgetting, stop, commit
    progress, and open a new session** with the starter message + the plan
    file path — the new session resumes from the file.

## Master / sub-agent reporting

- The **master is a ROLE, not an agent running continuously.** The master
  (strong model) only "wakes up" at decision points: planning, dispatching,
  reading reports, deciding, final verification. Between those points it
  "sleeps" — costing no quota and no context.
- **Sub-agents (cheap model)** work from the plan, handle routine problems
  inside the plan's scope, and escalate only on real decisions or
  out-of-plan errors.
- Reporting uses **two channels**:
  1. **Report file (the single source of truth):** the sub-agent writes a
     report to `<repo>/.agents/reports/<task>-<subagent>.md` following
     `templates/report-template.md`. The file outlives any chat or session.
  2. **Short notification message:** the platform delivers the sub-agent's
     result back to the master. Keep it SHORT: status (done / failed /
     blocked), the report file path, and any question needing a master
     decision. The master opens the full report only when detail is needed.
- **INBOX:** after writing its report, the sub-agent appends ONE line to
  `<repo>/.agents/reports/INBOX.md` (see `templates/report-template.md`
  for the line format). When the master wakes up, it reads ONE file to see
  all pending reports instead of searching the whole chat.
- **Master loop (when awake):** read INBOX → for each DONE + verified
  report, record it and dispatch the next step or move to integration; for
  each FAILED / BLOCKED report, read the full report and decide (fix the
  plan, re-dispatch with different instructions, or escalate to the user);
  answer decision questions decisively and record the decision in the plan
  file. Process reports **in a batch** (read all pending, then decide once)
  rather than one at a time.
- **Escalation rules:** a sub-agent may handle on its own: small errors
  inside the plan, syntax mistakes (fix and retry), small missing data
  (look it up). It MUST escalate: the plan is wrong or contradictory, an
  external site blocks or changed structure, a scope decision is needed,
  quota is exhausted, or the same error survived 2 fix attempts ("try twice"
  rule: attempt a fix at most twice; the third time, stop and report).
- **Model question (verify in Step 0):** if Antigravity does NOT allow a
  different model per sub-agent, use the two-phase fallback: the master
  (strong model) plans and dispatches, then the WHOLE session switches to
  the cheap model for execution; when a master decision is needed, switch
  back to the strong model, decide, then switch back to cheap. This still
  saves quota (the strong model only wakes for decisions) but requires
  switching models back and forth.

## Project adapter (fill this in per project — never hard-code one project's rules into the skill core)

When starting a task in a project, read that project's own rule files and
summarise them into the plan file's "Project context" section:

1. Find the project's rule files (common names: `AGENTS.md`, `README.md`,
   a `skills/` folder, API/contract documents). If the project has none,
   note that explicitly.
2. List the mandatory rules (things that must or must never be done).
3. List the file paths the task will touch and the files that must NOT be
   touched.
4. Note anything already tried and blocked for this task (routes that
   failed — do not retry them).

Example of an adapter: a vBook extension project has `AGENTS.md` (house
rules), a skill folder with `SKILL.md` + mode files, and `extension-api.md`
as the single contract; the adapter would summarise those rules into the
plan. See `examples/vbook-extension.md` for a worked example.

## When this skill does NOT apply

- Tasks under ~30 minutes or with 1–2 simple steps: do them directly.
- Tasks that cannot be split into verifiable steps (pure exploration,
  open-ended research): use the skill's planning part only, loosely.
- The strong model is unavailable everywhere (no Gemini app access and no
  other strong agent): plan with the cheap model for small tasks only, and
  flag the plan as lower quality.

## Changelog

- v1 (2026-11-08): first version. Split from the training plan
  `antigravity-quota-training-plan.md` (Parts 1–3).
