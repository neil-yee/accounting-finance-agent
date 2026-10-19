---
name: file-delivery-validation
description: Create or revise Excel, Word, PowerPoint, CSV, or JSON deliverables with explicit source, calculation, structural, and presentation checks before handing them to a human reviewer.
---

# Reviewable file delivery

1. Establish the requested output, reporting period, units, source files, and success
   criteria. Do not infer the reporting period from today's date.
2. Preserve source meaning. Distinguish sourced figures, assumptions, calculations,
   and interpretation. Report missing inputs; do not invent company policies.
3. Inspect the environment before installing a package. Prefer available libraries.
   Libraries commonly present include openpyxl, xlsxwriter, python-docx, and
   python-pptx. Check imports rather than assuming a particular version.
4. Create deliverables and reproducible supporting scripts under /workspace.
   Use one working directory; subfolders are optional. Never claim a local download
   succeeded merely because the remote file was created.
5. Reopen every final file with the appropriate reader. Confirm sheet/section names,
   expected row counts, required fields, and absence of unintended empty outputs.
6. For financial calculations, use Decimal where appropriate, document rounding,
   independently recompute critical totals, tie source data to output, and explain
   exceptions. For integrated statements, check balance sheet equality, opening-to-
   closing cash, retained earnings movements, and signs against source definitions.
7. For Excel, use formulas where they improve reviewability. openpyxl does not
   calculate formulas. If no calculation engine is available, explicitly state that
   recalculation/cached values are unverified; do not report a successful recalc.
   Check formulas for broken references and source ranges. Independently calculated
   values do not prove Excel formula evaluation.
8. For documents and slides, check text, headings, tables, dates, and cited figures.
   Rendering is a separate check. If no renderer is available, say layout was not
   visually verified. Do not generate PDF unless requested.
9. Save validation findings as /workspace/validation-report.json where useful:
   artifact paths, checks actually performed, findings, and remaining limitations.
   Technical checks do not amount to accounting sign-off.
10. Summarize outputs, evidence, and unresolved items for human review. Never approve
    your own output or promote changes to memory, skills, or reusable assets.

The host also performs limited structural checks on changed output files. Those
checks do not verify numerical correctness, formula recalculation, or visual layout.
