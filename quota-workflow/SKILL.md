---
name: quota-workflow
description: Work on a large task without dying when the strong model's quota runs out. Use this skill for any task estimated at more than 30 minutes or with 3+ dependent steps. Plans with Gemini 4 High (Argon Extended Thinking) via MCP gemini-web (consuming ZERO Antigravity Pro quota) or internal fallback, then coordinates and executes step-by-step with cheap model sub-agents (Gemini 3.8 Flash).
---

# quota-workflow (v4.0)

## The idea in one line

Plan with **Gemini 4 High (Argon Extended Thinking via MCP gemini-web)** at **ZERO Antigravity Pro quota cost** — then let the cheap model (**Gemini 3.8 Flash**) coordinate and **execute the plan file via sub-agents**. The plan file is the contract.

## When to use this skill

- The task is estimated at **> 30 minutes** or has **≥ 3 dependent steps**.
- Antigravity Pro model quota is scarce; Gemini Web or Flash model quota is plentiful.
- The task must survive interruptions (quota cut, session error, context limit): progress is saved to files, so any session can resume it.

Do **not** use this workflow for small tasks (< 30 minutes, 1–2 simple steps) — do those directly, the planning overhead is not worth it.

## Model mapping (Antigravity v4.0)

- **External Planner: Gemini 4 High (Gemini 4 Argon with Extended Thinking)** from Google Gemini Web via MCP Server `gemini-web` (`gemini_web_ask(prompt=..., model="gemini-4", extended_thinking=True)`). Consumes **0% Antigravity Pro quota**! Powered by `McpGemini2Antigravity`.
- **Master / Coordinator: Cheap model** — Gemini 3.8 Flash Medium (the `flash` tier). The coordinator receives the task, dispatches recon, calls the Gemini 4 Web MCP for planning, reviews the plan, and dispatches executor sub-agents.
- **Executor / sub-agents: Cheap model** — Gemini 3.8 Flash Medium (the `flash` tier). All bulk work runs here.
- **How a sub-agent is dispatched:** Antigravity's sub-agent call (`invoke_subagent`) takes a `Model` parameter with four values: `inherit`, `pro`, `flash`, `flash_lite`. Always dispatch with all three set explicitly:
  `TypeName: "self"`, `Workspace: "inherit"`, `Model: "flash"`.
  - `TypeName: "self"` is the only valid type for execution steps. Never use `TypeName: "research"` for gathering or network checks — the research sub-agent runs in a read-only sandbox with no network access and cannot fetch anything.
  - `Model` defaults to `"inherit"` if you omit it — always write `Model: "flash"` explicitly.
  - Models are chosen **by tier, not by version name** (`inherit` / `pro` / `flash` / `flash_lite`).

## Tri-Level Planning Fallback Matrix

1. **Mode 1 (Primary — Zero Pro Quota):** Call MCP Server `gemini-web` tool `gemini_web_ask(prompt=..., model="gemini-4", extended_thinking=True)` using credentials from `McpGemini2Antigravity`. Achieves maximum reasoning depth (Extended Thinking) with 0 Antigravity Pro tokens.
2. **Mode 2 (Fallback A — Antigravity Internal Pro):** If MCP `gemini-web` is unavailable (e.g. cookie expired, offline), and the user's Antigravity Pro quota is available, the Master switches to Antigravity internal `pro` tier (Gemini 4 Argon Medium) for 1 turn to plan.
3. **Mode 3 (Fallback B — Flash Emergency Planning):** If both MCP and Antigravity Pro quota are exhausted, the Flash coordinator drafts the plan, tags it `[LOW-CONFIDENCE-PLAN - REQUIRES USER REVIEW]`, and waits for explicit user confirmation before executing.

## Principles

1. **Hard thinking → external strong model (Gemini 4 Web), zero Antigravity Pro quota.** Architecture, decomposition, edge-case analysis.
2. **Heavy doing → cheap model (Gemini 3.8 Flash), many times.** Code writing, running tests, fixing small bugs via sub-agents.
3. **Never pass context by memory — only by FILE.** The plan file is the contract. A session that dies loses nothing if progress is in files.
4. **Every execution step must be verifiable.** No step is "trust me, it's done".
5. **Running out of quota is a signal to STOP, SAVE PROGRESS, and REPORT — not to retry in a loop.**

