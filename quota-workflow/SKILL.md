---
name: quota-workflow
description: Work on a large task without dying when the strong model's quota runs out. Use this skill for any task estimated at more than 30 minutes or with 3+ dependent steps, especially when the strong model (e.g. Gemini 4 Argon) has scarce quota and a cheaper model (e.g. Gemini 3.8 Flash) has plenty. Plan with the strong model inside the agent (a few calls only), save the plan as a file in the repo, then execute it step by step with the cheap model, with sub-agents reporting back to a master agent through files.
---

# quota-workflow

## The idea in one line

Use the strong model **only to plan** (a few calls, inside the agent) —
then let the cheap model **execute the plan file**. The plan file is the
contract between planner and executor.

## When to use this skill

- The task is estimated at **> 30 minutes** or has **≥ 3 dependent steps**.
- The strong model's quota is scarce; the cheap model's quota is plentiful.
- The task must survive interruptions (quota cut, session error, context
  limit): progress is saved to files, so any session can resume it.

Do **not** use this workflow for small tasks (< 30 minutes, 1–2 simple
steps) — do those directly, the planning overhead is not worth it.

## Model mapping (Antigravity)

- **Master / planner: strong model** — Gemini 4 Argon Medium (the
  `pro` tier). Use it only for planning (1–2 calls) and master decisions.
  Planning is cheap in calls, so the strong model's small quota is enough
  for this role. The master stays on the strong model for the whole task;
  it does not switch models — execution is done by dispatching sub-agents.
- **Executor / sub-agents: cheap model** — Gemini 3.8 Flash Medium (the
  `flash` tier). All bulk work runs here.
- **How a sub-agent is dispatched:** Antigravity's sub-agent call
  (`invoke_subagent`) takes a `Model` parameter with four values:
  `inherit` (same model as the master), `pro`, `flash`, `flash_lite`.
  Always dispatch with all three set explicitly:
  `TypeName: "self"`, `Workspace: "inherit"`, `Model: "flash"`.
  - `TypeName: "self"` is the only valid type for execution steps.
    Never use `TypeName: "research"` for gathering or network checks —
    the research sub-agent runs in a read-only sandbox with no network
    access and cannot fetch anything.
  - `Model` defaults to `"inherit"` if you omit it — a sub-agent
    dispatched without `Model` silently runs on the strong model and
    burns its scarce quota. Always write `Model: "flash"` explicitly.
  - Models are chosen **by tier, not by version name** — there is no way
    to pass a name like "Gemini 3.8" directly.
- **Model names change over time.** Record the exact names the UI shows
  when you verify (Step 0) and use those.
- **Do NOT route planning through the Gemini web app**
  (`gemini.google.com/app`). Verified 2026-11-08: the agent runs in an
  isolated cloud VM with no Google sign-in, and Google blocks sign-in
  from that VM's headless browser ("This browser or app may not be
  secure"), so the agent cannot use the web app at all — signed in or
  guest. Planning happens inside Antigravity on the strong model.

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
results in the project workflow file (section "Verified").

1. Confirm the strong model is available in Antigravity's model menu
   (record the exact model name shown in the UI — names change over time;
   use what the UI shows). Currently: **Gemini 4 Argon Medium**.
2. Confirm that model's quota. Read the numbers from Antigravity's
   **Usage view** (weekly and 5-hour limits, % remaining, when it
   resets) and record them exactly as shown. Do NOT infer the
   plan/package from the numbers — the displayed numbers do not reliably
   identify the package (e.g. 94% weekly remaining was shown on an
   account whose package is described as a free "gemini 1.5 pro" plan).
   Planning costs only 1–2 calls, so even a small remaining quota is
   enough for the planner role — but record the numbers.
3. Confirm the cheap model is available in Antigravity (currently:
   **Gemini 3.8 Flash Medium**) and its quota is sufficient for execution
   work (bulk calls). Read its numbers from the Usage view too, as in
   item 2.
