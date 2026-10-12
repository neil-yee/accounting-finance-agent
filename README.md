# Accounting & Finance Agent

> Exploring a reusable, human-supervised AI workflow system for accounting and finance work.

**Status:** Work in progress. The end-to-end finance workflow described below is planned.

## What this project aims to do

This project explores how to build an AI system that can support different accounting and finance workflows. The system brings together a work request, relevant business data and tools, task-specific guidance, human review, and run evaluation.

The goal is to make workflows adaptable to different tasks while keeping important decisions and financial changes reviewable. A month-end close support task will be the first end-to-end demonstration.

## First demonstration: month-end close support

The initial scenario will use synthetic accounting data for a fictional company. Given a close task and supporting records, the agent will:

- Review a trial balance and selected supporting data.
- Identify unusual balances or month-over-month changes.
- Prepare a reviewable workpaper and summary.
- Draft proposed adjusting entries when appropriate.
- Wait for human approval before making a simulated ERP change.
- Record the outcome on the Asana task.

This is a demonstration workflow, not an autonomous accounting system.

## Proposed workflow

```mermaid
flowchart LR
    A[Finance task in Asana] --> B[Agent gathers task context and data]
    B --> C[Accounting tools and document analysis]
    C --> D[Workpaper and proposed action]
    D --> E{Human review}
    E -->|Approve| F[Simulated ERP action]
    E -->|Revise or reject| G[Feedback on the task]
    F --> H[Outcome recorded in Asana]
    G --> B
