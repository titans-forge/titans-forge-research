import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("release_verify", ROOT / "verify.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class PublicationChecks(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "medical"
        shutil.copytree(ROOT, self.root, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))

    def rehash(self):
        path = self.root / "MANIFEST.json"
        manifest = json.loads(path.read_text())
        for name in manifest["files"]:
            manifest["files"][name] = hashlib.sha256((self.root / name).read_bytes()).hexdigest()
        path.write_text(json.dumps(manifest))

    def corrupt_evidence(self, change):
        path = self.root / "evidence.json"
        evidence = json.loads(path.read_text())
        change(evidence)
        path.write_text(json.dumps(evidence))
        self.rehash()

    def test_clean_package(self):
        self.assertEqual(MODULE.verify(self.root)["status"], "passed")

    def test_file_tampering(self):
        with (self.root / "README.md").open("a") as handle:
            handle.write("changed")
        with self.assertRaisesRegex(ValueError, "Hash mismatch"):
            MODULE.verify(self.root)

    def test_unknown_schema(self):
        self.corrupt_evidence(lambda e: e.update(schema="future"))
        with self.assertRaisesRegex(ValueError, "Unknown evidence schema"):
            MODULE.verify(self.root)

    def test_mitoq_cannot_become_pqq(self):
        self.corrupt_evidence(lambda e: next(s for s in e["sources"] if s["id"] == "S01").update(interventions=["pqq"]))
        with self.assertRaisesRegex(ValueError, "correction regressed"):
            MODULE.verify(self.root)

    def test_review_cannot_become_trial(self):
        self.corrupt_evidence(lambda e: next(s for s in e["sources"] if s["id"] == "S07").update(evidence_kind="human_randomized_trial"))
        with self.assertRaisesRegex(ValueError, "correction regressed"):
            MODULE.verify(self.root)

    def test_hydrogen_cannot_be_dropped(self):
        self.corrupt_evidence(lambda e: next(s for s in e["sources"] if s["id"] == "S22").update(interventions=["pqq"]))
        with self.assertRaisesRegex(ValueError, "correction regressed"):
            MODULE.verify(self.root)

    def test_duplicate_doi(self):
        self.corrupt_evidence(lambda e: e["sources"][0].update(doi=e["sources"][1]["doi"]))
        with self.assertRaisesRegex(ValueError, "Duplicate DOI"):
            MODULE.verify(self.root)

    def test_abstracts_not_allowed(self):
        self.corrupt_evidence(lambda e: e["sources"][0].update(abstractText="do not redistribute"))
        with self.assertRaisesRegex(ValueError, "source fields"):
            MODULE.verify(self.root)

    def test_missing_primary_null(self):
        self.corrupt_evidence(lambda e: next(s for s in e["sources"] if s["id"] == "S19").update(finding="Only positive results"))
        with self.assertRaisesRegex(ValueError, "Primary result omitted"):
            MODULE.verify(self.root)

    def test_no_fulltext_review_upgrade(self):
        self.corrupt_evidence(lambda e: e.update(full_text_rubric_review_complete=True))
        with self.assertRaisesRegex(ValueError, "Unsupported upgrade"):
            MODULE.verify(self.root)

    def test_wrong_pubmed_link(self):
        path = self.root / "mitochondrial-combination/mito_combo_landscape.md"
        path.write_text(path.read_text().replace("https://pubmed.ncbi.nlm.nih.gov/37560769/", "https://pubmed.ncbi.nlm.nih.gov/34415830/"))
        self.rehash()
        with self.assertRaisesRegex(ValueError, "wrong source"):
            MODULE.verify(self.root)

    def test_local_path_rejected(self):
        path = self.root / "README.md"
        path.write_text(path.read_text() + "\n/" + "Users/example/private.txt\n")
        self.rehash()
        with self.assertRaisesRegex(ValueError, "Private path"):
            MODULE.verify(self.root)

    def test_broken_relative_link(self):
        path = self.root / "README.md"
        path.write_text(path.read_text() + "\n[missing](missing.md)\n")
        self.rehash()
        with self.assertRaisesRegex(ValueError, "Missing local link"):
            MODULE.verify(self.root)

    def test_unexpected_file_rejected(self):
        (self.root / "private_note.txt").write_text("not permitted")
        with self.assertRaisesRegex(ValueError, "unexpected public files"):
            MODULE.verify(self.root)


if __name__ == "__main__":
    unittest.main()
