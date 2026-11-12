# antigravity-skills

A library of reusable skills for Antigravity agents — procedures an agent can
follow for any task, in any project, without re-learning them every session.

Skills are written in the [Agent Skills](https://agentskills.io) format: a
`SKILL.md` file with frontmatter (`name` + `description`) followed by the
instructions. Each skill lives in its own folder and may include a full
workflow document, templates, and worked examples.

## Skills

| Skill | What it does | When to use it |
|---|---|---|
| [quota-workflow](quota-workflow/SKILL.md) | Plan with a strong model, execute with a cheap model, never die on quota | Any task estimated at > 30 minutes or with ≥ 3 dependent steps, when the strong model's quota is scarce |
| [docx](.agents/skills/docx/SKILL.md) | Create, read, edit, and analyse Word documents and templates | Any task that produces or changes a .docx or .dotx file |
| [xlsx](.agents/skills/xlsx/SKILL.md) | Create, read, edit, and fix spreadsheets, with formulas | Any task that produces or changes a .xlsx, .xlsm, or .csv file |
| [pptx](.agents/skills/pptx/SKILL.md) | Create, read, edit, and analyse slide decks and templates | Any task that produces or changes a .pptx or .potx file |
| [pdf](.agents/skills/pdf/SKILL.md) | Read, extract, merge, split, rotate, create, and fill PDFs | Any task that reads or produces a .pdf file |

## Document skills (Anthropic, Apache 2.0)

The four document skills live in `.agents/skills/` in Antigravity's
native layout, copied verbatim from Anthropic's official repo
https://github.com/anthropics/skills on 2026-11-12. Install them
globally on Windows by copying the four folders to
`%USERPROFILE%\.gemini\config\skills\`, or per project by copying
them to `<project>\.agents\skills\`. Full steps, including the
differences from Claude Code, are in
[.agents/skills/README.md](.agents/skills/README.md). House rules for
FrieslandCampina documents are kept separate in
[.agents/skills/FRIESLANDCAMPINA-ADAPTER.md](.agents/skills/FRIESLANDCAMPINA-ADAPTER.md),
never inside the copied skill files.

## How to use a skill in a project

A skill repo on its own does not make Antigravity apply it everywhere. Use
one or more of these distribution mechanisms (in priority order):

1. **Session-starter message (most reliable, works immediately).**
   Paste this as the first message of a new Antigravity session, replacing
   `<skill>` and `<repo-url>` as needed:
   > Before doing anything, read the skill `<skill>` at `<repo-url>` and
   > follow it. Use the strong model only for master planning/decisions,
   > and explicitly dispatch sub-agents with TypeName: 'self',
   > Workspace: 'inherit', and Model: 'flash' for context gathering and
   > plan execution. Do not start coding before you have a reviewed plan
   > file. If you run out of quota at any step, stop, save progress to
   > the plan file, commit, and report — do not retry in a loop.
2. **Pointer file in the project (one-time setup per project).**
   Add a small `.agents/WORKFLOW.md` to the project repo containing one line
   pointing at the skill, e.g.:
   > Working procedure: see skill `quota-workflow` at
   > https://github.com/qsang2025/antigravity-skills
3. **Global Antigravity instructions (if available).**
   If Antigravity offers a place for user-level / global instructions, put
   the skill (or a link to it) there. Whether this exists needs verification.
4. **Clone the skill repo into the workspace.**
   Clone this repo next to the project (or copy the skill folder into the
   project) so the agent can read it directly from disk.

## Adding a new skill

1. Create a folder `<skill-name>/` with a `SKILL.md` (frontmatter `name` +
   `description`, then instructions).
2. Add supporting files as needed (`WORKFLOW.md` for the long version,
   `templates/`, `examples/`).
3. Add a row to the table above.
4. Keep the skill generic: a reusable core plus a per-project adapter
   section. Never hard-code one project's paths or house rules into the
   core — those belong in the adapter, filled in when the skill is used.

## License

MIT. See [LICENSE](LICENSE).
