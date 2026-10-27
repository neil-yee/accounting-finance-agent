"""Offline boundary checks for evaluator-controlled workbook recalculation."""
from contextlib import contextmanager
from dataclasses import replace
import json
from pathlib import Path
import shutil
import sys
import tempfile
import types
import unittest
from unittest.mock import Mock, patch

from accounting_finance_agent.config import Settings

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import recalculate_evaluation  # noqa: E402


class FakeBackend:
    def __init__(self, folder, result, stage_snapshot):
        self.folder = folder
        self.result = result
        self.stage_snapshot = stage_snapshot
        self.commands = []

    def execute(self, command, timeout):
        self.commands.append((command, timeout))
        self.stage_snapshot({path.relative_to(self.folder).as_posix(): path.read_bytes()
                             for path in self.folder.rglob("*") if path.is_file()})
        if self.result.exit_code == 0:
            final = self.folder / "final"
            final.mkdir()
            shutil.copyfile(self.folder / "staging/working-paper.xlsx", final / "working-paper.xlsx")
        return self.result


class EvaluationRecalculationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.project = self.root / "project"
        self.helper = self.project / "skills/file-delivery-validation/recalculate.py"
        self.helper.parent.mkdir(parents=True)
        self.helper.write_text("# fixed evaluator helper\n")
        self.delivery = self.root / "delivery"
        self.delivery.mkdir()
        self.workbook = self.delivery / "working-paper.xlsx"
        self.workbook.write_bytes(b"original workbook bytes")
        (self.delivery / "recalculation.json").write_text('{"formula_caches":"present"}')
        (self.delivery / "source.csv").write_text("Category,January\nExample,1\n")
        (self.delivery / "notes.json").write_text('{"notes":[]}')
        (self.delivery / "task.txt").write_text("make a workbook")
        (self.delivery / "agent-script.py").write_text("raise RuntimeError('must not run')\n")
        (self.delivery / "agent-helper.py").write_text("print('must not copy')\n")
        (self.delivery / "oracle.json").write_text('{"answer":123}')
        self.destination = self.root / "evaluator-output"
        self.settings = replace(Settings("offline-model", "high", False, "offline"),
                                sandbox_snapshot_id="snapshot-id")
        self.stage = None
        self.result = types.SimpleNamespace(exit_code=0, output="recalculated")
        self.backend = FakeBackend(self.destination, self.result, self._record_stage)
        self.sandbox_kwargs = None
        self.grade = Mock(return_value={"errors": [], "numeric_pass": True})
        self.validator = Mock(return_value={"errors": [], "workbook": "working-paper.xlsx"})
        self.context = self._patches()
        self.context.__enter__()

    def tearDown(self):
        self.context.__exit__(None, None, None)
        self.temp.cleanup()

    def _record_stage(self, stage):
        self.stage = stage

    @contextmanager
    def _backend_scope(self, **kwargs):
        self.sandbox_kwargs = kwargs
        self.backend.folder = self.destination
        yield self.backend

    def _patches(self):
        module = types.SimpleNamespace(grade=self.grade)
        return _PatchGroup(
            patch.object(recalculate_evaluation, "PROJECT_ROOT", self.project),
            patch.object(recalculate_evaluation, "validate_delivery", self.validator),
            patch.object(recalculate_evaluation, "sandbox_backend", side_effect=self._backend_scope),
            patch.dict(sys.modules, {"grade_excel_benchmark": module}),
        )

    def test_stages_only_fixed_helper_and_agent_inputs_without_changing_original(self):
        original_bytes = self.workbook.read_bytes()
        report = recalculate_evaluation.recalculate(self.delivery, self.destination, self.settings)

        self.assertEqual(report["status"], "complete")
        self.assertTrue(report["original_unchanged"])
        self.assertEqual(self.workbook.read_bytes(), original_bytes)
        self.assertEqual(self.stage["staging/working-paper.xlsx"], original_bytes)
        self.assertEqual(self.stage["recalculate.py"], self.helper.read_bytes())
        self.assertEqual(self.stage["source.csv"], (self.delivery / "source.csv").read_bytes())
        self.assertEqual(self.stage["notes.json"], (self.delivery / "notes.json").read_bytes())
        self.assertEqual(self.stage["task.txt"], (self.delivery / "task.txt").read_bytes())
        self.assertNotIn("agent-script.py", self.stage)
        self.assertNotIn("agent-helper.py", self.stage)
        self.assertNotIn("oracle.json", self.stage)
        self.assertEqual(self.backend.commands, [(
            "python3 /workspace/recalculate.py /workspace/staging/working-paper.xlsx /workspace/final", 120
        )])
        self.assertEqual(self.sandbox_kwargs["allowed_hosts"], ())
        self.assertEqual(self.sandbox_kwargs["command_timeout"], 120)
        self.assertEqual(self.sandbox_kwargs["snapshot_id"], "snapshot-id")
        self.assertEqual(self.grade.call_count, 1)
        record = json.loads((self.destination / "evaluator-recalculation.json").read_text())
        self.assertEqual(record["status"], "complete")

    def test_nonzero_sandbox_result_is_recorded_as_failure(self):
        self.backend.result = types.SimpleNamespace(exit_code=17, output="conversion failed")
        report = recalculate_evaluation.recalculate(self.delivery, self.destination, self.settings)

        self.assertEqual(report["status"], "failed")
        self.assertEqual(report["error"]["type"], "RuntimeError")
        self.assertIn("Evaluator recalculation failed", report["error"]["message"])
        self.assertEqual(report["command"]["exit_code"], 17)
        self.assertEqual(self.workbook.read_bytes(), b"original workbook bytes")
        record = json.loads((self.destination / "evaluator-recalculation.json").read_text())
        self.assertEqual(record["status"], "failed")
        self.grade.assert_not_called()

    def test_existing_destination_is_rejected_before_sandbox_execution(self):
        self.destination.mkdir()
        backend = patch.object(recalculate_evaluation, "sandbox_backend")
        with backend as sandbox:
            with self.assertRaisesRegex(ValueError, "fresh evaluator output folder"):
                recalculate_evaluation.recalculate(self.delivery, self.destination, self.settings)
        sandbox.assert_not_called()


class _PatchGroup:
    def __init__(self, *patchers):
        self.patchers = patchers

    def __enter__(self):
        for patcher in self.patchers:
            patcher.__enter__()

    def __exit__(self, exc_type, exc_value, traceback):
        for patcher in reversed(self.patchers):
            patcher.__exit__(exc_type, exc_value, traceback)
