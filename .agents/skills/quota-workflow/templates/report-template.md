# Report: <sub-task name>
- Sub-agent: <name>
- Status: DONE / FAILED / BLOCKED
- Time: <start> – <end>
- Plan file: <path to the plan file>
- Task: <which step(s) of the plan this report covers>

## What was done
- (short bullet list)

## Files changed
- <path> (commit hash, if committed: ...)

## Verification
- Command / check run: ...
- Result: ... (with real evidence — data, numbers, output — not claims)

## Not finished / errors
- ...

## Needs a master decision
_(If none, write "None". If there is one, write the question, the options,
and the sub-agent's recommendation.)_
- Question: ...
- Options: (a) ... (b) ...
- Recommendation: ...

## Full report file
<path to this file>

---

## INBOX line format

After writing this report, append ONE line to
`<repo>/.agents/reports/INBOX.md`:

```
| <YYYY-MM-DD HH:MM> | <task> | <DONE / FAILED / BLOCKED> | <report file path> | <needs decision? yes/no> |
```

Example:

```
| 2026-11-08 23:15 | truyenc extension, steps 1-3 | DONE | .agents/reports/truyenc-survey-builder.md | no |
```

The INBOX is a table with this header (create it on first use):

```
| Time | Task | Status | Report | Needs decision? |
|---|---|---|---|---|
```
