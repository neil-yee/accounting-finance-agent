# Project Task List — Accounting & Finance Agent

| Document field | Value |
|---|---|
| Version | v0.3 working project checklist |
| Owner | Neil Yee |
| Specification | [Agent specification](agent-spec.md) v0.7 |
| Status vocabulary | Done · In progress · Not started · Deferred (intentionally waiting on a prerequisite) · Blocked |

This checklist follows the [ADLC](mental-model/02-adlc.md). Each task points to the specification decision or evaluation it builds or carries out. The [README implementation inventory](../README.md#implementation-status) is the detail source for code status and verification evidence; “Done” here does not imply production readiness.

## Build: Plan

| # | Task | Spec | Done when | Status |
|---|---|---|---|---|
| 1 | Complete and review the project spec first pass | 1–7 | Purpose and scope are clear; all five anatomy functions have a project decision and mechanism; every success criterion maps to an evaluation; release, monitoring, and open decisions are recorded. | In progress |
| 2 | Draw and cross-check the architecture | 2–4, 6.2 | Overview, anatomy, run, and deployment views match spec rows; current and future components are distinguished; trust boundaries and links are correct. | Done |
| 3 | Maintain this ADLC task list and reconcile it with project status | All | Tasks link to the current spec version and reflect README implementation and verification evidence. | Done |

**Plan gate:** not yet met. Some evaluation thresholds, access decisions, and release/monitoring ownership remain open in the spec.

## Build: Configure — platform foundation

| # | Task | Spec | Done when | Status |
|---|---|---|---|---|
| 4 | Set up the repo, dependencies, and local environment | 3.1, 6.2 | The app starts reproducibly from the locked environment. | Done |
| 5 | Create the agent and sandbox execution path | 3.1, 3.3 | The agent can write and run code on a sample file in an isolated sandbox. | Done |
| 6 | Add persistent threads, checkpoints, and per-thread workspace | 3.5 | Conversation state and files survive restart and remain separated by thread. | Done |
| 7 | Implement file copy-in, preservation, and copy-out | 3.3, 3.5 | Inputs remain unchanged; new/changed outputs survive sandbox cleanup; version and conflict behavior is recorded. | Done |
| 8 | Add runtime limits, local locking, and failure handling | 3.1, 3.4, 3.5 | Limits are enforced; concurrent local runs are prevented; failures and recovery are visible. | In progress |
| 9 | Add tracing, provenance, and artifact review records | 3.4, 3.5, 6.1 | A reviewer can follow a run from inputs/configuration to tools, outputs, checks, and review decision. | In progress |
| 10 | Define platform eval cases and graders | 5, 6.1 | Cases cover exact outputs, source preservation, boundaries, restart/revision, and failure behavior with explicit pass conditions. | In progress |

**Configure gate:** the walking skeleton and file transfer exist. Full platform evaluation cases and some live control/recovery checks are outstanding.

## Test — platform foundation

| # | Task | Spec | Done when | Status |
|---|---|---|---|---|
| 11 | Run the platform evaluation plan | 6.1, E-PLAT-1, E-FILE-1, E-CTRL-1, E-PROV-1 | Each planned case passes on the recorded configuration; restart and failure cases are included; findings become tasks or regression cases. | In progress |

**Platform release gate:** not yet passed. The 58-test offline engineering suite and individual smoke runs are useful evidence, but they do not replace the planned eval set or prove finance quality.

## Skill 1 — Plan, Configure, Test

| # | Task | Spec | Done when | Status |
|---|---|---|---|---|
| 12 | Confirm bank reconciliation as Skill 1; collect representative examples and known answers | 4.1, 4.3, 5, E-FIN-1 | Synthetic bank and ledger cases have independent expected matches, exceptions, balances, and outputs. | In progress |
| 13 | Define the skill evaluation plan and acceptance thresholds | 5, 6.1, E-FIN-1 | Every finance success criterion maps to a fixture, check, grader, pass threshold, and required human review. | In progress |
| 14 | Confirm only the access and packages the skill needs | 3.3, 3.4 | Required access is narrowly scoped and tested; no unnecessary external connection or package is enabled. | In progress |
| 15 | Complete the skill procedure and evaluation cases | 3.2, 3.3, 6.1 | `SKILL.md`, known-answer cases, graders, and output review criteria are ready. | In progress |
| 16 | Run Skill 1 evals and platform regression | 6.1, E-FIN-1 | Critical finance checks pass; human review accepts a representative output; platform regressions still pass. | Not started |

**Skill 1 release gate:** not yet passed. The procedure exists, but known-answer fixtures and task evaluations remain outstanding.

## Deploy

| # | Task | Spec | Done when | Status |
|---|---|---|---|---|
| 17 | Complete readiness review and run an approved parallel trial | 6.2 | Owner, data policy, identity/access, limits, stop/rollback, and recovery are confirmed; results match the normal process on a defined sample. | Deferred |
| 18 | Advance only through the supervised-use gate | 6.2 | A defined period/sample meets agreed thresholds with every deliverable human-reviewed; no posting or payment actions are enabled. | Deferred |

**Deployment gate:** no hosted deployment is implemented. Do not advance until the foundation and first finance workflow pass their evaluation gates.

## Monitor

| # | Task | Spec | Done when | Status |
|---|---|---|---|---|
| 19 | Start the monitoring routine for an approved release | 6.3 | Every-run checks and provenance are active; an owner and review cadence are named; first trend review is complete. | Not started |
| 20 | Turn diagnosed findings into controlled changes and regression cases | 6.1, 6.3, 6.4 | Findings are stopped, fixed through Build/Test, or explicitly accepted; fixes add regression cases before release. | Not started |

## Later integration: Asana task-to-review path

These tasks follow the foundation and first finance workflow release gates. Asana integration is intentionally deferred.

| # | Task | Spec | Done when | Status |
|---|---|---|---|---|
| 21 | Define Asana eligibility, identity, and trigger rules | 3.4, 4.2, 7 | Assignment and actionable-feedback rules, narrow permissions, status mapping, and loop prevention are specified. | Deferred |
| 22 | Implement task intake and context gathering | 3.2, 3.3, 4.2 | An eligible task starts the correct thread with task fields, attachments, changes, skills, and relevant prior outputs. | Deferred |
| 23 | Publish status, output links, and handle review/revision | 3.3, 3.4, 3.5, 4.2 | Results appear for review; approval identifies an output version; actionable feedback revises the same task/thread. | Deferred |
| 24 | Evaluate the end-to-end task lifecycle | 6.1, E-ASANA-1 | Five consecutive tasks complete intake, execution, preservation, review/revision; duplicate updates do not start duplicate runs; failure and restart paths pass. | Deferred |

## Adding a later skill

Repeat the Skill 1 planning, configuration, and testing tasks for the new skill. Run the full regression set before release. Changes to model, instructions, knowledge, access, controls, or core execution also require the affected regression cases described in the [ADLC change guidance](mental-model/02-adlc.md#6-changes-after-release).

## Change log

| Version | Date | Change |
|---|---|---|
| v0.3 | 2026-10-23 | Updated section references for spec v0.7; implementation statuses unchanged. |
| v0.2 | 2026-10-22 | Adapted the attached ADLC checklist to current implementation and verification status; linked tasks to the v0.6 spec and evaluation IDs. |