4. Confirm Antigravity allows a **different model per sub-agent** (master
   on strong, sub-agents on cheap at the same time). Verified 2026-11-08:
   yes — dispatch with `TypeName: "self"`, `Workspace: "inherit"`,
   `Model: "flash"`. The AG agent confirmed it can act as Master on
   Gemini 4 Argon Medium and call flash-tier sub-agents this way. If this
   ever stops working, use the two-phase model-switching fallback (see
   "Master / sub-agent" below).
5. Confirm the agent can save a long plan text as a file in the repo
   (the plan file is the contract — if it cannot be saved, the workflow
   does not work).
6. Confirm the sub-agent call itself works as documented: dispatch a
   test sub-agent with `TypeName: "self"`, `Workspace: "inherit"`,
   `Model: "flash"` on a trivial task and confirm it runs on the cheap
   model. Do not assume the call, the parameter names, or the sample
   values are correct — verify them once, then trust the verified
   result. Anything still unverified is marked NEEDS VERIFICATION, never
   assumed.

Do NOT verify anything through the Gemini web app
(`gemini.google.com/app`): the agent cannot sign in there (see "Model
mapping" above). If Step 0 fails (e.g. the strong model has no quota left
at all), stop, report it, and use the fallback: ask another strong agent
to plan (for example Muse), then execute with the cheap model.

### Step 1 — Take the task and prepare a context bundle (ONE "Recon Sub-agent" dispatch)

1. The user gives the task.
2. Dispatch **ONE** flash sub-agent (`TypeName: "self"`, `Workspace:
   "inherit"`, `Model: "flash"`) — the "Recon Sub-agent" — to do both
   jobs in a single trip:
   (a) record the task in `<repo>/.agents/plans/<date>-<task>-REQUEST.md`:
   goal, repo, branch, definition of done, and what must NOT be done;
   (b) survey the repo and prepare a short **context bundle** file,
   `<repo>/.agents/plans/<task>-CONTEXT.md`, at most 1–2 pages,
   containing:
   - The repo layout that matters (paths, what each file/folder does).
   - The project's house rules (the mandatory ones, with paths to the
     source files). See "Project adapter" below — read the project's own
     rule files and summarise them here; do not hard-code one project's
     rules into this skill.
   - Verified facts (URLs, numbers, observed behaviour of external sites).
   - Constraints (files that must not be touched, routes already tried and
     blocked, secrets that must never be pasted anywhere).
   This is mechanical work — the master (strong model) does not spend a
   call on it.
3. The master only wakes up when the Recon Sub-agent reports back, then
   reads the context bundle and writes the plan (Step 2). Do NOT split
   this into two separate dispatches (one to record the request, one to
   prepare the bundle): each dispatch wakes the master and costs one
   strong-model turn, so two dispatches waste one turn in between.
4. **Do not start coding yet.** The first thing after taking a task is to
   plan, not to write code.

The master planner works from the context bundle, and the executor works
from the plan + bundle without re-reading the whole repo. The Recon
Sub-agent runs on the cheap model, so the master spends only one turn
waking up to read the bundle — then Step 2 (plan + review + dispatch)
runs in that same turn.

### Step 2 — Plan with the strong model (inside Antigravity)

The master (strong model) writes the plan. This is the master's main
job — 1 strong-model turn: plan, review (Step 3), write, dispatch, all
in the same turn. (A rewrite after a failed review is the only
exception, and it costs one more turn.)

1. Give the master the task description and the context bundle (Step
   1). The master runs on the strong model (Gemini 4 Argon Medium,
   tier `pro`); it does not switch models.
2. The plan follows `templates/plan-template.md` — five mandatory
   sections: (1) Goal, (2) Context the executor needs, (3) Numbered
   execution steps (each with what to do, exact files/commands, expected
   result, how to verify, done criterion), (4) Risks & fallbacks,
   (5) Definition of done. The template also has a Progress section (the
   executor updates it) and a Decisions section (the master records
   decisions there).
