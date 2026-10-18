"""Tests for the famous historical Companion-kunya batch builder."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))

import add_famous_companion_kunyas_2026_10 as builder  # noqa: E402
import add_quranic_names_2026_10 as core  # noqa: E402


class FamousCompanionKunyaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.template = core.read_json(builder.TEMPLATE)
        cls.records, cls.errors, cls.latin_index, cls.script_index = builder._index_and_validate(cls.template)

    def test_batch_build_does_not_mutate_shared_quranic_builder_metadata(self) -> None:
        self.assertEqual(core.BATCH_ID, "quranic-islamic-2026-10")
        self.assertEqual(core.CREATED_AT, "2026-10-17T00:00:00+00:00")
        self.assertEqual(core.REVIEWED_AT, "2026-10-17")

    def test_batch_contains_ten_collision_free_unique_kunyas(self) -> None:
        self.assertEqual(self.errors, [])
        self.assertEqual(len(builder.DATA), 10)
        self.assertEqual(len({entry["slug"] for entry in builder.DATA}), 10)
        self.assertEqual(len(self.records), 10)

    def test_records_keep_super_2_schema_and_explicit_kunya_type(self) -> None:
        expected_paths = set(core.key_paths(self.template))
        for entry, record in zip(builder.DATA, self.records):
            with self.subTest(name=entry["name"]):
                self.assertEqual(record["schema_version"], "super-2.0")
                self.assertIs(record["success"], True)
                self.assertEqual(set(core.key_paths(record)), expected_paths)
                self.assertEqual(record["data"]["identity"]["name_type"], "historical_kunya")
                self.assertEqual(record["data"]["identity"]["name_status"], "historically_attested_kunya")
                self.assertEqual(core.validate_record(record, self.template, entry), [])

    def test_historical_and_quranic_claims_are_separate(self) -> None:
        for record in self.records:
            data = record["data"]
            with self.subTest(name=data["name"]):
                self.assertFalse(data["religion"]["quranic_status"]["is_quranic"])
                self.assertIn("kunya", data["core_meaning"]["primary_meaning"].lower())
                self.assertIn("does not by itself assert biological parenthood", data["core_meaning"]["primary_meaning"])
                self.assertIn("not independently rechecked", data["evidence"]["verification_method"])
                self.assertIs(data["content_quality"]["tier1_verified"], False)
                self.assertIsNone(data["popularity"]["score"])
                self.assertFalse(data["popularity"]["render"])

    def test_unverified_optional_content_and_translations_are_suppressed(self) -> None:
        for record in self.records:
            data = record["data"]
            with self.subTest(name=data["name"]):
                self.assertFalse(data["numerology"]["render"])
                self.assertFalse(data["lucky_attributes"]["render"])
                self.assertFalse(data["personality_associations"]["render"])
                self.assertFalse(data["spiritual_meaning"]["render"])
                self.assertTrue(data["translation_quality"]["native_review_required"])
                self.assertTrue(data["editorial_validation"]["needs_manual_verification"])

    def test_visible_faq_and_structured_faq_remain_in_parity(self) -> None:
        for record in self.records:
            data = record["data"]
            faq_pages = [node for node in data["structured_data"]["@graph"] if node.get("@type") == "FAQPage"]
            self.assertEqual(len(faq_pages), 1)
            self.assertEqual(len(faq_pages[0]["mainEntity"]), len(data["faq"]))
            self.assertEqual(
                [node["acceptedAnswer"]["text"] for node in faq_pages[0]["mainEntity"]],
                [item["a"] for item in data["faq"]],
            )

    def test_persisted_batch_check(self) -> None:
        manifest = json.loads(builder.MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(manifest["batch_id"], builder.BATCH_ID)
        self.assertEqual(manifest["verification_summary"]["name_type"], "historical_kunya; not automatically a modern given name")
        progress = json.loads(builder.PROGRESS.read_text(encoding="utf-8"))
        self.assertEqual(progress["status"], "complete")
        self.assertEqual(progress["names_added"], 10)
        rows, _ = builder._read_csv()
        by_slug = {row["slug"]: row for row in rows}
        for entry in builder.DATA:
            self.assertEqual(by_slug[entry["slug"]]["status"], builder.STATUS)
            self.assertEqual(by_slug[entry["slug"]]["batch"], builder.BATCH_ID)
            persisted = core.read_json(builder.DATASET / f"{entry['slug']}.json")
            expected = self.records[[item["slug"] for item in builder.DATA].index(entry["slug"])]
            self.assertEqual(persisted, expected)


if __name__ == "__main__":
    unittest.main(verbosity=2)
