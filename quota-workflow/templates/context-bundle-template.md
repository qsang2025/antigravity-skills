# Context bundle: <task name>

Purpose: everything the planner (strong model, in the Gemini web app — it
cannot read the repo) needs to write a good plan. Keep it to 1–2 pages.
Paste this into the Gemini app together with the planning prompt, or upload
it (and the rule files listed below) if the app supports file upload.

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
  key into the Gemini web app.

## 5. Source files (for upload or reference)
- `<path to rule file 1>`
- `<path to rule file 2>`
