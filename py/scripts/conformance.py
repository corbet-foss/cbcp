"""Shared-vector conformance for the Python port (stdlib only)."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

import cbcp

VECTORS = Path(__file__).resolve().parent.parent.parent / "tests" / "vectors"

FNS = {
    "normalize_locale_id": lambda v: cbcp.normalize_locale_id(v),
    "to_bcp47": lambda v: cbcp.to_bcp47(v),
    "base_language": lambda v: cbcp.base_language(v),
    "is_well_formed": lambda v: cbcp.is_well_formed(v),
    "locale_eq": lambda v: cbcp.locale_eq(v[0], v[1]),
    "deepl_source": lambda v: cbcp.deepl_source(v),
    "deepl_target": lambda v: cbcp.deepl_target(v),
    "google_language": lambda v: cbcp.google_language(v),
}


def load_cases():
    for path in sorted(VECTORS.glob("*.json")):
        for vector in json.loads(path.read_text(encoding="utf-8")):
            yield path.name, vector


class Conformance(unittest.TestCase):
    def test_vectors(self):
        seen = 0
        for path, vector in load_cases():
            with self.subTest(vector=vector["name"], file=path):
                self.assertEqual(
                    FNS[vector["fn"]](vector["input"]),
                    vector["expected"],
                )
                seen += 1
        self.assertGreater(seen, 0, "at least one vector ran")


if __name__ == "__main__":
    unittest.main()
