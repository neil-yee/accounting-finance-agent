# Starter evaluation dataset - Draft

These two synthetic CSV cases exercise simple arithmetic, negative/zero amounts,
structured output, source preservation, and separate workspaces. They are a draft
platform dataset, not an approved finance benchmark. The owner has not reviewed
the task specifications and no results have been measured for this setup.

Run explicitly when you want paid model and sandbox trials:

```powershell
uv run --locked python scripts/evaluate_agent.py --run
```

The runner uses a fresh evaluation thread and workspace per case, invokes the real
agent with the normal context, limits, snapshot, and lifecycle, and saves a local
JSON report. Only source.csv and the prompt are exposed to the agent. Expected
answers remain on the host and are compared independently afterwards. Failed or
incomplete runs fail the case, even if a partial file happens to match. There are
no LLM judges, production data, Asana actions, or automatic scheduled trials.

For these cases, success requires: normal run completion, exact parsed JSON
equality with the expected total and row count, and byte-identical source data.
Other files are permitted. A failure can reflect harness/environment issues as
well as model behavior; inspect the run log/trace before interpreting it.

This does not assess reconciliation, accounting policy, financial-statement
accuracy, formula recalculation, visual presentation, or broader reliability.
Bank reconciliation is now the provisional first finance scenario. Review its
skill acceptance criteria and add representative inputs with independently known
results before making finance-quality claims.
