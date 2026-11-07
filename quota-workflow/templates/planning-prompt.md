# Planning prompt (paste into the Gemini web app)

Copy the block below, fill in the `<placeholders>`, and paste it into
`https://gemini.google.com/app` together with the context bundle (see
`context-bundle-template.md`).

```
You are a planning architect. Task: <describe the task as specifically as possible>.

Context:
- Repo: <repo URL, branch>
- Project rules: <short summary, with paths to the rule files>
- Relevant structure: <paths, what each file does>
- Constraints: <files that must not be touched, routes already tried and blocked, ...>
- Verified facts: <URLs, numbers, observed behaviour...>

Write a detailed execution plan following exactly this skeleton (do not add sections outside the skeleton, do not write code, only plan):
1. Goal (1 paragraph)
2. Context the executor needs (enough to work without reading the chat history)
3. Numbered steps. Each step has: (a) what to do, (b) exact files/commands, (c) expected result, (d) how to verify, (e) done criterion.
4. Risks & fallbacks (per risk: what to do if it happens, when to stop and report)
5. Definition of done (final checklist)

Requirements: steps small enough for a weaker model to do in one go; every step verifiable; do not invent APIs or paths you have not verified — where you are unsure, write "NEEDS VERIFICATION" instead of guessing.

Return the plan in several numbered parts, each ending with a clear marker line (for example: --- END OF PART 1 ---), so it can be saved part by part.
```