3. Write the plan as **ONE complete file in a single `write_to_file`
   call** — `<repo>/.agents/plans/<date>-<task>.md`. Do NOT split the
   plan into numbered parts with end markers: `write_to_file` writes
   directly to the VM disk, so there is no clipboard truncation to work
   around, and one complete file is faster and cheaper than several
   partial calls.
4. Do the review (Step 3), the write, and the first dispatch **in this
   same turn** — review the plan against the checklist (Step 3) yourself,
   call `write_to_file` to write the plan, and dispatch the first flash
   sub-agent (`TypeName: "self"`, `Workspace: "inherit"`,
   `Model: "flash"`) for the first execution step cluster. Do NOT commit
   the plan file yourself and do NOT wait for the write to finish before
   dispatching: the first sub-agent commits the plan file as Step 0 of
   the Plan (see `templates/plan-template.md`) before starting its
   cluster, so the plan survives quota cuts and session errors without
   costing the master an extra turn. Target: the whole Plan + Review +
   Dispatch phase costs the master **exactly 1 turn** on the strong
   model.

### Step 3 — Review the plan (short, mandatory)

Do this review **in the same Master turn as Step 2** (see Step 2 item
4) — never a separate turn.

1. Review the plan against the review checklist (see `WORKFLOW.md`).
   In particular, check that every assumption in the plan is either
   verified (with evidence) or marked NEEDS VERIFICATION — an unverified
   assumption is a plan defect, not a detail.
2. If the plan is missing steps, missing verification, or contradicts the
   project's house rules, go back to Step 2 (a rewrite costs one more
   turn — write it right the first time).
3. Only a plan that passes the checklist may be executed. This review costs
   a few minutes and saves hours of rework.

### Step 4 — Execute with the cheap model (in Antigravity)

The master stays on the strong model. Execution is done by dispatching
flash sub-agents — the session model does not switch.

1. Dispatch **ONE flash sub-agent per step cluster**
   (`TypeName: "self"`, `Workspace: "inherit"`, `Model: "flash"`),
   and run the clusters **sequentially, one at a time** — never in
   parallel on the same repo (see the Git rules below). A step cluster is
   a group of related plan steps (e.g. Steps 1–4 of one extension build).
   The first sub-agent commits the plan file as Step 0 of the Plan before
   starting its cluster (see `templates/plan-template.md`).
2. Each sub-agent reads the plan file and does its steps **in order**,
   without adding steps, changing scope, or "improving" the plan.
3. **Never edit the plan's Goal or Steps yourself** — only the Progress
   section (item 5) is yours to update. If the plan is incomplete,
   wrong, or contradicts itself, STOP and report back to the Master —
   the Master fixes the plan. (This rule was in Step 2 in v3, aimed at
   the wrong role: the actor at Step 2 is the Master itself.)
