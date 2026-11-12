# Document skills for Antigravity

Four official Anthropic document skills, copied verbatim from
https://github.com/anthropics/skills on 2026-11-12, Apache 2.0
(LICENSE.txt kept in each skill folder). Do not edit the copied
SKILL.md files to add house rules. House rules live in
FRIESLANDCAMPINA-ADAPTER.md beside this file.

## What is here

- docx: create, read, edit, and analyse Word documents and templates.
- xlsx: create, read, edit, and fix spreadsheets, with formulas.
- pptx: create, read, edit, and analyse slide decks and templates.
- pdf: read, extract, merge, split, rotate, create, and fill PDFs.

Each skill is a folder with SKILL.md, LICENSE.txt, and scripts.
The pdf skill also has forms.md and reference.md.

## How Antigravity finds them

Antigravity loads skills from two places, per its official docs:

- Workspace: `<workspace-root>/.agents/skills/<skill-folder>/`
- Global: `~/.gemini/config/skills/<skill-folder>/`

This folder IS the workspace layout. Copy the four skill folders
from here into one of those two places. Do not rename the folders,
because the folder name is the skill name and the slash command.

## Install on Windows (global, all projects)

In PowerShell, from a clone of this repo:

```
Copy-Item .agents\skills\docx  $env:USERPROFILE\.gemini\config\skills\docx  -Recurse -Force
Copy-Item .agents\skills\xlsx  $env:USERPROFILE\.gemini\config\skills\xlsx  -Recurse -Force
Copy-Item .agents\skills\pptx  $env:USERPROFILE\.gemini\config\skills\pptx  -Recurse -Force
Copy-Item .agents\skills\pdf   $env:USERPROFILE\.gemini\config\skills\pdf   -Recurse -Force
```

Restart Antigravity after copying, then type `/docx` or `/xlsx` or
`/pptx` or `/pdf` in a session, or just ask for a document and let
the agent pick the skill by itself.

## Install for one project only (workspace)

Copy the same four folders into `<project>/.agents/skills/` and
commit them with the project, so the whole team gets them.

## Differences from Claude Code

The copied SKILL.md files were written for Claude's sandbox. Two
assumptions in them do NOT carry over to Antigravity:

- Libraries are NOT preinstalled here. Check the import first
  (python-docx, openpyxl, python-pptx, pypdf, pdfplumber, reportlab,
  pandas, markitdown). Install only the missing one, with pip or npm.
- The `scripts/office/soffice.py` wrapper is for a sandboxed Linux
  environment. On Windows, call LibreOffice directly for conversions
  and recalculation.

Treat the scripts as black boxes. Run them with `--help` first
rather than reading all their source code into context.

## Verify after install

Ask Antigravity for a small test first, for example a spreadsheet
with a SUM formula, and check that the formula recalculates and the
file opens in Excel. Only then use the skills for a real report.
