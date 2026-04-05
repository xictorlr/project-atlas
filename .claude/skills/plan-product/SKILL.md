---
name: plan-product
description: Convert a product idea or scope area into a PRD, milestones, risks, and acceptance criteria.
disable-model-invocation: true
allowed-tools: Read Grep Glob Bash
model: sonnet
effort: high
argument-hint: [scope or objective]
---

# /plan-product

Convert a product idea or scope area into a PRD, milestones, risks, and acceptance criteria.

Use the following instructions when this skill is invoked.
The skill should interpret $ARGUMENTS as the active scope, objective, or problem statement.

## Purpose

- Help build Project Atlas in a way that preserves the vault as a first-class artifact.
- Prefer operational clarity over generic brainstorming.
- Keep changes bounded, typed, tested, and documented.

## When to use

- Use this skill when the repo owner asks for a concrete implementation plan.
- Use this skill when the relevant domain needs refactoring or first-time setup.
- Use this skill when the current code or docs are vague, inconsistent, or incomplete.
- Use this skill when the work affects product behavior, data contracts, or operational procedures.

## Inputs to gather

- Inspect the current workspace files, schemas, tests, and docs that relate to $ARGUMENTS.
- Inspect the current source files, schemas, tests, and docs that relate to $ARGUMENTS.
- Inspect the current raw artifact files, schemas, tests, and docs that relate to $ARGUMENTS.
- Inspect the current normalized extract files, schemas, tests, and docs that relate to $ARGUMENTS.
- Inspect the current entity note files, schemas, tests, and docs that relate to $ARGUMENTS.
- Inspect the current concept article files, schemas, tests, and docs that relate to $ARGUMENTS.
- Inspect the current timeline note files, schemas, tests, and docs that relate to $ARGUMENTS.
- Inspect the current search index files, schemas, tests, and docs that relate to $ARGUMENTS.
- Inspect the current answer plan files, schemas, tests, and docs that relate to $ARGUMENTS.
- Inspect the current report files, schemas, tests, and docs that relate to $ARGUMENTS.
- Inspect the current slide deck files, schemas, tests, and docs that relate to $ARGUMENTS.
- Inspect the current simulation run files, schemas, tests, and docs that relate to $ARGUMENTS.
- Inspect the current adapter files, schemas, tests, and docs that relate to $ARGUMENTS.
- Inspect the current audit log files, schemas, tests, and docs that relate to $ARGUMENTS.
- Inspect the current publish target files, schemas, tests, and docs that relate to $ARGUMENTS.
- Inspect the nearest rule files under .claude/rules/.
- Inspect any existing ADRs, runbooks, or manifest formats.
- Identify external integrations and feature flags in scope.

## Outputs to produce

- Produce a concise plan when relevant to $ARGUMENTS.
- Produce specific file changes when relevant to $ARGUMENTS.
- Produce tests or fixtures when relevant to $ARGUMENTS.
- Produce docs updates when relevant to $ARGUMENTS.
- Produce migration notes when relevant to $ARGUMENTS.
- Produce risk notes when relevant to $ARGUMENTS.
- Produce follow-up tasks when relevant to $ARGUMENTS.
- Produce verification steps when relevant to $ARGUMENTS.

## Procedure

1. Restate the task in terms of user workflows, system boundaries, and artifacts.
2. Read the minimal set of files needed to map current behavior.
3. Identify the smallest useful slice that can be completed safely.
4. Propose the target shape before editing many files.
5. Implement the slice, keeping interfaces stable where possible.
6. Run focused verification and capture any gaps explicitly.
7. Update docs, prompts, fixtures, and schemas alongside code.
8. End with a summary of what changed, what remains, and how to verify it.

## Decision rules

- Prefer deterministic transformations for ingest and compilation.
- Use model judgment for synthesis, summarization, contradiction detection, and answer composition.
- Do not let external adapters dictate internal domain models.
- Keep the vault portable and readable in standard Markdown tools.
- Avoid adding vector retrieval until lexical plus structural retrieval is proven insufficient.
- Treat source provenance and generated artifacts as auditable domain objects.
- If a change touches permissions, storage, or third-party calls, add security notes.
- If a change affects stable note paths, add migration and redirect logic.

## File targets

