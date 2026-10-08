"""Cas préparés, non exécutés par l'auteur de la composition."""
from __future__ import annotations

import ast
from hashlib import sha256
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class CompositionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Seul le module pur préparé est évalué lors d'un futur GO de test.
        cls.namespace = {}
        source = (ROOT / "render_git_listener.py").read_text()
        cls.code = ast.parse(source)
        exec(compile(cls.code, "renderer-pur-prepare", "exec"), cls.namespace)

    def setUp(self):
        self.definitions = {
            name: (ROOT / "preimages" / "definitions" / name).read_text()
            for name in self.namespace["SOURCES"]
        }
        self.helper = (ROOT / "preimages" / "aux_node-git.mjs").read_text()
        self.context = self.definitions["complements/instruments/contexte-v3.mjs"]

    @staticmethod
    def ref(text):
        return {"sha256": sha256(text.encode()).hexdigest(), "bytes": len(text.encode())}

    def render(self, **overrides):
        arguments = dict(
            definitions=self.definitions,
            source_refs={name: self.ref(value) for name, value in self.definitions.items()},
            helper_source=self.helper, helper_ref=self.ref(self.helper),
            context_source=self.context, context_ref=self.ref(self.context),
        )
        arguments.update(overrides)
        return self.namespace["render"](**arguments)

    def refused(self, **overrides):
        with self.assertRaises(self.namespace["Refused"]):
            self.render(**overrides)

    def test_three_exact_listener_fixtures_and_nine_git_texts_unchanged(self):
        output = self.render()
        self.assertEqual(set(output), set(self.definitions))
        for name in self.namespace["CHANGED_PATHS"]:
            self.assertEqual(output[name], (ROOT / "expected-definition-only" / name).read_text())
        for name in set(output) - self.namespace["CHANGED_PATHS"]:
            self.assertEqual(output[name], self.definitions[name])

    def test_git_context_and_helper_are_preserved(self):
        output = self.render()
        self.assertEqual(output["complements/instruments/contexte-v3.mjs"], self.context)
        self.assertEqual(self.ref(self.helper)["sha256"], self.namespace["HELPER_SHA"])

    def test_old_helper_is_refused_even_with_its_true_pin(self):
        old = (ROOT / "preimages" / "aux_node-before-git.mjs").read_text()
        self.refused(helper_source=old, helper_ref=self.ref(old))

    def test_rehashed_changed_git_helper_is_refused(self):
        changed = self.helper + "\n// autre definition\n"
        self.refused(helper_source=changed, helper_ref=self.ref(changed))

    def test_rehashed_changed_recipe_is_refused(self):
        self.definitions["runtime/recette-c17.mjs"] += "\n"
        self.refused()

    def test_missing_or_extra_definition_is_refused(self):
        changed = dict(self.definitions)
        changed.pop("runtime/recette-crm-focus.mjs")
        self.refused(definitions=changed)
        changed = dict(self.definitions, unknown="")
        self.refused(definitions=changed)

    def test_context_before_git_is_refused(self):
        old = (ROOT / "preimages" / "contexte-before-git.mjs").read_text()
        self.refused(context_source=old, context_ref=self.ref(old))

    def test_divergent_representation_of_context_is_refused(self):
        changed = self.context + "\n"
        self.refused(context_source=changed, context_ref=self.ref(changed))

    def test_wrong_sha_bytes_or_extra_reference_field_is_refused(self):
        for reference in (
            {"sha256": "0" * 64, "bytes": len(self.helper.encode())},
            {"sha256": self.namespace["HELPER_SHA"], "bytes": len(self.helper.encode()) + 1},
            dict(self.ref(self.helper), approved=True),
        ):
            self.refused(helper_ref=reference)

    def test_fourteen_site_table_remains_definition_only_and_closed(self):
        table = ast.parse((ROOT / "preimages" / "ab_auxiliary_table.py").read_text())
        values = {}
        for node in table.body:
            if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                if node.targets[0].id in ("RPC_JOBS", "DIRECT_SITES"):
                    values[node.targets[0].id] = ast.literal_eval(node.value)
        self.assertEqual(len(values["RPC_JOBS"]), 5)
        self.assertEqual(len(values["DIRECT_SITES"]), 9)
        self.assertEqual(len(set(values["RPC_JOBS"]) | {name for name, _ in values["DIRECT_SITES"]}), 14)
        self.assertIs(self.namespace["RUNTIME_ENABLED"], False)
        self.assertIs(self.namespace["OS_STARTUP_QUALIFIED"], False)
        self.assertEqual(self.namespace["ADMISSIONS"], {})
        self.assertEqual(self.namespace["CAPABILITIES"], {})


if __name__ == "__main__":
    unittest.main()