## The 6-step workflow

### Step 0 — Verify once (before trusting the workflow)

Do this once, before relying on the workflow for real work. Record the results in the project workflow file (section "Verified").

1. **Verify MCP Gemini Web availability (Mode 1):**
   - Check if MCP `gemini-web` tool `gemini_web_ask` or `gemini_web_account_info` is responsive.
   - If available: verify auth cookie status and model availability (`gemini-4`). Mode 1 is ACTIVE.
   - If unavailable: verify whether cookie is present in `.env` (`GEMINI_SECURE_1PSID`) or local browser. If not configured, fall back to Mode 2.
2. **Confirm Antigravity Flash model quota:**
   - Read quota numbers from Antigravity's **Usage view** (weekly and 5-hour limits) for `flash` tier (Gemini 3.8 Flash Medium).
3. **Confirm sub-agent dispatch capability:**
   - Dispatch with `TypeName: "self"`, `Workspace: "inherit"`, `Model: "flash"`.
4. **Confirm file persistence:**
   - Confirm the agent can save a plan file directly to the repo via `write_to_file`.

### Step 1 — Take the task and prepare a context bundle (ONE "Recon Sub-agent" dispatch)

1. The user gives the task.
2. Dispatch **ONE** flash sub-agent (`TypeName: "self"`, `Workspace: "inherit"`, `Model: "flash"`) — the "Recon Sub-agent" — to do both jobs in a single trip:
   (a) record the task in `<repo>/.agents/plans/<date>-<task>-REQUEST.md`: goal, repo, branch, definition of done, and what must NOT be done;
   (b) survey the repo and prepare a short **context bundle** file, `<repo>/.agents/plans/<task>-CONTEXT.md`, at most 1–2 pages (see `templates/context-bundle-template.md`):
   - Repo layout that matters.
   - Project house rules (summarised, with paths to source files).
   - Verified facts (URLs, numbers, observed behaviour).
   - Constraints (files that must not be touched, routes already tried and blocked).
3. The coordinator wakes up only when the Recon Sub-agent reports back, then proceeds to Step 2. Do NOT split into two dispatches.

### Step 2 — Plan with Gemini 4 High via MCP gemini-web (or fallback)

1. **Mode 1 (Primary):** The coordinator formats the planning prompt using `templates/planning-prompt-web.md`, inserting:
   - The contents of `<date>-<task>-REQUEST.md`.
   - The contents of `<task>-CONTEXT.md`.
   - The 5 mandatory sections of `templates/plan-template.md`.
2. Call MCP tool:
   ```python
   gemini_web_ask(prompt=planning_prompt, model="gemini-4", extended_thinking=True)
   ```
   Gemini 4 Argon with Extended Thinking generates a deep, comprehensive plan.
3. If Mode 1 fails (network/cookie error), fallback to Mode 2 (Master internal Pro turn) or Mode 3.
4. The plan contains five mandatory sections: (1) Goal, (2) Context the executor needs, (3) Numbered execution steps (with exact files/commands, expected results, verification, done criteria), (4) Risks & fallbacks, (5) Definition of done.

### Step 3 — Review the plan (Dual Gatekeeper, same turn)

Do this review **in the same coordinator turn as Step 2** — never a separate turn.

1. Coordinator reviews the plan against the Review Checklist (see `WORKFLOW.md`).
2. Write the plan as **ONE complete file in a single `write_to_file` call** — `<repo>/.agents/plans/<date>-<task>.md`.
3. In that **same turn**, dispatch the first flash sub-agent (`TypeName: "self"`, `Workspace: "inherit"`, `Model: "flash"`) for the first execution step cluster. The first sub-agent commits the plan file as Step 0 before starting execution. Target: Plan + Review + Dispatch costs **exactly 1 coordinator turn** on the cheap model!

### Step 4 — Execute with the cheap model (in Antigravity)

