# V5 request and tool ceiling probes

These synthetic probes exercised the v5 limits separately on November 5, 2026. They did not execute an accounting workflow or change the production configuration. The $1 API budget and 30-minute deadline remained in force.

## Provider attempts

The actual `BudgetClient` and v5 `RunControls` sent 100 minimal, independent GPT-6 Luna/high Responses API requests. All returned HTTP 200 and completed; the client rejected request 101 with `Run model-call limit reached (100)` before an HTTP request was sent. The conservative ledger recorded $0.00855, which is an estimate rather than an invoice. These requests were initiated directly by the probe, not by the complete agent graph. A LangSmith root trace covers the probe; the 100 raw HTTP requests were not individually instrumented as model spans. Per-attempt events are in the probe work log.

## Tool attempts

The complete agent graph and filesystem middleware ran against a real v5 sandbox. A scripted model produced one `ls` call per model turn, with no live model requests. Using the normal runner recursion limit of 300, the graph raised `GraphRecursionError` after 74 successful tool calls, before reaching the tool ceiling. The exact count depends on the graph and call pattern; it is not a general hard limit of 74.

The probe was then repeated with a **test-only recursion limit of 600**. The graph completed 100 sandbox tool calls and rejected the 101st with `Run tool-call limit reached (100)`. This verifies the tool middleware ceiling when the graph can reach it; it does not mean every normal v5 run can reach 100 tools before another limit. Both probe sandboxes were confirmed absent via the provider API after cleanup.

## Evidence and implications

- Results and per-attempt work logs are stored in gitignored `.state/evaluations/live-ceilings-v5-20261105/`.
- Exported traces: `01a1ad3a-2a0d-7f93-81f8-17fb19740365` (request probe root), `990f26b4-7de9-4a8d-90e2-9ad8a844d766` (normal recursion), and `a3f3ebff-1364-4920-a7af-c88cd33af30f` (test-only higher recursion).
- Request, tool, recursion, time and dollar limits are separate. The first one reached can stop a run; the exact number of agent actions that fit within the recursion limit varies with graph execution and batching.
- The user authorized a test. No production limits were changed, and this result is not release approval.
