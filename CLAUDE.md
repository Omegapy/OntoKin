@AGENTS.md

# Claude sessions

The import above holds the shared project instructions. This file adds only what is specific
to Claude.

- Start from [LOCAL-START-HERE.md](LOCAL-START-HERE.md) when the owner starts persistent local
  development, or types "Go" or "Continue" and `execution_mode` in
  [CURRENT](docs/workflow/CURRENT.json) is `local`. Loading this file declares no execution
  mode, because Claude sessions also run on disposable and remote hosts.
- The six project skills in `.claude/skills/` are links into `.agents/skills/`. Change a skill
  only at its target.
- The application's Worktree mode creates checkouts under `.claude/worktrees/`. They start
  without a `.venv`; the [setup guide](docs/development/LOCAL-SETUP.md) says how to add one.
