# quota-workflow — full workflow

This is the long version of the `quota-workflow` skill. The short, runnable
version is `SKILL.md`. This document adds the review checklist, fallbacks,
measurement, and the "training" mechanism. Both documents describe the same
workflow; if they disagree, `SKILL.md` wins for execution and this file wins
for explanation.

## 0. The problem this solves

An agent with a strong model (e.g. Gemini 4) runs out of quota mid-task:
the work is left half-done, context is lost, and the task has to be redone.
A cheap model (e.g. Gemini 3.8) has more quota but is weaker — letting it
plan a complex task on its own produces a poor plan, and fixing that costs
more quota than planning well in the first place.

## 1. The idea

Split the work into two phases with two different models:

- **Phase 1 — Plan (strong model).** Do it **inside the agent**, on the
  strong model (Gemini 4 Argon Medium, tier `pro`). Planning costs only
  1–2 calls, so the strong model's small quota is enough. The strong model
  produces a detailed, verifiable plan. Save the plan as a file in the repo
  and commit it.
- **Phase 2 — Execute (cheap model).** Switch to the cheap model (Gemini
  3.8 Flash Medium, tier `flash`) and execute the plan file step by step,
  committing progress after each step. Sub-agents are dispatched with
  `Model: "flash"`.

**Model mapping:** master = Gemini 4 Argon Medium (`pro` tier); executor
/ sub-agents = Gemini 3.8 Flash Medium (`flash` tier). Models are chosen
by tier via the sub-agent call's `Model` parameter (`inherit` / `pro` /
`flash` / `flash_lite`), not by version name. **Do NOT route planning
through the Gemini web app** (`gemini.google.com/app`) — verified
2026-11-08, the agent cannot sign in there: it runs in an isolated cloud
VM with no Google sign-in, and Google blocks sign-in from that VM's
headless browser ("This browser or app may not be secure").

The plan file is the contract between planner and executor. Any session can
resume the work by reading the file.

## 2. The 6-step workflow (detailed)

### Step 0 — Verify once

Before trusting the workflow, verify its core assumptions once and record
the results in the project workflow file (section "Verified"):

1. The strong model is available in Antigravity's model menu — record the
   exact model name shown in the UI (names change; use what the UI
   shows). Currently: **Gemini 4 Argon Medium**.
2. That model's quota (weekly and 5-hour limits, % remaining, when it
   resets). Planning costs only 1–2 calls, so a small remaining quota is
   enough for the planner role — but record the numbers.
3. The cheap model is available in Antigravity (currently: **Gemini 3.8
   Flash Medium**) and its quota is sufficient for execution work.
4. Antigravity allows a **different model per sub-agent** (master on
   strong, sub-agents on cheap at the same time). Verified 2026-11-08:
   yes — the sub-agent call takes a `Model` parameter (`inherit` / `pro`
   / `flash` / `flash_lite`). If this ever stops working, use the
   two-phase model-switching fallback (master plans + dispatches on
   strong, then the whole session switches to cheap; switch back to
   strong only for master decisions).
5. The agent can save a long plan text as a file in the repo (the plan
   file is the contract).

Do NOT verify anything through the Gemini web app
(`gemini.google.com/app`): the agent cannot sign in there (see section 1).
If Step 0 fails, stop, report, and use a fallback: ask another strong
agent to plan (for example Muse), then execute with the cheap model.

### Step 1 — Take the task

- Record the task in `<repo>/.agents/plans/<date>-<task>-REQUEST.md`:
  goal, repo, branch, definition of done, and what must NOT be done.
- Do not start coding yet.

### Step 1.5 — Prepare a context bundle

The master planner works from this bundle, and the executor works from the
plan + bundle without re-reading the whole repo. Prepare a context bundle
file, `<repo>/.agents/plans/<task>-CONTEXT.md`, at most 1–2 pages (see
`templates/context-bundle-template.md`):

- Repo layout that matters, project house rules (summarised, with paths to
  the source files), verified facts, constraints, and what must not be done.
- Give the bundle to the master planner together with the planning prompt
  (Step 2).

### Step 2 — Plan with the strong model

- Switch the session model to the strong model (Gemini 4 Argon Medium,
  tier `pro`) and give the master the planning prompt (see
  `templates/planning-prompt.md`) with the task description and the context
  bundle.
- Ask for the plan in **several numbered parts, each ending with a clear
  marker** (e.g. `--- END OF PART 1 ---`). Save each part; check all
  markers are present before treating the plan as complete. If a part is
  missing, ask the strong model for that part only.
- Save the plan to `<repo>/.agents/plans/<date>-<task>.md` (template:
  `templates/plan-template.md`) and **commit it immediately**.
