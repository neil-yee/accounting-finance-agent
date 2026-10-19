---
name: csv-analysis
description: Inspect CSV financial or operational data, validate its shape and amounts, summarize totals, and produce traceable reviewable outputs without silently dropping bad rows.
---

# CSV analysis

1. Read the source headers, encoding, delimiter, and sample rows before selecting
   columns. Confirm which amount/date/status fields the task requires.
2. Record source row counts. Identify malformed rows, missing values, duplicated
   keys, mixed currencies, and inconsistent dates. Do not silently discard records
   or assume duplicate descriptions mean duplicate transactions.
3. Parse monetary values with decimal.Decimal. State grouping, sign, and rounding
   conventions. Do not combine currencies without an explicit conversion policy.
4. Compute requested totals and reconcile summaries to the included source rows.
   If rows are excluded, report their count, amounts when measurable, and reasons.
5. Produce the requested format. Keep source copies intact, include supporting code
   when useful, and follow the file-delivery-validation skill for final checks.
6. A simple sum is not a reconciliation, audit, or proof that transactions are valid.
