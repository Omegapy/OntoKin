# Prompts for local sessions

Short instructions for the owner. Type one into a session that was started in the local
project folder. Replace bracketed text. Every prompt relies on
[LOCAL-START-HERE](../../LOCAL-START-HERE.md); none needs an earlier conversation, a ZIP or a
ChatGPT Library link.

## In the Claude desktop application

1. Open the **Code** tab, choose the local environment, and choose the folder of the checkout
   or worktree that holds the selected scope: normally the `OntoKin` clone, or that scope's
   own worktree while its branch is not integrated.
2. Type one of the prompts below. The agent runs the setup and test commands; a terminal is
   not needed.
3. Leave Worktree mode off for a single session in the main checkout. Turn it on deliberately
   before parallel editing, and have the agent report the actual checkout path and branch
   before it edits.
4. Before archiving a session that used a worktree, have the agent commit or otherwise
   preserve the files you need from it.

The Code tab carries its own Claude Code version, which can differ from a terminal
installation. Read it in the application when the version matters.

## Start

```text
Start a local OntoKin session from LOCAL-START-HERE.md.
Scope or question: [what you want done].
Report the startup items, then state one bounded objective before you change anything.
```

A read-only question needs no task record. A new scope is selected through the normal
workflow before work on it begins.

## Continue

```text
Continue.
```

"Go" means the same. The agent resumes the first unmet step of the selected scope, in the
mode that scope's record names.

## Recover

```text
Recover an interrupted local OntoKin session from LOCAL-START-HERE.md.
What happened: [brief description, or unknown].
Inspect the actual working tree, processes, refs and destination state before you retry
anything, then continue from the existing commits and checkpoint.
```

## Checkpoint

```text
Checkpoint this session.
Commit or name every change that should survive, update the task record and the session
checkpoint from observed state, push if that is authorized and confirm it by reading the
remote, and name one next action with the condition that makes it safe.
```
