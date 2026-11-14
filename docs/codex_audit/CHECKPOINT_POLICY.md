# Codex Checkpoint Policy

This project keeps lightweight checkpoint records for every maintained stabilization milestone. A checkpoint is not a release tag; it is a reproducibility note that says what changed, what passed, what remains weak, and where the evidence lives.

## When to Write a Checkpoint

Write or refresh a checkpoint when one of these happens:

- a master-plan row changes status, for example `UNVERIFIED` -> `PARTIAL` or `PARTIAL` -> `PASS-SMOKE`;
- a new validator, smoke script, or default-gate step is added;
- a solver-coupled benchmark or plotfile validator becomes maintained evidence;
- a major risk is reclassified after a fresh audit;
- before handing work to another agent or pausing a long repair sequence.

## Required Content

Each checkpoint should include:

- date/time and agent;
- related master-plan items;
- short summary of the milestone;
- files or modules touched;
- verification commands and result;
- evidence log paths;
- known limitations, explicitly distinguishing smoke evidence from full validation;
- current git status summary.

## Naming

Use `CHECKPOINTS/checkpoint-YYYYMMDD-HHMMSS-<slug>.md` for generated Codex checkpoints. Historical manually written checkpoints may keep their existing numbering.

## Status Rules

Do not use checkpoint text to claim stricter completion than the evidence proves. A passing smoke can support `PASS-SMOKE`, but not full solver validation, GPU readiness, long-time stability, performance scaling, or benchmark accuracy unless the checkpoint cites direct evidence for those claims.
