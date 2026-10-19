# Fictional company reference

**Status:** Provisional demonstration assumptions, maintained by the project owner.
This is synthetic business context, not information about an actual company and
not a statement of statutory accounting or tax policy. Edit this file to change
the demonstration defaults without changing agent code.

## Company and reporting conventions

| Field | Demonstration default |
| --- | --- |
| Entity | Maple Harbour Services Ltd. (fictional) |
| Business | Small professional-services business |
| Location / timezone | Ontario, Canada / America/Toronto |
| Functional and reporting currency | CAD |
| Fiscal year-end | December 31 |
| Management reporting | Monthly, accrual-based; no claim of statutory-framework compliance |
| Financial amounts | CAD dollars, two decimal places, unless a source explicitly states otherwise |
| Rounding | Decimal arithmetic; ROUND_HALF_UP for displayed monetary amounts |
| Default reviewer role | Finance Manager, represented by the human operating this prototype |

These defaults apply to fictional/demo work when the request does not provide
different conventions. Label their use as assumptions. A named real entity or
conflicting source metadata requires that entity's facts; do not relabel real
records as this fictional company or apply these assumptions silently.

The current date is not the reporting period. Obtain the reconciliation month and
account identity from the task and source metadata. No transaction records,
opening balances, closing balances, or prior approvals are supplied by this file.

## Bank reconciliation defaults

| Field | Demonstration default |
| --- | --- |
| Scope | One CAD operating account, one calendar month |
| Bank account label | Main operating account; no real bank details |
| Ledger cash account | 1010 - Operating bank |
| Signed cash convention | Positive = cash receipt/increase; negative = payment/decrease |
| Automatic match | Unique exact reference and exact signed amount, dates no more than 3 calendar days apart |
| Missing references / uncertain links | Suggested candidates only; no automatic match |
| Monetary matching tolerance | CAD 0.00; no amount rounding to force a match |
| Residual tolerance | CAD 0.00; do not plug a difference |
| Exception handling | Report every unmatched, ambiguous, invalid, or conflicting item |
| Proposed bank-fee expense account | 6100 - Bank charges, subject to reviewer confirmation |
| Proposed bank-interest income account | 7100 - Bank interest income, subject to reviewer confirmation |

The date window is a matching heuristic, not proof that two records are the same.
Do not automatically net unrelated transactions, deduplicate real entries, assume
an unmatched item is a timing difference, or write off small differences.
Amounts with more than two decimal places require an explanation or agreed source
mapping before matching. Currency conversion and multiple bank accounts are outside
the first workflow; identify them explicitly rather than silently combining them.

## Review and permissions

- Keep source transaction files unchanged. Work on sandbox copies and save outputs
  in the current thread's working directory.
- Journal entries are proposals only. Show the source evidence, account mapping,
  debit/credit, explanation, and review requirement; never post them to an ERP.
- No payments, external messages, bank instructions, or changes to authoritative
  records. Do not describe the demonstration as an audit or certification.
- Only a human can approve a deliverable. Approval of its file version does not
  approve changes to memory, skills, or reusable assets.
- The owner edits this reference directly. Do not learn new company policies or
  revise this file automatically from task data.
