# Project Atlas Claude Code kit

This package contains a production-grade instruction set for Claude Code.
It is designed for a web application that ingests raw research sources, compiles them into a linked Markdown vault, exposes them through a web UI, and keeps the vault compatible with Obsidian.

The package follows current Claude Code guidance:
- Keep the root CLAUDE.md concise and human-readable.
- Move long, reusable guidance into .claude/rules and .claude/skills.
- Use subagents for isolated work streams.
- Use hooks only for deterministic enforcement and automation.

Suggested usage:
1. Copy the root CLAUDE.md and .claude directory into your repository.
2. Adapt the project name, stack, commands, and deployment details.
3. Keep the short rules in always-on memory and move deep references into skills and docs.
4. Ask Claude Code to scaffold the monorepo, then implement the product slice by slice.

Included sections:
- CLAUDE.md: short project memory loaded every session.
- .claude/rules: modular instructions, some path-gated.
- .claude/skills: long-form workflows for repeatable tasks.
- .claude/agents: specialized subagents for research, architecture, UI, backend, data, QA, security, and Obsidian stewardship.
- .claude/output-styles: optional response formatting modes.
- docs/: detailed design references, product specs, and implementation playbooks.

This package is intentionally large so that Claude Code has a rich operating manual to draw from.
The root CLAUDE.md remains short to avoid bloating every session.

How to inspect what Claude loaded:
- /memory to inspect loaded CLAUDE.md and rules.
- /skills to inspect available skills.
- /agents to inspect custom agents.
- /context to inspect context cost.

Recommended next action in Claude Code:
Use /init only as a bootstrap comparison, then replace the generated output with the package in this directory.
