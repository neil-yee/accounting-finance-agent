---
name: bank-reconciliation
description: Reconcile one month's bank statement to a cash ledger for one account and currency; explain unmatched items, prepare a reconciliation workbook and Word review memo, and draft supported adjustments without posting entries.
---

# Monthly bank reconciliation

This is the first complete workflow procedure for the prototype. Its execution
has not yet been evaluated. Use it for bank-to-ledger reconciliation, not for
general financial statement preparation or a full month-end close.

## 1. Load context and establish scope

Read `/memories/company-profile.md` through file tools for the fictional company's
provisional conventions and matching rules. Task-specific source facts take
precedence over demonstration defaults; document any differences. Also use the
`csv-analysis` and `file-delivery-validation` skills as applicable.

Identify the entity, account, currency, reconciliation period, requested outputs,
and available evidence. Do not infer the reporting period from today's date.
If essential evidence is missing, explain what is missing and prepare a useful
input template or partial analysis; do not invent transactions or balances.

## 2. Inspect and normalize inputs

Expect:

- Bank transactions: stable row/transaction ID, posting date, description,
  reference where available, signed cash amount, and currency/account identity.
- Cash-ledger transactions: stable row/transaction ID, posting date, description,
  reference where available, signed cash amount, and currency/account identity.
- Opening and closing bank and ledger balances with explicit as-of dates.
- Prior reconciliation/open items when available, especially when opening bank
  and ledger balances differ or prior-period items clear in the current month.

Map actual columns explicitly rather than requiring exact input filenames or
headers. For separate debit/credit columns, verify the source convention before
conversion: a ledger debit to cash increases cash, whereas bank statement column
labels may use the bank's perspective. Do not infer sign from the word debit alone.

Use Decimal for amounts. Preserve original row IDs and values in working tables.
Record row counts, totals, date ranges, file names, and mapping decisions. Flag
invalid dates/amounts, missing account/currency data, duplicate IDs, and possible
duplicate transactions. Do not silently drop or deduplicate rows.

Check each source's opening balance plus signed movements against its closing
balance for the same period. Explain source roll-forward differences before
claiming a reconciled result. A missing prior reconciliation is a coverage
limitation, not permission to assume its open items were zero.

## 3. Match and classify

1. Apply the company profile's unique reference, exact signed amount, and date
   window rule. Normalize references only for case and surrounding whitespace;
   retain original values. A reference must be nonempty. Auto-match only when
   the candidate is unique on both sides, then consume each source row once.
2. Repeated references, multiple candidates, missing references, amount/date-only
   candidates, and grouped settlements require review. Record suggested links and
   reasons separately; do not count them as confirmed matches.
3. Inspect remaining items with their evidence. A ledger-only receipt/payment
   may be a deposit in transit/outstanding payment. A bank-only item may be an
   unrecorded fee, interest, receipt, payment, error, or missing ledger coverage.
   These are candidate classifications until supported by source evidence.
4. Carry prior open items forward once, including any that cleared this month.
   Do not add them again if already represented in the provided ledger export.
5. Leave unsupported or ambiguous items unresolved. A matching transaction pair
   does not prove business validity or establish the accuracy of opening balances.

## 4. Build the closing-balance bridge

Show both sides explicitly:

```text
Bank closing balance
+ supported deposits in transit
- supported outstanding payments
+/- supported bank-error corrections
= adjusted bank balance

Ledger closing balance
+ supported unrecorded bank credits (cash increases)
- supported unrecorded bank debits (cash decreases)
+/- supported book-error corrections
= adjusted ledger balance

Residual = adjusted bank balance - adjusted ledger balance
```

Use positive magnitudes for the named addition/subtraction lines and explain each
item's cash effect. Include an adjustment once; matched transactions do not become
reconciling adjustments. Do not force classifications or plug the residual.

Draft journal entries only for supported book adjustments. Include source IDs,
explanation, provisional account mapping and balanced debits/credits. Unsupported
account mappings remain questions. Bank errors normally need bank follow-up rather
than an unsupported book entry. All entries require human review and are never posted.

## 5. Deliver the review package

Unless the task specifies another format, save under `/workspace`:

- `bank_reconciliation.xlsx`: Summary, Source_Bank, Source_Ledger, Matches,
  Reconciling_Items, Exceptions, Proposed_Entries, and Checks sheets.
- `review_memo.docx`: entity/account/period/currency; source coverage; balances
  and residual; material findings without inventing a materiality threshold;
  unresolved items; proposed next steps; and a clear human-review requirement.
- `reconciliation.json`: machine-readable scope, source counts/totals, matched
  row IDs, reconciling items, unresolved IDs, adjusted balances, residual, status,
  assumptions, and validation limitations. Store money as two-decimal strings.
- Supporting scripts and, where useful, `validation-report.json` so a reviewer
  can reproduce the calculation. Do not generate a PDF unless requested.

Use readable Excel formatting and traceable calculations. Follow the file-delivery
skill for reopening, formula/cached-value limitations, and document layout checks.

## 6. Acceptance checks and outcome

- Account/currency/period are explicit and consistent, or discrepancies are flagged.
- Each source ID is accounted for exactly once as matched, open, or invalid;
  matches consume one row from each side without duplication.
- Source counts and monetary totals tie to the working tables; both source
  roll-forwards and the final bridge have independent arithmetic checks.
- Proposed entries balance and have supporting evidence; no entries were posted.
- Every required output reopens; report any checks not performed, including Excel
  recalculation and visual rendering. Structural validity alone is insufficient.

Report `reconciled_draft` only when the residual is zero, source controls and
coverage are established, and no unresolved items undermine the reconciliation.
Explained, supported timing items may remain open. Otherwise report
`needs_investigation` or `blocked_missing_inputs`, with the exact reasons.
Even a zero-residual draft still requires human approval; never claim sign-off.
