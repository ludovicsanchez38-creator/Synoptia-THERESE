"""Tests statiques du delta. Aucun import du builder complet ni de G1."""
from __future__ import annotations

import ast
import copy
import difflib
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import unittest

HERE = Path(__file__).resolve().parent
BASE = HERE / "preimages/build_fresh_wrapper-v10.py"
CANDIDATE = HERE / "build_fresh_wrapper.py"
OLD_PROFILE_SHA = "19808ee2cac3169e9fb8c71c24385bcbb97f924c5ed785f4651817ecaa179b0c"
NEW_PROFILE_SHA = "bee3c2e780e58cbc80ed7e37d64115adf08997aab39dae8f11b56050785633a9"


def only_profile_nodes_removed(text):
    tree = ast.parse(text)
    excluded = set()
    for node in tree.body:
        profile_function = isinstance(node, ast.FunctionDef) and node.name == "checked_chrome_successor"
        profile_constant = (isinstance(node, ast.Assign) and len(node.targets) == 1
                            and isinstance(node.targets[0], ast.Name)
                            and node.targets[0].id in {"CHROME_PROFILE", "CHROME_PREIMAGE_PROFILE"})
        if profile_function or profile_constant:
            excluded.update(range(node.lineno, node.end_lineno + 1))
    return "".join(line for number, line in enumerate(text.splitlines(True), 1)
                   if number not in excluded)


def selected_body(text):
    tree = ast.parse(text)
    names = {"need", "regular_bytes", "checked", "checked_chrome_successor"}
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
    if {node.name for node in functions} != names:
        raise ValueError("corps sélectionnés absents")
    constants = {}
    for node in tree.body:
        if (isinstance(node, ast.Assign) and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id in {"CHROME_PROFILE", "CHROME_PREIMAGE_PROFILE", "CHROME_V8_PROFILE"}):
            constants[node.targets[0].id] = ast.literal_eval(node.value)
    namespace = {"Path": Path, "os": os, "stat": stat, "hashlib": hashlib, "re": re, **constants}
    exec(compile(ast.Module(body=functions, type_ignores=[]), "<selected-profile-AST>", "exec"), namespace)
    # Préimage historique synthétique ; le V8 réel épinglé est lu par checked().
    # La chaîne UI/Unix/RootDomain n'est pas exécutée ni qualifiée par ces tests.
    namespace["checked_chrome_v8_successor"] = lambda ref: (
        "synthetic-historical-prefix", namespace["checked"](ref).decode())
    return namespace