- Do not edit the plan yourself — if it is incomplete or wrong, ask the
  strong model again.

### Step 3 — Review the plan

Review against the checklist below. If the plan fails any item, go back to
Step 2. Only a plan that passes may be executed.

**Review checklist**

- [ ] Enough steps to go from start to finish, no missing middle step.
- [ ] Every step has exact files/commands (full paths, not "edit the
      config file").
- [ ] Every step has a concrete verification method and a clear done
      criterion.
- [ ] The plan follows the project's house rules (checked against the
      project's rule files).
- [ ] It says when to STOP (quota out, out-of-scope error, external site
      blocking, ...) instead of pushing on.
- [ ] It says which files must NOT be touched.
- [ ] Anything uncertain is marked "NEEDS VERIFICATION" instead of guessed.
- [ ] Step 0 of the plan is "sync the repo, record HEAD, check the plan's
      assumptions still hold; if they drifted, stop and report."

### Step 4 — Execute with the cheap model

- Switch the agent to the cheap model.
- Do the plan steps **in order**, without adding steps, changing scope, or
  "improving" the plan.
- Before each step, **echo** it ("Doing Step N per the plan; rule
  applied: ...") so non-compliance is visible.
- After each step: update the **Progress** section of the plan file (what
  was done, evidence, time) and **commit the progress**.
- Ambiguity in the plan → **STOP and ask**. Do not guess.
- Error outside the plan → record it in the plan file, stop at that step,
  report. Do not expand scope.

### Step 5 — Verify

- After each step: run exactly the verification written in the plan.
- At the end: run the full verification and review the diff before the
  final commit.
- Errors inside the plan's scope → fix per the plan. Errors outside the
  scope or unfixable → record in the plan file, stop, report.

### Step 6 — Commit, push, report

- `git pull --rebase` before pushing; if the push is rejected, pull
  --rebase again and retry once; never force-push.
- Report: commit hash, verification results (with real evidence), and what
  is still open.
- Add anything newly learned to "Lessons learned" below.

## 3. Quota rules

1. Use the strong model only for planning and master decisions — never
   for bulk execution. Plan first (Step 2, on the strong model), then
   execute on the cheap model.
2. Strong-model quota exhausted → do not retry in a loop. Switch to the
   cheap model and work from an existing plan, or plan small tasks on the
   cheap model (note clearly the plan is lower quality and needs a human
   review).
3. Cheap-model quota exhausted mid-task → save progress to the plan file,
   commit, stop, report. Do not spin, do not switch accounts silently.
4. Split work into small chunks so a mid-task cut loses as little as
   possible.
5. A second agent account is only a fallback with the user's approval.
   Switching accounts mid-task loses context — resuming from the plan file
   is fine, starting over is not.
6. Every quota exhaustion is a lesson: record it (what error, when, which
   model, how to avoid it next time).
7. Do not use teamwork (many sub-agents) when quota is weak. Teamwork
   multiplies quota consumption. Use it only when quota is plentiful, or
   the task is large enough to justify it.
8. Always commit progress after each step. The plan file + progress is the
   save point.
9. Never paste secrets, credentials, tokens, passwords, or API keys into
   any web app or chat outside the agent. Only code, rules, and task
   descriptions.
10. If a session fills its context or starts forgetting, stop, commit
    progress, and open a new session with the starter message + the plan
    file path.
11. Only use this two-phase workflow for tasks estimated at > 30 minutes
    or with ≥ 3 dependent steps. Smaller tasks: do them directly.

## 4. Master / sub-agent reporting

See `SKILL.md` for the full mechanism. Summary:

- The **master is a ROLE, not an agent running continuously.** It wakes
  only at decision points (plan, dispatch, read reports, decide, final
  verification).
- Sub-agents report through **two channels**: a report file in the repo
  (`<repo>/.agents/reports/<task>-<subagent>.md`, template:
  `templates/report-template.md`) and a short notification message (status,
  report path, any question needing a master decision).
- Sub-agents append ONE line per finished piece of work to
  `<repo>/.agents/reports/INBOX.md`. The master reads ONE file to see all
  pending reports, then processes them **in a batch**.
- Escalation: a sub-agent may fix small in-plan errors itself (at most 2
  attempts per error — "try twice" rule). It MUST escalate: plan wrong or
  contradictory, external site blocking or changed, scope decision needed,
  quota exhausted, or the same error survived 2 attempts.

## 5. How this skill is "installed" (the training mechanism)

There is no fine-tuning here. "Training" the agent means three things:

1. **A fixed workflow file in the repo** (this skill, or a pointer to it)
   — every agent session reads it first.
2. **A session-opening ritual:** the first message of every new session
   tells the agent to read the skill and follow it. Starter message:
   > Before doing anything, read the skill `quota-workflow` at
   > https://github.com/qsang2025/antigravity-skills and follow it. Do
   > not start coding before you have a reviewed plan file. If you run
   > out of quota at any step, stop, save progress to the plan file,
   > commit, and report — do not retry in a loop.
3. **A "Lessons learned" section**, updated after every task — this is how
   the workflow improves over time instead of staying a static document.

How well this works depends on the skill being written clearly and every
session actually reading it. That is the known limit — there is no magic.

## 6. Fallbacks

| Situation | Fallback |
|---|---|
| Strong-model quota exhausted in Antigravity | Plan small tasks with the cheap model; large tasks wait for the quota reset or use Muse as planner. |
| Plan file is incomplete (long plan) | Save the plan in numbered parts with end markers; re-ask the master for a missing part only. |
| Cheap model keeps executing the plan wrong | The plan is not detailed enough — go back to Step 2 and make it more detailed (smaller steps, exact commands); do not force the cheap model. |
| Per-sub-agent model choice is not supported | Two-phase model-switching fallback (see SKILL.md). |

## 7. Measuring effectiveness

After each task, record these three numbers in the project workflow file
(section "Measured effectiveness"):

1. Quota errors per task.
2. % of tasks completed without interruption.
3. Number of steps that had to be redone.

If the numbers do not improve after 2–3 tasks, the workflow needs fixing —
do not keep following a workflow that is not working.

## 8. Optimisations

1. **Batch planning:** several similar tasks (e.g. 4 similar extensions)
   get ONE shared plan (common template + per-item sections) — pay the
   planning cost once.
2. **Plans carry full context** (house rules, contracts, verified facts) so
   the cheap model does not have to re-read the whole repo.
3. **Steps small + verifiable after each step** — the cheap model does well
   on small, precisely specified work and poorly on large, vague work.
4. **Optional strong-model final review:** after the cheap model finishes,
   if strong-model quota has recovered, ask it to review the diff quickly
   — only for important tasks, not every task.
5. **Plans are committed, so they are reusable:** a similar future task
   copies an old plan's skeleton and changes only the specifics.

## 9. Verified

- **2026-11-08 (account qsang2025, session "Kiểm Chứng Quy Trình Phase
  0"):** strong model in Antigravity = **Gemini 4 Argon Medium**; cheap
  model = **Gemini 3.8 Flash Medium**. Other models in the menu: Claude
  Opus 5.5 / Sonnet 5.5 Medium, GPT-OSS 120B (Medium). Quota (qsang2025):
  Gemini Models weekly 94% left (reset 6d 7h), 5h 100%; Gemini 4 Argon
  99% weekly left (reset 6d 23h); Claude/GPT weekly 37% left. Per-sub-agent
  model choice: **YES** — sub-agent call takes a `Model` parameter
  (`inherit` / `pro` / `flash` / `flash_lite`); models are chosen by tier,
  not by version name.
- **2026-11-08 — Gemini web app: NOT usable.** The agent runs in an
  isolated cloud VM with no Google sign-in. Guest mode shows no model
  menu or quota; a sign-in attempt was blocked by Google right after the
  email step ("Couldn't sign you in — This browser or app may not be
  secure") because the VM's headless browser is detected as automation.
  The agent never reached the password or phone-code step. **Do not route
  planning through the Gemini web app.**

## 10. Lessons learned

_(Add one line per lesson after each task: date, what happened, what to do
differently.)_

- 2026-11-07: teamwork run on a strong model died on quota ("Individual
  quota reached") after producing only coordination documents and 0 lines
  of code. Lesson: do not use teamwork when quota is weak; plan first,
  then execute with the cheap model. (This incident is what motivated this
  skill.)
- 2026-11-08: Phase 0 verification proved the Gemini web app step does not
  work — the agent cannot sign in from its cloud VM (Google blocks the
  headless browser). User decision: master plans inside Antigravity on
  Gemini 4 Argon Medium (planning costs only 1–2 calls, so the small
  quota is enough); sub-agents execute on the flash tier (Gemini 3.8 Flash
  Medium). The Gemini app step was removed from the skill (v2).

## Changelog

- v2 (2026-11-08): master plans inside Antigravity on Gemini 4 Argon
  Medium; sub-agents execute on the flash tier (Gemini 3.8 Flash Medium).
  Gemini web app step removed (Phase 0 proved the agent cannot sign in
  there). Per-sub-agent model choice confirmed by tier. Verified + Lessons
  learned sections filled in with the Phase 0 results.
- v1 (2026-11-08): first version, split from the training plan
  (Parts 1–3: workflow, self-critique, general scope).
