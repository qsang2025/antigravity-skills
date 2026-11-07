# Context bundle: <task name>

Purpose: everything the planner (master agent, strong model) needs to
write a good plan. Keep it to 1–2 pages. Give this to the master agent
together with the planning prompt (see `planning-prompt.md`).

- Date: <YYYY-MM-DD>
- Repo: <repo URL, branch>
- Task: <one-line task description>

## 1. Repo layout that matters
- `<path>` — <what it does>
- `<path>` — <what it does>

## 2. Project rules that must be followed
_(Read the project's own rule files and summarise the mandatory rules here.
Do not paste whole rule files — summarise, and give the file paths so the
planner can ask for detail if needed.)_
- Rule: ... (source: `<path to rule file>`)
- Rule: ... (source: `<path to rule file>`)
- Must NEVER do: ...

## 3. Verified facts
_(Only facts already checked with real evidence — URLs, numbers, observed
behaviour. Mark anything uncertain as NEEDS VERIFICATION.)_
- ...
- ...

## 4. Constraints
- Files that must NOT be touched: ...
- Routes already tried and blocked (do not retry): ...
- Secrets / credentials: NEVER paste any secret, token, password, or API
  key into any web app or chat outside the agent.

## 5. Source files (for reference)
- `<path to rule file 1>`
- `<path to rule file 2>`