class ProfileOnlyBuilderTests(unittest.TestCase):
    def setUp(self):
        self.old = BASE.read_text()
        self.new = CANDIDATE.read_text()
        self.ns = selected_body(self.new)
        self.base_profile = (HERE / "preimages/chrome-v10.sb").read_bytes()
        self.new_profile = (HERE / "profile/chrome.sb").read_bytes()

    def test_original_constructor_full_preimage_exact(self):
        self.assertEqual(hashlib.sha256(BASE.read_bytes()).hexdigest(),
                         "e697ec7733e691681bb104ffee6e083a251f1779abab895e63e316bcfaf72e2f")
        self.assertEqual(BASE.stat().st_size, 80319)

    def test_every_byte_outside_profile_nodes_identical(self):
        self.assertEqual(only_profile_nodes_removed(self.old), only_profile_nodes_removed(self.new))

    def test_no_new_runtime_function_or_helper(self):
        inventory = lambda text: [(type(n).__name__, n.name) for n in ast.parse(text).body
                                  if isinstance(n, (ast.FunctionDef, ast.ClassDef))]
        self.assertEqual(inventory(self.old), inventory(self.new))

    def test_profile_inputs_physical_exact(self):
        self.assertEqual(hashlib.sha256(self.base_profile).hexdigest(), OLD_PROFILE_SHA)
        self.assertEqual(hashlib.sha256(self.new_profile).hexdigest(), NEW_PROFILE_SHA)
        self.assertEqual(len(self.base_profile), 2067)
        self.assertEqual(len(self.new_profile), 2375)
        self.assertTrue(self.new_profile.startswith(self.base_profile))
        self.assertEqual(self.ns["CHROME_PREIMAGE_PROFILE"]["sha256"], OLD_PROFILE_SHA)
        self.assertEqual(self.ns["CHROME_PROFILE"]["sha256"], NEW_PROFILE_SHA)

    def test_real_selected_validator_accepts_exact_suffix(self):
        before, after = self.ns["checked_chrome_successor"](copy.deepcopy(self.ns["CHROME_PROFILE"]))
        self.assertEqual(before, "synthetic-historical-prefix")
        self.assertEqual(after.encode(), self.new_profile)

    def test_wrong_reference_path_refused(self):
        row = copy.deepcopy(self.ns["CHROME_PROFILE"])
        row["path"] += "-other"
        self.refused(row)

    def test_wrong_reference_sha_refused(self):
        row = copy.deepcopy(self.ns["CHROME_PROFILE"])
        row["sha256"] = "0" * 64
        self.refused(row)

    def test_wrong_reference_bytes_refused(self):
        row = copy.deepcopy(self.ns["CHROME_PROFILE"])
        row["bytes"] += 1
        self.refused(row)

    def test_reference_extra_field_refused(self):
        row = copy.deepcopy(self.ns["CHROME_PROFILE"])
        row["approved"] = True
        self.refused(row)

    def test_wrong_base_profile_refused_by_preserved_v9_oracle(self):
        self.byte_mutant(self.base_profile + b"; arbitrary base delta\n", base=True,
                         message="trois lectures littérales")

    def test_missing_new_rule_refused(self):
        self.byte_mutant(self.new_profile.replace(
            b'(allow mach-lookup (global-name "com.apple.CARenderServer"))\n', b""))

    def test_wildcard_iokit_refused(self):
        self.byte_mutant(self.new_profile.replace(b'"AGXDeviceUserClient"', b'"*"'))

    def test_extra_mach_rule_refused(self):
        self.byte_mutant(self.new_profile + b"(allow mach-lookup)\n")

    def test_original_network_rule_change_refused(self):
        self.byte_mutant(self.new_profile.replace(b"localhost:17594", b"localhost:17595"))

    def test_forward_builder_diff_exact(self):
        self.assertEqual((HERE / "diffs/builder-forward.diff").read_text(),
                         self.diff(BASE, CANDIDATE))

    def test_inverse_builder_diff_exact(self):
        self.assertEqual((HERE / "diffs/builder-inverse.diff").read_text(),
                         self.diff(CANDIDATE, BASE))

    def test_profile_forward_and_inverse_diffs_exact(self):
        old = HERE / "preimages/chrome-v10.sb"
        new = HERE / "profile/chrome.sb"
        self.assertEqual((HERE / "diffs/profile-forward.diff").read_text(), self.diff(old, new))
        self.assertEqual((HERE / "diffs/profile-inverse.diff").read_text(), self.diff(new, old))

    def refused(self, row):
        with self.assertRaisesRegex(ValueError, "trois règles nominatives exactes"):
            self.ns["checked_chrome_successor"](row)

    def byte_mutant(self, raw, *, base=False, message="trois règles nominatives exactes"):
        # Double explicite : injecte des octets contradictoires après la vérification
        # de ref pour atteindre le vrai prédicat de delta, sans écrire de fixture.
        checked = self.ns["checked"]
        selected = self.ns["CHROME_PREIMAGE_PROFILE" if base else "CHROME_PROFILE"]
        self.ns["checked"] = lambda ref: raw if ref == selected else checked(ref)
        with self.assertRaisesRegex(ValueError, message):
            self.ns["checked_chrome_successor"](self.ns["CHROME_PROFILE"])

    def diff(self, before, after):
        return "".join(difflib.unified_diff(
            before.read_text().splitlines(True), after.read_text().splitlines(True),
            fromfile=str(before.relative_to(HERE)), tofile=str(after.relative_to(HERE))))


if __name__ == "__main__":
    unittest.main(verbosity=2)
