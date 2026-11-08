# Plan: <task name>
- Date: <YYYY-MM-DD>
- Repo: <repo URL, branch>
- Planner: External Gemini 4 High (Argon Extended Thinking via MCP gemini-web) [or fallback: Antigravity Internal Pro]
- Coordinator: Antigravity Primary Agent (Gemini 3.8 Flash)
- Executor: Antigravity Subagents (Gemini 3.8 Flash)
- Request file: <path to the REQUEST file, if any>
- Context bundle: <path to the CONTEXT file, if any>

<!-- Write the plan as ONE complete file in a single write_to_file call. Do not split it into numbered parts with end markers. -->

## 1. Goal
<One short paragraph: what to do, why, and what exists when it is done.>

## 2. Context the executor needs
- Repo layout that matters (paths, what each file/folder does):
  - ...
- Project rules that must be followed (short quotes, with paths to the source files):
  - ...
- Verified facts (URLs, numbers, observed behaviour):
  - ...
- What must NOT be done (files that must not be touched, routes already tried and blocked):
  - ...

## 3. Execution steps

### Step 0: Sync & check assumptions (always first)
- What to do: first **commit the plan file** — the Master wrote it but did not commit it; committing is your first job, so the plan survives quota cuts and session errors (include the REQUEST/CONTEXT files too if they are not yet committed). Then `git pull --rebase`, record the current HEAD commit, and check the plan's assumptions (file paths, versions, external sites) still hold.
- Expected result: plan file committed; HEAD recorded; all assumptions confirmed.
- How to verify: `git log --oneline -1` output matches the recorded HEAD; `git status` shows a clean tree.
- Done when: the plan file is committed, HEAD is recorded and every assumption is confirmed — or, if anything drifted, STOP and report.
- Rationale: the repo changes constantly; a plan written hours ago can be wrong by execution time.

### Step 1: <step name>
- What to do: ...
- Exact files / commands: ...
- Expected result: ...
- How to verify: ...
- Done when: ...
- Rationale (for non-obvious steps): why this way and not another.
- Decision rules (if applicable): if X happens, do Y; if Z happens, stop.

### Step 2: <step name>
- (same fields as Step 1)

<!-- Add one section per step. Keep steps small enough for the cheap model to do in one go. -->

## 4. Risks & fallbacks
- Risk: ... → If it happens: ... → When to stop and report: ...
- Risk: ... → If it happens: ... → When to stop and report: ...

## 5. Definition of done (final checklist)
- [ ] ...
- [ ] ...
- [ ] All verification steps in section 3 passed, with real evidence.
- [ ] Changes committed and pushed; commit hash recorded below.

## 6. Progress (the executor updates this after each step — commit after each update)
- [ ] Step 0 — <status, evidence, time>
- [ ] Step 1 — <status, evidence, time>
- [ ] Step 2 — <status, evidence, time>

## 7. Decisions made during execution
_(The master records decisions here so later sub-agents can look them up.)_
- <date> — <question> → <decision> — <who decided>
