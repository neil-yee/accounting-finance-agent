# Agent skills

Approved reusable procedures live here, outside the temporary sandbox. The agent
can read this directory through `/skills/` but cannot modify these source files.

Each skill needs its own directory and a `SKILL.md` file:

```text
skills/
  your-skill-name/
    SKILL.md
    references/       # Optional supporting material
    scripts/          # Optional reusable code
```

Start `SKILL.md` with YAML frontmatter:

```markdown
---
name: your-skill-name
description: Explain the task this skill supports and when the agent should use it.
---

# Your skill

Describe the procedure, expected outputs, and checks.
```

The middleware initially supplies skill names and descriptions. The agent reads
the full file when the task matches. Keep detailed references in supporting files.
This README is not a registered skill. Three procedures are bundled:

- `csv-analysis`: inspect and summarize structured transaction data.
- `file-delivery-validation`: check sources, calculations, file structure and presentation.
- `bank-reconciliation`: the first end-to-end finance workflow procedure, covering
  scope, source controls, matching, the balance bridge, draft entries, Excel/Word
  deliverables, exceptions and human review. Execution remains unverified.

The provisional fictional-company reference lives at `memory/company-profile.md`
and is read through `/memories/company-profile.md`. Company conventions are separate
from workflow instructions so either file can be revised without changing agent code.
The reference is demonstration context, not verified information about a real business.

These virtual routes are accessible through file tools, not sandbox shell paths.
If a skill includes a script that must execute remotely, its contents must first
be copied into the sandbox working directory. Python packages still need to be
available or installed there; documenting a library in a skill does not install it.

After adding or changing approved guidance, restart the app and use `:new` for a
fresh thread so cached memory and skill metadata do not obscure the change.

Keep this public directory free of secrets and private company information. Skill
revisions require owner review before use as approved guidance.
