import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "core_meaning_evidence_audit.py"


class CoreMeaningAuditTests(unittest.TestCase):
    def run_audit(self, root: Path, *extra: str):
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--root", str(root),
             "--json-report", str(root.parent / "report.json"),
             "--csv-report", str(root.parent / "report.csv"), *extra],
            capture_output=True, text=True, check=False,
        )

    def test_recursively_flags_template_and_missing_evidence_without_mutating_record(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "names"
            nested = root / "islamic" / "subgroup"
            nested.mkdir(parents=True)
            record_path = nested / "sample.json"
            original = {
                "schema_version": "super-2.0",
                "data": {
                    "name": "Sample", "slug": "sample",
                    "core_meaning": {
                        "short_meaning": "Unverified",
                        "primary_meaning": "Sample is an Arabic-origin name meaning something beautiful.",
                        "literal_meaning": "Unverified",
                        "meaning_explanation": "The exact meaning is not established.",
                        "meaning_confidence": "HIGH"
                    },
                    "etymology": {"etymology_confidence": "HIGH"},
                    "evidence": {}
                }
            }
            record_path.write_text(json.dumps(original, ensure_ascii=False), encoding="utf-8")
            before = record_path.read_bytes()
            result = self.run_audit(root)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(record_path.read_bytes(), before)
            report = json.loads((base / "report.json").read_text(encoding="utf-8"))
            self.assertEqual(report["summary"]["discovered_json_files"], 1)
            issues = report["records"][0]["issues"]
            self.assertIn("generic_template_primary_meaning", issues)
            self.assertIn("no_evidence_urls_detected", issues)
            self.assertIn("high_meaning_confidence_without_evidence_urls", issues)

    def test_skips_search_index_and_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "names"
            root.mkdir()
            (root / "_search-index.json").write_text("[]", encoding="utf-8")
            (root / "manifest.json").write_text("{}", encoding="utf-8")
            (root / "one.json").write_text(json.dumps({"data": {"name": "One"}}), encoding="utf-8")
            result = self.run_audit(root)
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads((Path(tmp) / "report.json").read_text(encoding="utf-8"))
            self.assertEqual(report["summary"]["discovered_json_files"], 1)

    def test_invalid_json_is_reported_and_returns_two(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "names"
            root.mkdir()
            (root / "broken.json").write_text("{", encoding="utf-8")
            result = self.run_audit(root)
            self.assertEqual(result.returncode, 2, result.stderr)
            report = json.loads((Path(tmp) / "report.json").read_text(encoding="utf-8"))
            self.assertEqual(report["summary"]["invalid_json_files"], 1)

    def test_strict_mode_fails_for_review_flags(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "names"
            root.mkdir()
            (root / "one.json").write_text(json.dumps({"data": {"name": "One"}}), encoding="utf-8")
            result = self.run_audit(root, "--strict")
            self.assertEqual(result.returncode, 1, result.stderr)


if __name__ == "__main__":
    unittest.main()