4. Before each step, the sub-agent **echoes** it ("Doing Step N per the
   plan; rule applied: ...") so non-compliance is visible.
5. After each step: update the **Progress** section of the plan file (what
   was done, evidence, time) and **commit the progress** — so if quota runs
   out mid-task, the next session resumes from exactly that step.
6. If something in the plan is ambiguous → **STOP and ask**. Do not guess;
   a weak model guessing wrong costs more quota to fix than asking.
7. If an error is outside the plan → record it in the plan file, stop at
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

## Git rules (one repo, one writer at a time)

- **Never run sub-agents in parallel writing to the same repo.**
  Sub-agents share one `.git` directory through `Workspace: "inherit"`,
  so parallel writers corrupt each other's work. Dispatch ONE flash
  sub-agent per step cluster and run the clusters sequentially (Step 4).
- **Several independent sources in one task** (e.g. several extensions):
  sub-agents may edit files for different sources, but git commits still
  run strictly one at a time, sequentially — never two commits at once.
- **`.agents/plans/` and `.agents/reports/` are working files, not
  product files.** Commit them on the working branch (they are the save
  point), but do NOT merge them into the product repo's `main` branch —
  clean them up before merging, so `main` stays clean and CI is not
  triggered by plan/report churn. The skill itself
  (`.agents/skills/`, `.agents/WORKFLOW.md`) is meant to live in the repo
  and is the exception.

## Quota rules (memorise these)

1. **Use the strong model only for planning and master decisions —
   never for bulk execution.** Plan first (Step 2, on the strong model),
   then execute on the cheap model.
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
9. **Never paste secrets, credentials, tokens, passwords, or API keys
   into any web app or chat outside the agent.** Only code, rules, and
   task descriptions.
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
- **Model choice (verified 2026-11-08):** Antigravity DOES allow a
  different model per sub-agent. Dispatch with `TypeName: "self"`,
  `Workspace: "inherit"`, `Model: "flash"`. The master runs on `pro`
  (Gemini 4 Argon Medium); sub-agents run on `flash` (Gemini 3.8 Flash
  Medium). Models are chosen by tier, not by version name. The AG agent
  confirmed (2026-11-08) it can act as Master on Gemini 4 Argon Medium
  and call flash-tier sub-agents this way. If per-sub-agent choice ever
  stops working, use the two-phase fallback: the master (strong model)
  plans and dispatches, then the WHOLE session switches to the cheap
  model for execution; when a master decision is needed, switch back to
  the strong model, decide, then switch back to cheap. This still saves
  quota (the strong model only wakes for decisions) but requires
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
- The strong model is unavailable in Antigravity (quota exhausted and
  no other strong agent to plan): plan with the cheap model for small
  tasks only, and flag the plan as lower quality.

## Changelog

- v3.1 (2026-11-08): AG re-review micro-optimisations (3, to save
  strong-model turns). Step 1 + Step 1.5 merged into ONE "Recon
  Sub-agent" dispatch (record REQUEST.md + prepare CONTEXT.md in a single
  trip; the Master wakes only once — two separate dispatches would waste
  one strong-model turn in between). The Plan + Review + Dispatch phase
  costs the Master exactly 1 turn: Step 2 reviews (Step 3), writes the
  plan, and dispatches the first flash sub-agent in the same turn; the
  first sub-agent commits the plan file as Step 0 of the Plan (the Master
  no longer commits it). The "Do not edit the plan yourself" rule moved
  from Step 2 to Step 4, where it belongs: sub-agents never edit the
  plan's Goal/Steps, only the Progress section; if the plan is wrong,
  they report back to the Master.
- v3 (2026-11-08): AG review fixes. Dispatch uses `TypeName: "self"` +
  `Workspace: "inherit"` + explicit `Model: "flash"` everywhere (never
  `TypeName: "research"` for gathering/network steps — its sandbox is
  read-only with no network; `Model` defaults to `inherit` if omitted).
  Steps 1/1.5 run on a flash sub-agent so the master spends only 2–3
  strong-model calls. The plan is written as ONE complete file in a
  single `write_to_file` call (no more numbered parts with end markers).
  Git rules added: one writer at a time per repo; `.agents/plans/` +
  `.agents/reports/` stay off `main`. Step 0 now verifies the sub-agent
  call and reads quota from the Usage view (never infer the package from
  the numbers). `templates/planning-prompt.md` removed — the five
  mandatory plan sections live in SKILL.md + the plan template. Starter
  message carries an explicit model-choice permission.
- v2 (2026-11-08): master plans inside Antigravity on Gemini 4 Argon
  Medium; sub-agents execute on the flash tier (Gemini 3.8 Flash Medium).
  The Gemini web app step is REMOVED — Phase 0 verification (2026-11-08)
  proved the agent cannot sign in there (Google blocks the VM's headless
  browser). Per-sub-agent model choice confirmed by tier
  (`inherit`/`pro`/`flash`/`flash_lite`).
- v1 (2026-11-08): first version. Split from the training plan
  `antigravity-quota-training-plan.md` (Parts 1–3).
