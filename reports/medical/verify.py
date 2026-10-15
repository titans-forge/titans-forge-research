"""Offline publication consistency checks, not experimental or clinical validation."""

import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys
from urllib.parse import unquote, urlsplit


EXPECTED_FILES = {
    "README.md", "CORRECTIONS.md", "SOURCES.md", "evidence.json", "verify.py",
    "tests/test_verify.py", "mitochondrial-combination/README.md",
    "mitochondrial-combination/mito_combo_landscape.md",
    "mitochondrial-combination/oxidative_inflammation_resilience.md",
    "mitochondrial-combination/neurocognitive_neurovascular.md",
    "mitochondrial-combination/muscle_fatigue_recovery.md",
    "mitochondrial-combination/renal_vascular_metabolic.md",
    "mitochondrial-combination/safety_interactions_pilot_design.md",
    "sleep-mitophagy/README.md", "sleep-mitophagy/report.md",
}
KINDS = {
    "human_randomized_trial", "narrative_review", "systematic_review_meta_analysis",
    "mixed_human_animal_study", "human_intervention_study", "mechanistic_review",
    "systematic_review", "human_randomized_bioavailability_study", "human_observational_cohort",
    "human_quasi_experimental_study", "human_randomized_acute_biomarker_trial",
    "human_randomized_crossover_biomarker_study", "animal_experiment",
    "mixed_preclinical_human_biomarker_study", "ex_vivo_experiment", "cell_experiment",
    "pooled_selected_intervention_studies",
}
SOURCE_BOUNDARIES = {
    "S01": ("10.1152/ajprenal.00067.2023", "37560769", "human_randomized_trial", ["mitoq"]),
    "S02": ("10.3390/antiox9040341", "32331285", "narrative_review", ["coq10"]),
    "S07": ("10.3390/ijms151120169", "25380523", "narrative_review", ["multiple_mitochondrial_nutrients"]),
    "S08": ("10.3390/ijms26125788", "40565253", "narrative_review", ["coq10"]),
    "S22": ("10.1016/j.jnha.2024.100287", "38908296", "human_randomized_trial", ["hydrogen_producing_minerals", "pqq"]),
    "S26": ("10.1111/jgs.15758", "30724333", "human_quasi_experimental_study", ["cpap_adherence"]),
    "S30": ("10.1002/alz.13847", "38753870", "animal_experiment", ["urolithin_a"]),
    "S33": ("10.14712/fb2016062020053", "27187037", "ex_vivo_experiment", ["coq10", "other_experimental_compounds"]),
    "S34": ("10.1074/jbc.m109.030130", "19861415", "cell_experiment", ["pqq"]),
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def payload_files(root):
    files = set()
    for path in root.rglob("*"):
        require(not path.is_symlink(), "Symlinks are not allowed")
        relative = path.relative_to(root).as_posix()
        if "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        if path.is_file() and relative != "MANIFEST.json":
            files.add(relative)
    return files


def verify(root=None):
    root = Path(root or Path(__file__).parent).resolve()
    manifest = json.loads((root / "MANIFEST.json").read_text())
    require(manifest.get("schema") == "forge_medical_publication_manifest_v1", "Unknown manifest schema")
    require(manifest.get("edition") == "2026-10-15", "Unknown edition")
    require(manifest.get("claim_scope") == "research_only_not_clinical_validation", "Claim scope changed")
    require(set(manifest.get("files", {})) == EXPECTED_FILES, "Manifest file allowlist changed")
    require(payload_files(root) == EXPECTED_FILES, "Missing or unexpected public files")
    for name, digest in manifest["files"].items():
        require(hashlib.sha256((root / name).read_bytes()).hexdigest() == digest, f"Hash mismatch: {name}")

    evidence = json.loads((root / "evidence.json").read_text())
    require(evidence.get("schema") == "forge_medical_publication_evidence_v1", "Unknown evidence schema")
    require(evidence.get("edition") == "2026-10-15", "Evidence edition mismatch")
    require(evidence.get("review_scope") == "bibliographic_record_and_abstract", "Review scope overstated")
    for key in ("systematic_review", "peer_reviewed", "full_text_rubric_review_complete", "direct_four_component_efficacy_established"):
        require(evidence.get(key) is False, f"Unsupported upgrade: {key}")
    sources = evidence["sources"]
    require(len(sources) == 34, "Expected 34 verified bibliographic records")
    ids = {s["id"] for s in sources}
    require(len(ids) == len(sources), "Duplicate source IDs")
    require(len({s["doi"].lower() for s in sources}) == len(sources), "Duplicate DOI aliases")
    indexed = {s["id"]: s for s in sources}
    required_fields = {
        "id", "doi", "pmid", "title", "authors", "publication_date", "journal", "evidence_kind",
        "interventions", "population", "finding", "limitations", "review_scope", "primary_url",
        "doi_url", "retrieval_url", "retrieval_date_utc", "private_raw_record_sha256",
    }
    for source in sources:
        require(set(source) == required_fields, "Unexpected/missing source fields, including restricted full text")
        require(source["evidence_kind"] in KINDS, "Unknown evidence kind")
        require(source["review_scope"] == "bibliographic_record_and_abstract", "Source scope overstated")
        require(bool(re.fullmatch(r"\d+", source["pmid"])), "Invalid PMID")
        require(source["primary_url"] == f'https://pubmed.ncbi.nlm.nih.gov/{source["pmid"]}/', "PMID URL mismatch")
        require(source["doi_url"] == f'https://doi.org/{source["doi"]}', "DOI URL mismatch")
        require(urlsplit(source["retrieval_url"]).hostname == "www.ebi.ac.uk", "Unexpected acquisition host")
        require(bool(re.fullmatch(r"[0-9a-f]{64}", source["private_raw_record_sha256"])), "Missing source provenance hash")
        require(all(source[k] for k in ("title", "finding", "limitations", "interventions")), "Incomplete evidence boundary")
    for sid, expected in SOURCE_BOUNDARIES.items():
        source = indexed[sid]
        require((source["doi"], source["pmid"], source["evidence_kind"], source["interventions"]) == expected,
                f"Critical identity/design correction regressed: {sid}")
    for sid, term in (("S18", "primary"), ("S19", "not significant"), ("S22", "P=.14")):
        require(term in indexed[sid]["finding"], f"Primary result omitted: {sid}")
    unresolved = evidence["unresolved_acquisition_requests"]
    require(len(unresolved) == 4, "Unresolved request disclosure changed")
    require(all(r.get("action") == "not_cited_or_counted_in_this_edition" for r in unresolved), "Unresolved source promoted")

    citations = set()
    for name in sorted(EXPECTED_FILES):
        text = (root / name).read_text()
        require(not any(p in text for p in ("/" + "Users/", "/" + "private/var/", "file" + "://")), f"Private path: {name}")
        require(not re.search(r"(?:github_pat_|gh[pousr]_)[A-Za-z0-9]{20,}|sk-[A-Za-z0-9]{24,}", text), f"Possible credential: {name}")
        if not name.endswith(".md"):
            continue
        for label, target in re.findall(r"\[([^\]]*)\]\(([^)]+)\)", text):
            if re.fullmatch(r"S\d{2}", label):
                require(label in ids, f"Unknown citation: {label}")
                citations.add(label)
                require(target == indexed[label]["primary_url"] or target == "SOURCES.md#" + label.lower(),
                        f"Citation points to wrong source: {name} {label}")
            parsed = urlsplit(target)
            if parsed.scheme:
                require(parsed.scheme == "https" and bool(parsed.hostname), f"Non-HTTPS URL: {name}")
                continue
            require(not parsed.netloc, "Protocol-relative links are not allowed")
            destination = (root / name).parent / unquote(parsed.path) if parsed.path else root / name
            destination = destination.resolve()
            require(root == destination or root in destination.parents, f"Link escapes package: {name}")
            require(destination.is_file(), f"Missing local link: {name} -> {target}")
            if parsed.fragment:
                headings = re.findall(r"^#+ (.+)$", destination.read_text(), re.M)
                anchors = {re.sub(r"[^\w\- ]", "", h.lower()).replace(" ", "-") for h in headings}
                require(unquote(parsed.fragment) in anchors, f"Missing anchor: {target}")
    require(len(citations) >= 25, "Unexpected loss of source-linked report coverage")
    night = (root / "sleep-mitophagy/report.md").read_text()
    require("unvalidated" in night, "Missing score-validation boundary")
    require("production, release, transport" in night, "Missing concentration/flux alternatives")
    require("Not peer reviewed" in night, "Missing publication status")
    return {"status": "passed", "files": len(EXPECTED_FILES), "sources": len(sources),
            "citation_ids_used": len(citations), "scope": "offline_package_consistency_not_scientific_validation"}


if __name__ == "__main__":
    try:
        print(json.dumps(verify(Path(sys.argv[1]) if len(sys.argv) > 1 else None), indent=2))
    except (ValueError, KeyError, TypeError, OSError, json.JSONDecodeError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        sys.exit(1)
