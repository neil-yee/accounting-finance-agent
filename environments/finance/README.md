# Finance sandbox environment

This recipe captures LangSmith's default filesystem as a named release. The first
release keeps its libraries unchanged; `requirements.txt` is intentionally empty
apart from comments. No task files, memory, skills, or local credentials are uploaded
to the builder. This is a filesystem snapshot, not conversation memory.

From the repository root:

```powershell
uv run --locked python scripts/build_sandbox_snapshot.py --activate
```

This uses one temporary cloud builder (1 vCPU, 2 GiB RAM), captures a persistent
snapshot, records the Python/package inventory and build inputs under ignored
`.state/snapshots/`, confirms builder deletion, then sets `SANDBOX_SNAPSHOT_ID` in
local `.env`. It makes no model calls. Snapshot storage and builder compute are
subject to LangSmith billing. The snapshot remains after builder deletion.

Restart `finance-agent --sandbox` to load the selection. Application sandboxes
still receive the explicit allocation in `sandbox.py`; a snapshot does not replace
the compute settings. Existing workspace transfers and cleanup still apply.

## Updating a release

1. Add additional packages with exact versions to `requirements.txt`.
2. Change the tag in `snapshot.json`, for example to `v2`.
3. Build without `--activate` to leave the selected release unchanged.
4. Select the returned immutable ID in deployment configuration or local `.env`.

When extra requirements are present, the builder installs them in
`/opt/finance-python`, a venv that can also read the base's system packages. The
snapshot's saved PATH selects that interpreter for subsequent `python3` commands.
This installation branch is provided for future use; the first release does not
exercise it. Skills alone do not install packages.

The recipe pins the ID of the published `system/default` snapshot inspected for
this release. The default can change over time; builds retain the selected base
until the owner changes `base_snapshot` in `snapshot.json` or passes
`--base-snapshot ID`. The manifest records that ID. For repeatable dependency resolution,
pin transitive dependencies as well when adding packages. Base snapshots and
package sources must still be available to rebuild.

Reusing a tag points it at the new snapshot; running agents select immutable IDs,
so moving a tag does not silently upgrade them. Roll back by setting the previous
ID. Clear `SANDBOX_SNAPSHOT_ID` to use LangSmith's default again. Snapshot IDs are
workspace-specific, so other users build their own. An exported process setting
takes precedence over `.env`; unset it before using `--activate`.

The build script always requests builder deletion in `finally`. If deletion cannot
be confirmed, inspect the printed builder name in LangSmith. Captured snapshots
are retained for explicit release selection and rollback; remove unneeded releases
in LangSmith when no longer referenced.

## GitHub Actions

`.github/workflows/build-sandbox-snapshot.yml` defines a manually triggered build
on main. After pushing the project, configure the repository's Actions secret
`LANGSMITH_API_KEY` and, if needed, variable `LANGSMITH_ENDPOINT`. Then choose
Actions > Build sandbox snapshot > Run workflow. Each run uses a distinct commit/run
tag, publishes its immutable snapshot ID, and saves the manifest for 30 days.
It does not change a running deployment or local .env. Builds are serialized,
require an explicit trigger, and incur sandbox/snapshot usage. The workflow has
not been run, and no GitHub secrets were configured by the local setup.

[LangSmith snapshot documentation](https://docs.langchain.com/langsmith/sandbox-snapshots)
