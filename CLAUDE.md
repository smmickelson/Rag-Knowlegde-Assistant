## Rules for AI tools in this repo

Roles:
- DeepSeek writes tests. It does not write or edit app code.
- ChatGPT runs the question round and reviews finished work.
- Claude (chat session, not Claude Code) coaches: drafts specs, reviews test coverage,
  explains results in plain English. The owner is not a coder.
- Claude Code (this tool, running locally) builds app code — and only app code, once
  the owner has written "approved" on the PR. It does not write or edit tests.

Rules:
- Claude Code: only write or edit files in src/ (or wherever app code lives) after approval.
  Do not touch tests/ unless the owner says yes to that exact change.
- Do not commit, push, change branches, or post anything on GitHub.
- Ask before editing any file, and name the file.
- Follow docs/course/routine.md. Nobody builds until the owner writes "approved" on the PR.
- Say "invalid", not "bad".