Execution is done by dispatching flash sub-agents sequentially.

1. Dispatch **ONE flash sub-agent per step cluster** (`TypeName: "self"`, `Workspace: "inherit"`, `Model: "flash"`), run clusters **sequentially, one at a time** — never in parallel on the same repo (shared `.git`).
2. Each sub-agent does the plan steps **in order**, without scope creep.
3. **Sub-agents never edit the plan's Goal or Steps** — only the **Progress** section is theirs to update. If the plan is flawed, stop and report back to the coordinator.
4. Before each step: echo ("Doing Step N per the plan; rule applied: ...").
5. After each step: update **Progress** in the plan file and **commit progress** immediately.
6. Ambiguity in the plan → **STOP and ask**. Do not guess.
7. Out-of-plan error → record in the plan file, stop, report ("try twice" rule: max 2 fix attempts per error).

### Step 5 — Verify (a gate, never skipped)

1. After each step: run exactly the verification written in the plan.
2. At the end: run full verification and review git diff before final commit.

### Step 6 — Commit, push, report

1. `git pull --rebase` before pushing; retry once on rejection; never force-push.
2. Report: commit hash, verification results (with real evidence), open items.
3. Record lessons learned in the workflow file.

## Git rules (one repo, one writer at a time)

- **Never run sub-agents in parallel writing to the same repo.** Sub-agents share one `.git` directory through `Workspace: "inherit"`. Run clusters sequentially.
- **`.agents/plans/` and `.agents/reports/` are working files, not product files.** Commit them on the working branch (save points), but do NOT merge them into `main`.

## Quota rules (v4.0)

1. **Use Gemini 4 Web (MCP `gemini-web`) for deep planning and architecture — burns 0 Antigravity Pro quota.**
2. **Coordinator and execution run on Gemini 3.8 Flash (`flash` tier) — preserving scarce IDE resources.**
3. **Cheap-model quota exhausted mid-task → save progress to plan file, commit, stop, report.**
4. **Split work into small clusters** so a mid-task interruption loses minimal work.
5. **Never paste secrets, credentials, tokens, or API keys into any external web prompt.** Only code, rules, and task specs.
6. **If a session context fills up, stop, commit progress, and open a new session** pointing to the plan file.

## Master / sub-agent reporting

- **Master/Coordinator is a ROLE, not a continuous process.** Wakes only at decision points (Recon return, Plan review, cluster completions, final report).
- Reporting uses two channels:
  1. **Report file:** `<repo>/.agents/reports/<task>-<subagent>.md` (`templates/report-template.md`).
  2. **Short notification message:** status (done/failed/blocked), report file path, decision question if any.
- **INBOX:** Sub-agent appends one line to `<repo>/.agents/reports/INBOX.md`. Coordinator reads INBOX in batches.

## Project adapter

When starting a task in a project, read that project's own rule files (`AGENTS.md`, `README.md`, skills) and summarise into `CONTEXT.md`:
1. Find house rules.
2. List mandatory rules and prohibited actions.
3. List files to touch and files never to touch.
4. Record verified facts and routes already tried and blocked.

## Changelog

- v4.0 (2026-11-08): Full integration with `McpGemini2Antigravity`. Planner shifts to Gemini 4 High (Argon Extended Thinking) via MCP `gemini_web_ask` from Google Gemini Web, achieving **ZERO Antigravity Pro quota usage**. Tri-level fallback matrix introduced (Mode 1: Web MCP, Mode 2: Internal Pro, Mode 3: Flash Emergency). Coordinator and Subagents run on Gemini 3.8 Flash (`flash` tier). Added `templates/planning-prompt-web.md`.
- v3.1 (2026-11-08): AG re-review micro-optimisations (merged Recon sub-agent dispatch; 1-turn Plan+Review+Dispatch).
- v3 (2026-11-08): Explicit TypeName/Workspace/Model params, Git rules, single plan file.
- v2 (2026-11-08): Internal Pro planner inside Antigravity (Gemini Web app headless browser was blocked).
- v1 (2026-11-08): First version.