- Touch apps/web only if the task truly requires it; avoid broad unrelated edits.
- Touch services/api only if the task truly requires it; avoid broad unrelated edits.
- Touch services/worker only if the task truly requires it; avoid broad unrelated edits.
- Touch packages/shared only if the task truly requires it; avoid broad unrelated edits.
- Touch packages/prompts only if the task truly requires it; avoid broad unrelated edits.
- Touch packages/adapters only if the task truly requires it; avoid broad unrelated edits.
- Touch vault only if the task truly requires it; avoid broad unrelated edits.
- Touch docs only if the task truly requires it; avoid broad unrelated edits.
- Touch .claude/rules only if the task truly requires it; avoid broad unrelated edits.
- Touch .claude/agents only if the task truly requires it; avoid broad unrelated edits.

## Testing expectations

- Add or update unit tests for pure transformations when it is relevant.
- Add or update integration tests for API and worker boundaries when it is relevant.
- Add or update snapshot tests for Markdown compiler output when it is relevant.
- Add or update fixtures for answer assembly and citation formatting when it is relevant.
- Add or update smoke tests for publish and sync flows when it is relevant.
- Add or update negative tests for permission and privacy boundaries when it is relevant.

## Common pitfalls

- Avoid mixing user-authored notes with machine-generated notes without clear ownership metadata.
- Avoid rewriting note slugs unnecessarily.
- Avoid burying important behavior inside prompts instead of code or config.
- Avoid claiming a knowledge feature works without citation inspection.
- Avoid coupling the UI directly to provider-specific payloads.
- Avoid skipping operational notes for long-running jobs.
- Avoid breaking Obsidian compatibility through exotic markdown constructs.
- Avoid ignoring licensing boundaries for external adapters.

## Delivery checklist

- Confirm code implemented or plan written.
- Confirm tests updated.
- Confirm docs updated.
- Confirm risks called out.
- Confirm rollback or migration plan noted.
- Confirm vault impact reviewed.
- Confirm follow-ups listed.

## Prompt snippets

- Implement $ARGUMENTS as a narrow slice that leaves the rest of the repository stable.
- Review the current implementation for $ARGUMENTS and propose the smallest safe redesign.
- Add tests and documentation for $ARGUMENTS, including vault impact and rollback notes.
- Compare the current and target states for $ARGUMENTS and list contract changes explicitly.

## Appendix

- For workspace: capture inputs, outputs, side effects, idempotency, and observability before changing it.
- For workspace: keep names stable and expose enough metadata for operators to inspect results.
- For source: capture inputs, outputs, side effects, idempotency, and observability before changing it.
- For source: keep names stable and expose enough metadata for operators to inspect results.
- For raw artifact: capture inputs, outputs, side effects, idempotency, and observability before changing it.
- For raw artifact: keep names stable and expose enough metadata for operators to inspect results.
- For normalized extract: capture inputs, outputs, side effects, idempotency, and observability before changing it.
- For normalized extract: keep names stable and expose enough metadata for operators to inspect results.
- For entity note: capture inputs, outputs, side effects, idempotency, and observability before changing it.
- For entity note: keep names stable and expose enough metadata for operators to inspect results.
- For concept article: capture inputs, outputs, side effects, idempotency, and observability before changing it.
- For concept article: keep names stable and expose enough metadata for operators to inspect results.
- For timeline note: capture inputs, outputs, side effects, idempotency, and observability before changing it.
- For timeline note: keep names stable and expose enough metadata for operators to inspect results.
- For search index: capture inputs, outputs, side effects, idempotency, and observability before changing it.
- For search index: keep names stable and expose enough metadata for operators to inspect results.
- For answer plan: capture inputs, outputs, side effects, idempotency, and observability before changing it.
- For answer plan: keep names stable and expose enough metadata for operators to inspect results.
- For report: capture inputs, outputs, side effects, idempotency, and observability before changing it.
- For report: keep names stable and expose enough metadata for operators to inspect results.
- For slide deck: capture inputs, outputs, side effects, idempotency, and observability before changing it.
- For slide deck: keep names stable and expose enough metadata for operators to inspect results.
- For simulation run: capture inputs, outputs, side effects, idempotency, and observability before changing it.
- For simulation run: keep names stable and expose enough metadata for operators to inspect results.
- For adapter: capture inputs, outputs, side effects, idempotency, and observability before changing it.
- For adapter: keep names stable and expose enough metadata for operators to inspect results.
- For audit log: capture inputs, outputs, side effects, idempotency, and observability before changing it.
- For audit log: keep names stable and expose enough metadata for operators to inspect results.
- For publish target: capture inputs, outputs, side effects, idempotency, and observability before changing it.
- For publish target: keep names stable and expose enough metadata for operators to inspect results.
- Always prefer repository evidence over memory.
- Always mention unresolved assumptions.
- Always summarize verification status.
- Always keep generated files reviewable.
