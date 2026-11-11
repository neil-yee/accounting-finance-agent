# Excel benchmark v5 — three-trial results

The fictional two-month Excel fixture v4 was run in three fresh threads under `excel-benchmark-v5`. All three passed the numerical grader and independent recalculation of an unchanged workbook copy. The owner reviewed the outputs and said “Yes, looks good” on November 5, 2026. The work log records approval of each exact, unchanged workspace manifest. This is approval for the synthetic Excel test, not a release decision.

| Trial | Run ID | Numerical gate | Agent time | Provider requests / tool attempts |
|---|---|---|---:|---:|
| 1 | `099f9f9f-c622-44a6-aa10-9a914b216cad` | Pass | 162.264 s | 18 / 23 |
| 2 | `445c2ecd-c6bc-4c61-8851-6adf8b155ebd` | Pass | 153.085 s | 18 / 20 |
| 3 | `25faa341-fd33-4c90-b4a0-69c2c4effb65` | Pass | 168.662 s | 18 / 25 |

The assistant reviewed the narratives against the supplied notes and inspected the rendered pages. Pages 1–4 and 7–8 had identical image hashes across the three outputs; differing pages 5–6 were reviewed separately. No material clipping was observed; some columns were tightly spaced and some continuation pages sparse. The agents each inspected two representative pages, rather than all pages.

The runs used 636,899 tokens in total. The conservative model budget ledger recorded $0.57746425, an estimate rather than an invoice or total infrastructure cost. Exported traces contained 288, 276 and 296 records, respectively, with zero unfinished records. The configuration retained tracing, a 30-minute work deadline and a $1 conservative model API cap per run; it allowed 100 provider requests and 100 tool attempts, with delegation disabled.

Series ID: `1d094542-a7e9-46a5-83d6-cfcc91a123cd`. The machine-readable series and owner review pack are saved in the gitignored `.state/evaluations/` directory; traces are in `traces/` and artifacts in their thread workspaces. The three workbook SHA-256 values are `f7bda77a068d4ba4f8ad5616a215e1413da8b0428573a318d1deaa559deab00f`, `a2b6b88f217efcfd5dd842ec4f73f8ca0e624ee58396fcb814b6b6ff06162a8b`, and `2dba8a8d0429a0d5d0ad060a49f2689054457b5f17bf8863603c9d7817247d2a`.

This is evidence for one fictional Excel task and the tested configuration, not general accounting reliability. Selected foundation checks were subsequently repeated under v5; see their [results and limits](foundation-v5-2026-11-05.md), the [benchmark and rubric](excel-benchmark.md), and [earlier v3 foundation evidence](test-gate-followup-2026-10-25.md).
