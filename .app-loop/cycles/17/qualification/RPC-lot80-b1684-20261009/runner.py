"""Exécute les tests mémoire sans conftest ni import produit."""
import importlib.util
import json
import sys
import unittest
from pathlib import Path

test_path, source_path, output_path = map(Path, sys.argv[1:])
spec = importlib.util.spec_from_file_location("b1684_memoire", test_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module.SOURCE = source_path
suite = unittest.defaultTestLoader.loadTestsFromModule(module)
result = unittest.TextTestRunner(verbosity=2).run(suite)
receipt = {"tests": result.testsRun, "failures": len(result.failures),
           "errors": len(result.errors), "skipped": len(result.skipped),
           "successful": result.wasSuccessful(), "source": str(source_path),
           "test": str(test_path), "fullRuntime": False, "DB": False,
           "Chrome": False, "FULL": False}
with output_path.open("x", encoding="utf-8") as sink:
    json.dump(receipt, sink, ensure_ascii=False, indent=2)
    sink.write("\n")
print(json.dumps(receipt, ensure_ascii=False), flush=True)
sys.exit(0 if result.wasSuccessful() else 1)
