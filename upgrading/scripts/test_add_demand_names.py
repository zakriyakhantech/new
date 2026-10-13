"""Tests for the source-aware super-2.0 demand-name batch builder."""
from __future__ import annotations

import contextlib
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))

import add_demand_names as builder  # noqa: E402


class DemandNameBuilderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest_path = REPO_ROOT / "upgrading/name_batches/demand_2026-10.json"
        cls.template_path = REPO_ROOT / "upgrading/names_upgraded/islamic/aabid.json"
        cls.manifest = json.loads(cls.manifest_path.read_text(encoding="utf-8"))
        cls.template = json.loads(cls.template_path.read_text(encoding="utf-8"))
        cls.records = [
            builder.build_record(candidate, cls.template, cls.manifest["created_at"])
            for candidate in cls.manifest["names"]
        ]

    def test_manifest_contains_exactly_ten_unique_valid_slugs(self) -> None:
        self.assertEqual(builder.validate_manifest(self.manifest), [])
        self.assertEqual(len(self.manifest["names"]), 10)
        slugs = [item["slug"] for item in self.manifest["names"]]
        self.assertEqual(len(set(slugs)), 10)

    def test_records_preserve_super_2_schema_and_template_keys(self) -> None:
        expected_keys = list(self.template["data"])
        for candidate, record in zip(self.manifest["names"], self.records):
            with self.subTest(name=candidate["name"]):
                self.assertEqual(record["schema_version"], "super-2.0")
                self.assertEqual(record["success"], True)
                self.assertEqual(list(record["data"]), expected_keys)
                self.assertEqual(record["data"]["name"], candidate["name"])
                self.assertEqual(record["data"]["slug"], candidate["slug"])
                self.assertEqual(builder.validate_record(record, candidate, self.template), [])

    def test_popularity_keeps_measurements_scoped_and_unaggregated(self) -> None:
        for record in self.records:
            popularity = record["data"]["popularity"]
            self.assertIsNone(popularity["score"])
            self.assertTrue(popularity["render"])
            self.assertTrue(popularity["by_region"])
            for measurement in popularity["by_region"]:
                self.assertTrue(measurement["region"])
                self.assertTrue(measurement["year"])
                self.assertTrue(measurement["source"])
                self.assertTrue(measurement["limitation"])

        sariya = next(r for r in self.records if r["data"]["slug"] == "sariya")
        self.assertEqual(
            [(m["category"], m["rank"], m["relative_interest_percent"]) for m in sariya["data"]["popularity"]["by_region"]],
            [("overall", 27, 50), ("Quranic names", 19, 53)],
        )

    def test_unverified_optional_claims_are_suppressed(self) -> None:
        for record in self.records:
            data = record["data"]
            self.assertFalse(data["numerology"]["render"])
            self.assertFalse(data["lucky_attributes"]["render"])
            self.assertFalse(data["personality_associations"]["render"])
            self.assertFalse(data["spiritual_meaning"]["render"])
            self.assertTrue(data["translation_quality"]["native_review_required"])
            self.assertTrue(data["editorial_validation"]["needs_manual_verification"])

    def test_latin_and_arabic_normalization_catches_real_variants(self) -> None:
        self.assertEqual(builder.normalize_latin("Sāriyā"), "sariya")
        self.assertEqual(builder.normalize_latin("Alp Arslan"), "alparslan")
        self.assertEqual(builder.normalize_script("سَارِيَة"), builder.normalize_script("سارية"))
        self.assertEqual(builder.normalize_script("يُسْرَى"), builder.normalize_script("يسرى"))

    def test_indic_vowel_signs_are_not_stripped(self) -> None:
        # Regression guard: dropping Devanagari matras made unrelated forms collide.
        self.assertNotEqual(builder.normalize_script("युसरा"), builder.normalize_script("यासिर"))
        self.assertNotEqual(builder.normalize_script("दुरु"), builder.normalize_script("दैर"))

    def test_collision_audit_checks_documented_romanized_aliases(self) -> None:
        candidate = next(r for r in self.records if r["data"]["slug"] == "sariya")
        old_record = {
            "schema_version": "super-2.0",
            "success": True,
            "data": {
                "name": "Old entry",
                "slug": "old-entry",
                "identity": {"alternate_spellings": ["Sariyah"]},
            },
        }
        index = builder.build_existing_index([(Path("old-entry.json"), old_record)])
        collisions = builder.check_batch_collisions([candidate], index)
        self.assertTrue(any("Sariyah" in error and "old-entry.json" in error for error in collisions))

    def test_collision_audit_checks_arabic_script_forms_without_vowel_marks(self) -> None:
        candidate = next(r for r in self.records if r["data"]["slug"] == "sariya")
        old_record = {
            "schema_version": "super-2.0",
            "success": True,
            "data": {
                "name": "Old entry",
                "slug": "old-entry",
                "pronunciation": {"scripts": {"arabic": "سارية"}},
            },
        }
        index = builder.build_existing_index([(Path("old-entry.json"), old_record)])
        collisions = builder.check_batch_collisions([candidate], index)
        self.assertTrue(any("old-entry.json" in error for error in collisions))

    def test_write_then_check_is_idempotent_in_a_temporary_dataset(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            dataset = Path(temporary) / "islamic"
            dataset.mkdir()
            shutil.copyfile(self.template_path, dataset / "aabid.json")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                write_result = builder.run(
                    self.manifest_path, dataset, self.template_path, write=True, check=False
                )
                check_result = builder.run(
                    self.manifest_path, dataset, self.template_path, write=False, check=True
                )
            self.assertEqual(write_result, 0, output.getvalue())
            self.assertEqual(check_result, 0, output.getvalue())
            for item in self.manifest["names"]:
                self.assertTrue((dataset / f"{item['slug']}.json").is_file())
            self.assertIn("Wrote 10 records", output.getvalue())
            self.assertIn("OK: 10 records exactly match", output.getvalue())


if __name__ == "__main__":
    unittest.main(verbosity=2)
