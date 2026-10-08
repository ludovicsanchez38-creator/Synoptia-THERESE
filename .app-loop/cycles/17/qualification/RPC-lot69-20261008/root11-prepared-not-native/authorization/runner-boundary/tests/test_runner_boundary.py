"""Tests purs : vrais corps wrapper/blueprint, transport et fichiers en mémoire.

Aucun pytest/Vitest métier, G1, Popen, Node, DNS, service ou profil n'est lancé.
Les XML et retours sont des doubles déclarés, pas des observations natives.
"""
from __future__ import annotations

import contextlib
import copy
import hashlib
import io
import json
from pathlib import Path
import socket
import subprocess
import sys
import types
import unittest
from unittest import mock
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / "source"))
import runner_boundary as patcher

CONTRACT = Path("/private/tmp/therese-c17-rpc-integration-UctqC8UG/coordinator/rpc_instrument_contract.py")
ROOT = Path("/private/tmp/therese-c17-wrapper-canary-pure0123456789")


def load_text_module(name: str, text: str, filename: str) -> types.ModuleType:
    module = types.ModuleType(name)
    module.__file__ = filename
    exec(compile(text, filename, "exec"), module.__dict__)
    return module


def forbidden(*args, **kwargs):
    raise AssertionError("OS/process/socket interdit dans les doubles purs")


class RunnerBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.runner_pre = (HERE / "preimages/calibrate-test-runner.py").read_text()
        cls.blueprint_pre = (HERE / "preimages/wrapper_blueprint.py").read_text()
        cls.runner_text = (HERE / "source/calibrate-test-runner.py").read_text()
        cls.blueprint_text = (HERE / "source/wrapper_blueprint.py").read_text()
        cls.contract = load_text_module("rpc_instrument_contract", CONTRACT.read_text(), str(CONTRACT))
        with mock.patch.dict(sys.modules, {"rpc_instrument_contract": cls.contract}):
            cls.blueprint = load_text_module("candidate_blueprint", cls.blueprint_text,
                                            str(HERE / "source/wrapper_blueprint.py"))
        cls.environments = cls.blueprint.web_environment(ROOT,
            data_dir=cls.blueprint.paths(ROOT)["test_data"])

    def setUp(self) -> None:
        self.memory: dict[str, str] = {}
        self.calls: list[dict] = []
        self.saved: dict = {}
        self.codes = None
        self.bad_counts = False
        memory = self.memory

        class MemoryPath(type(Path())):
            def write_text(self, data, encoding=None):
                memory[str(self)] = data
                return len(data)

            def resolve(self, strict=False):
                return self

            def exists(self):
                return str(self) in memory

            @contextlib.contextmanager
            def open(self, mode="r", encoding=None):
                if mode != "x":
                    raise AssertionError("Seule la log exclusive est attendue")
                if str(self) in memory:
                    raise FileExistsError(str(self))
                stream = io.StringIO()
                yield stream
                memory[str(self)] = stream.getvalue()

        self.MemoryPath = MemoryPath
        self.out = MemoryPath(self.contract.expected_allocations(ROOT)["test-runner"])

    def rows(self) -> list[dict]:
        reference = lambda p: {"path": str(p), "sha256": "a" * 64, "bytes": 10}
        jobs = ("rpc-all-runtime_ui-visual_capture-network_capture", "rpc-screen-negative",
                "rpc-screen-positive-visual", "rpc-screen-positive-network", "rpc-screen-restored")
        metadata = self.blueprint.auxiliary_metadata(ROOT,
            git_ref=reference(ROOT / "authorization/git-snapshot.json"),
            chrome_context_refs={job: reference(ROOT / "auxiliary" / job / "context.json") for job in jobs})
        envelopes = {name: reference(ROOT / "session-rpc/envelope" / (name + ".json"))
                     for name in self.contract.REQUESTERS}
        return self.blueprint.descriptors(ROOT, {"context_id": "b" * 32}, envelopes,
            metadata_by_job=metadata, source_refs=[reference(ROOT / "source/rpc_protocol.py")])

    def execute_wrapper(self, text=None) -> int:
        common = types.ModuleType("common")
        common.FRONT = self.MemoryPath(self.blueprint.FRONT)
        common.PYTHON = self.MemoryPath(self.blueprint.QA_PYTHON)
        common.REPO = self.MemoryPath(self.blueprint.QA_SOURCE)
        common.environment = lambda data: dict(self.environments)
        common.head = lambda: self.blueprint.HEAD
        common.manifest = lambda: {"temporary_root": str(self.blueprint.paths(ROOT)["profile"])}
        common.new_run = forbidden
        common.sha = lambda p: hashlib.sha256(self.memory[str(p)].encode()).hexdigest()
        common.save = lambda path, data: self.saved.update(data)
        nested = types.ModuleType("nested_capture")
        def reserve(label):
            self.assertEqual(label, "test-runner")
            return self.out
        nested.reserved_path = reserve
        def capture(command, **kwargs):
            label = kwargs["label"]
            index = len(self.calls)
            self.calls.append({"argv": command, **kwargs})
            defect = label.endswith("positive")
            code = (1 if defect else 0) if self.codes is None else self.codes[index]
            failed = 1 if defect else 0
            if self.bad_counts and index == 0:
                failed = 0
            xml = str(self.out / (label.removeprefix("test-") + ".xml"))
            self.memory[xml] = f'<testsuite tests="1" failures="{failed}" errors="0" skipped="0"/>'
            return subprocess.CompletedProcess(command, code, "stdout fixture\n", "stderr fixture\n")
        nested.capture_nested = capture
        original_parse = ET.parse
        def parse(source, *args, **kwargs):
            return original_parse(io.StringIO(self.memory[str(source)]))
        with mock.patch.dict(sys.modules, {"common": common, "nested_capture": nested}), \
             mock.patch.object(ET, "parse", side_effect=parse), \
             mock.patch.object(subprocess, "Popen", side_effect=forbidden), \
             mock.patch.object(subprocess, "run", side_effect=forbidden), \
             mock.patch.object(subprocess, "check_output", side_effect=forbidden), \
             mock.patch.object(socket, "socket", side_effect=forbidden), \
             contextlib.redirect_stdout(io.StringIO()):
            module = load_text_module("fixture_wrapper", text or self.runner_text,
                                      str(HERE / "source/calibrate-test-runner.py"))
            module.Path = self.MemoryPath
            with self.assertRaises(SystemExit) as ended:
                module.main()
        return ended.exception.code

    def test_pinned_derivations_equal_supplied_sources(self):
        self.assertEqual(patcher.derive_runner(self.runner_pre), self.runner_text)
        self.assertEqual(patcher.derive_blueprint(self.blueprint_pre), self.blueprint_text)

    def test_restoring_three_anchors_is_byte_exact(self):
        back = self.runner_text.replace(patcher.ROOTDIR_AFTER, patcher.ROOTDIR_BEFORE).replace(
            patcher.HOST_AFTER, patcher.HOST_BEFORE)
        self.assertEqual(back, self.runner_pre)
        self.assertEqual(self.blueprint_text.replace(patcher.BLUEPRINT_AFTER, patcher.BLUEPRINT_BEFORE),
                         self.blueprint_pre)

    def test_runner_changed_preimage_is_refused(self):
        with self.assertRaisesRegex(ValueError, "Préimage runner SHA"):
            patcher.derive_runner(self.runner_pre + "\n")

    def test_blueprint_changed_preimage_is_refused(self):
        with self.assertRaisesRegex(ValueError, "Préimage blueprint SHA"):
            patcher.derive_blueprint(self.blueprint_pre.replace("timeout_seconds", "other"))

    def test_double_application_is_refused(self):
        with self.assertRaises(ValueError):
            patcher.derive_runner(self.runner_text)
        with self.assertRaises(ValueError):
            patcher.derive_blueprint(self.blueprint_text)

    def test_real_wrapper_four_calls_match_blueprint_exactly(self):
        self.assertEqual(self.execute_wrapper(), 0)
        rows = {r["label"]: r for r in self.rows()}
        self.assertEqual(len(self.calls), 4)
        for call in self.calls:
            row = rows[call["label"]]
            self.assertEqual(call["argv"], row["argv"])
            self.assertEqual(str(call["cwd"]), row["cwd"])
            self.assertEqual(call["env"], row["environment"])
            self.assertEqual(call["timeout"], row["timeout_seconds"])
            self.assertEqual(str(call["stdout_path"]), row["stdout_path"])
            self.assertEqual(str(call["stderr_path"]), row["stderr_path"])

    def test_pytest_has_one_exact_rootdir_for_each_variant(self):
        self.execute_wrapper()
        for call in self.calls[:2]:
            options = [arg for arg in call["argv"] if arg.startswith("--rootdir=")]
            self.assertEqual(options, ["--rootdir=" + str(self.out)])
            self.assertEqual(call["cwd"], self.blueprint.QA_SOURCE)

    def test_vitest_generated_host_is_numeric_and_options_preserved(self):
        self.execute_wrapper()
        config = self.memory[str(self.out / "vitest.runtime.config.mjs")]
        self.assertIn('server: {host: "127.0.0.1"}', config)
        self.assertIn('globals: true, environment: "node", include: ["calibrationC17.test.ts"], cache: false', config)
        self.assertNotIn("localhost", config)

    def test_old_wrapper_reproduces_missing_rootdir_and_host_in_pure_double(self):
        self.execute_wrapper(self.runner_pre)
        self.assertFalse(any(arg.startswith("--rootdir=") for arg in self.calls[0]["argv"]))
        self.assertNotIn("server:", self.memory[str(self.out / "vitest.runtime.config.mjs")])

    def test_old_blueprint_does_not_equal_new_pytest_request(self):
        with mock.patch.dict(sys.modules, {"rpc_instrument_contract": self.contract}):
            old = load_text_module("old_blueprint", self.blueprint_pre, "preimage")
        previous = self.blueprint
        try:
            self.blueprint = old
            row = next(r for r in self.rows() if r["label"] == "test-pytest-positive")
        finally:
            self.blueprint = previous
        self.execute_wrapper()
        self.assertNotEqual(row["argv"], self.calls[0]["argv"])

    def test_codes_one_zero_and_xml_oracles_remain_exact(self):
        self.assertEqual(self.execute_wrapper(), 0)
        self.assertEqual([v["exit_code"] for v in self.saved["controls"].values()], [1, 0, 1, 0])
        for name, value in self.saved["controls"].items():
            self.assertEqual(value["counts"], {"tests": 1, "failures": int(name.endswith("positive")),
                                               "errors": 0, "skipped": 0})

    def test_native_failure_codes_are_not_reclassified_as_causal_pass(self):
        self.codes = [4, 4, 1, 1]
        self.assertEqual(self.execute_wrapper(), 1)
        self.assertEqual(self.saved["status"], "failed")
        self.assertFalse(self.saved["controls"]["pytest-positive"]["pass"])
        self.assertFalse(self.saved["controls"]["vitest-negative"]["pass"])

    def test_wrong_xml_failure_count_remains_red(self):
        self.bad_counts = True
        self.assertEqual(self.execute_wrapper(), 1)
        self.assertFalse(self.saved["controls"]["pytest-positive"]["pass"])

    def test_no_non_test_descriptor_or_env_bound_changes(self):
        with mock.patch.dict(sys.modules, {"rpc_instrument_contract": self.contract}):
            old = load_text_module("old_blueprint", self.blueprint_pre, "preimage")
        current = self.rows()
        previous = self.blueprint
        try:
            self.blueprint = old
            historical = self.rows()
        finally:
            self.blueprint = previous
        self.assertEqual(len(current), 15)
        for before, after in zip(historical, current, strict=True):
            if before["label"].startswith("test-pytest-"):
                self.assertEqual([arg for arg in after["argv"] if not arg.startswith("--rootdir=")], before["argv"])
                without = dict(after, argv=before["argv"])
                self.assertEqual(without, before)
            else:
                self.assertEqual(after, before)

    def overlay(self):
        path = str(ROOT / "auxiliary-ports/runtime/calibrate-test-runner.py")
        payloads = {path: self.runner_pre.encode()}
        for index in range(25):
            payloads[str(ROOT / "auxiliary-ports" / ("fixture-" + str(index)))] = b"fixture\n"
        outputs = {p: patcher.planned_ref(p, raw) for p, raw in payloads.items()}
        scripts = {"runtime/calibrate-test-runner.py": outputs[path]}
        scripts.update({"fixture-" + str(i): outputs[str(ROOT / "auxiliary-ports" / ("fixture-" + str(i)))] for i in range(16)})
        return {"schema": "c17-wrapper-auxiliary-additive-plan-v1", "scope": "WRAPPER_CANARY",
                "root": str(ROOT), "emitted": False, "admission": False, "OS_qualified": False,
                "payloads": payloads, "outputs": outputs, "script_outputs": scripts,
                "base_manifest_ref": {"fixture": "immutable11"}}

    def test_overlay_updates_only_runner_payload_and_both_refs(self):
        original = self.overlay()
        baseline = copy.deepcopy(original)
        result = patcher.derive_overlay(original)
        path = str(ROOT / "auxiliary-ports/runtime/calibrate-test-runner.py")
        self.assertEqual(original, baseline)
        self.assertEqual(result["payloads"][path], self.runner_text.encode())
        self.assertEqual(result["outputs"][path], patcher.planned_ref(path, self.runner_text.encode()))
        self.assertEqual(result["script_outputs"]["runtime/calibrate-test-runner.py"], result["outputs"][path])
        restored = copy.deepcopy(result)
        for key in ("payloads", "outputs"):
            restored[key][path] = original[key][path]
        restored["script_outputs"]["runtime/calibrate-test-runner.py"] = original["script_outputs"]["runtime/calibrate-test-runner.py"]
        self.assertEqual(restored, original)

    def test_overlay_stale_ref_is_refused(self):
        plan = self.overlay()
        path = str(ROOT / "auxiliary-ports/runtime/calibrate-test-runner.py")
        plan["outputs"][path]["sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "préalable divergent"):
            patcher.derive_overlay(plan)

    def test_overlay_emitted_or_admitted_is_refused(self):
        for key in ("emitted", "admission", "OS_qualified"):
            plan = self.overlay()
            plan[key] = True
            with self.subTest(key=key), self.assertRaises(ValueError):
                patcher.derive_overlay(plan)


if __name__ == "__main__":
    unittest.main(verbosity=2)
