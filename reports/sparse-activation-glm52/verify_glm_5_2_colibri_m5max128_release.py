#!/usr/bin/env python3
"""Deterministic verifier for the public GLM-5.2 Colibri M5 Max packet.

Design rules enforced here:
- Every published figure must be derivable from raw primitives in the JSON
  (per-run timings, token count), re-derived at *publication rounding*, never
  from a full-precision re-derivation that would silently move the gate.
- Median agreement alone is NOT tamper-evident (perturbing the middle of three
  samples leaves the median unchanged), so medians are backed by per-run
  derivational checks and by identity invariants.
- The strongest anti-tamper link is cross-artifact agreement: every cell of the
  systems note's prose tables and headline sentences must equal the JSON value.
"""

from __future__ import annotations

import json
import math
import statistics
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
BENCHMARK_PATH = BASE_DIR / "results" / "glm_5_2_colibri_m5max128_benchmark_v1.json"
NOTE_PATH = BASE_DIR / "GLM_5_2_COLIBRI_GROUPED_INT4_METAL_20260731.md"

EXPECTED_CHAIN_ABBREV = ["ecade075", "18568e8", "208a115", "de85d2e"]
EXPECTED_CHAIN_FULL = [
    "ecade075cfc2eae684097ea7de5570c3786ce199",
    "18568e8084db1fe5efdc8804229c616dfa192450",
    "208a11522d15dc0333b95d132f51cffb1bff3a6a",
    "de85d2e27006b2c8c3790b91ff597aeb6dc1fff1",
]
EXPECTED_STEP_LABELS = [
    "Upstream base",
    "grouped-int4 Metal support",
    "residual fallback correction",
    "m5max-128 profile defaults",
]
FORBIDDEN_PUBLIC_STRINGS = [
    "/Users/",
    "FMC_",
    "WFAPPR_",
    "Sovereign_Mesh",
    "task_outputs",
    "dev_worktrees",
    "rollback_dir",
    "source_worktree",
]


CHECK_COUNT = 0

# Control key -> (label used in the note's controls table, chain index of its commit)
CONTROL_NOTE_ROWS = {
    "upstream_out_of_box": ("Upstream out-of-box", 0),
    "same_head_cpu_only": ("Same-head CPU-only", 3),
    "upstream_matched_settings": ("Upstream matched settings", 0),
}

# Control key -> the token the JSON's n=1 limitation must use to name it.
# Note: the JSON says "upstream matched-settings" (hyphenated), which differs
# from the note's table label "Upstream matched settings".
CONTROL_CAVEAT_TOKENS = {
    "upstream_out_of_box": "out-of-box",
    "same_head_cpu_only": "same-head CPU-only",
    "upstream_matched_settings": "matched-settings",
}

# Any limitation that loses every cue reads as a positive claim, not a caveat.
CAVEAT_CUES = ("n=1", "depends on", "no ", "not ", "never", "without")

# Published claim boundary -> (terms that must all appear, cues any of which must).
# The term+cue pair must select exactly one limitation sentence.
CAVEAT_BOUNDARIES = [
    ("n=1 sample size for all three controls", ("n=1", "sample size"), ("n=1",)),
    ("auto-config depends on memory and usage history", ("auto-configuration", "depends on"), ("depends on",)),
    ("no quality-parity claim vs official checkpoint", ("quality parity",), ("no claim", "not")),
    ("RSS excludes the on-disk expert bank", ("expert bank",), ("does not include",)),
    ("no SAOD / broad coding / trillion-parameter feasibility claim", ("SAOD", "feasibility"), ("claim is made",)),
]

# Caveat terms whose presence in the systems note was confirmed by inspection.
# "sample size" is confirmed ABSENT from the note and is deliberately not listed.
CONFIRMED_CAVEAT_NOTE_TERMS = (
    "n=1", "feasibility", "auto-config", "trillion", "expert bank",
    "quality parity", "SAOD",
)


def require(condition: bool, message: str) -> None:
    global CHECK_COUNT
    if not condition:
        raise AssertionError(message)
    CHECK_COUNT += 1


def rounded_ratio(control_decode_seconds: float, profile_decode_seconds: float) -> float:
    return round(control_decode_seconds / profile_decode_seconds, 2)


def published(value) -> str:
    """Render a JSON number exactly as the systems note publishes it."""
    return str(value)


def enabled_label(flag: bool) -> str:
    return "enabled" if flag else "disabled"


def table_rows_after(note: str, header_marker: str, columns: int, artifact: str) -> list[list[str]]:
    """Data rows of the first markdown table whose header line contains the marker."""
    lines = note.splitlines()
    for index, line in enumerate(lines):
        if line.startswith("|") and header_marker in line:
            rows: list[list[str]] = []
            for raw in lines[index + 2:]:
                if not raw.startswith("|"):
                    break
                cells = [cell.strip() for cell in raw.strip().strip("|").split("|")]
                require(len(cells) == columns, f"{artifact} table row has {len(cells)} cells, expected {columns}")
                rows.append(cells)
            require(rows, f"{artifact} table after header '{header_marker}' has no data rows")
            return rows
    raise AssertionError(f"{artifact} table with header '{header_marker}' is missing")


def main() -> None:
    data = json.loads(BENCHMARK_PATH.read_text(encoding="utf-8"))
    note = NOTE_PATH.read_text(encoding="utf-8")
    public_text = json.dumps(data, sort_keys=True) + note

    for forbidden in FORBIDDEN_PUBLIC_STRINGS:
        require(forbidden not in public_text, f"forbidden public string present: {forbidden}")

    require(data["schema"] == "public_glm52_colibri_m5max128_benchmark_v1", "unexpected schema")
    require(data["source"]["chain_abbrev"] == EXPECTED_CHAIN_ABBREV, "unexpected abbreviated source chain")
    require(data["source"]["chain_full"] == EXPECTED_CHAIN_FULL, "unexpected full source chain")

    generation = data["generation"]
    require(generation["generated_tokens"] == 64, "generated token count changed")
    generated_tokens = generation["generated_tokens"]
    require(generation["temperature"] == 0, "release runs must be greedy (temperature 0)")

    hardware = data["hardware"]
    require(
        f"{hardware['machine_class']} {hardware['marketing_memory_class_gb']} GB machine" in note,
        "systems note hardware claim does not match the JSON hardware primitives",
    )

    release = data["release_profile"]
    runs = release["runs"]
    require(len(runs) == 3, "release profile must contain exactly three runs")
    require(release["aggregate"]["sample_size"] == 3, "release aggregate sample size must be three")
    require([run["run"] for run in runs] == [1, 2, 3], "release run numbering must be 1, 2, 3")
    require(all(run["exit_code"] == 0 for run in runs), "all release runs must pass")
    require(all(run["metal_cpu_fallbacks"] == 0 for run in runs), "all release runs must have zero Metal CPU fallbacks")

    # Per-run derivational checks: a median can hide a tampered sample, so each
    # sample is re-derived at the rounding the packet publishes (2 dp tok/s).
    for run in runs:
        label = f"release run {run['run']}"
        require(run["decode_seconds"] > 0 and run["prefill_seconds"] > 0, f"{label} timings must be positive")
        require(run["rss_gb"] > 0, f"{label} observed RSS must be positive")
        require(0.0 <= run["expert_hit_rate_percent"] <= 100.0, f"{label} expert hit rate out of range")
        derived_tps = round(generated_tokens / run["decode_seconds"], 2)
        require(
            derived_tps == run["decode_tokens_per_second"],
            f"{label} decode tok/s is not derivable from {generated_tokens} generated tokens / decode seconds",
        )

    # Identity invariant: the workload is greedy and deterministic, so the
    # expert bytes fetched must be byte-identical across the three runs.
    fetched_values = {run["expert_bytes_fetched_gb"] for run in runs}
    require(len(fetched_values) == 1, "expert bytes fetched must be identical across deterministic release runs")

    median_prefill = statistics.median(run["prefill_seconds"] for run in runs)
    median_decode = statistics.median(run["decode_seconds"] for run in runs)
    median_tps = statistics.median(run["decode_tokens_per_second"] for run in runs)
    median_rss = statistics.median(run["rss_gb"] for run in runs)
    median_hit_rate = statistics.median(run["expert_hit_rate_percent"] for run in runs)
    aggregate = release["aggregate"]
    stored_tps = [run["decode_tokens_per_second"] for run in runs]
    require(math.isclose(median_prefill, aggregate["median_prefill_seconds"], abs_tol=0.005), "median prefill seconds mismatch")
    require(math.isclose(median_decode, aggregate["median_decode_seconds"], abs_tol=0.005), "median decode seconds mismatch")
    require(math.isclose(median_tps, aggregate["median_decode_tokens_per_second"], abs_tol=0.005), "median tok/s mismatch")
    require(math.isclose(median_rss, aggregate["median_rss_gb"], abs_tol=0.005), "median RSS mismatch")
    require(math.isclose(median_hit_rate, aggregate["median_expert_hit_rate_percent"], abs_tol=0.005), "median hit rate mismatch")
    require(
        aggregate["decode_tokens_per_second_range"] == [min(stored_tps), max(stored_tps)],
        "decode tok/s range does not match the per-run values",
    )
    require(aggregate["all_runs_zero_cpu_fallbacks"] is True, "aggregate fallback flag must be true")

    # ---------------------------------------------------------------- controls
    # Controls are n=1: they carry no median to hide behind, so each one is
    # re-derived from its own decode time and its ratio is re-derived against
    # the published profile median.
    controls = data["controls"]
    published_median_decode = aggregate["median_decode_seconds"]
    require(set(controls) == set(CONTROL_NOTE_ROWS), "unexpected control set")
    for key, (note_label, chain_index) in CONTROL_NOTE_ROWS.items():
        control = controls[key]
        require(control["sample_size"] == 1, f"{key} must be published as n=1")
        require(control["exit_code"] == 0, f"{key} must have exit code 0")
        require(control["decode_seconds"] > 0, f"{key} decode seconds must be positive")
        derived_tps = round(generated_tokens / control["decode_seconds"], 2)
        require(
            derived_tps == control["decode_tokens_per_second"],
            f"{key} decode tok/s is not derivable from {generated_tokens} generated tokens / decode seconds",
        )
        derived_ratio = rounded_ratio(control["decode_seconds"], published_median_decode)
        require(
            derived_ratio == control["profile_to_control_speedup_from_decode_time"],
            f"{key} ratio is not derivable from its decode seconds and the published profile median",
        )
        expected_commit = EXPECTED_CHAIN_FULL[chain_index]
        require(control["source_commit"] == expected_commit, f"{key} source commit is not in the declared chain")
        require(
            control["decode_tokens_per_second"] < aggregate["median_decode_tokens_per_second"],
            f"{key} must be slower than the release profile for the published ratio to exceed 1",
        )

    same_head = controls["same_head_cpu_only"]
    require(
        same_head["configuration_difference"] == "COLI_METAL=0",
        "same-head control must be the Metal-disabled difference",
    )
    require(
        same_head["rss_gb"] == round(same_head["rss_gb"], 2) and abs(same_head["rss_gb"] - median_rss) < 1.0,
        "same-head control RSS should track the release profile RSS (Metal toggle is not a memory change)",
    )
    matched = controls["upstream_matched_settings"]
    require(matched["settings_matched_to_release_profile"] is True, "matched-settings control flag must be true")

    out_of_box = controls["upstream_out_of_box"]
    observed = out_of_box["runtime_settings_observed"]
    release_settings = release["settings"]
    require(observed["backend"] == "CPU", "out-of-box control observed a non-CPU backend")
    require(observed["pipeline"] is False and release_settings["pipeline"] is True, "out-of-box pipeline contrast broken")
    require(observed["direct_io"] is False and release_settings["direct_io"] is True, "out-of-box direct I/O contrast broken")
    require(observed["mtp"] is True and release_settings["mtp"] is False, "out-of-box MTP contrast broken")
    require(
        out_of_box["rss_gb"] > median_rss,
        "out-of-box control RSS should exceed the release profile (pinned expert budget, not process cache)",
    )

    # ------------------------------------------------- JSON-internal narrative
    interpretation = data["interpretation"]
    for key, field in (
        ("upstream_out_of_box", "primary_speedup"),
        ("upstream_matched_settings", "matched_source_speedup"),
        ("same_head_cpu_only", "same_head_metal_speedup"),
    ):
        ratio = controls[key]["profile_to_control_speedup_from_decode_time"]
        require(
            interpretation[field].startswith(f"{published(ratio)}x"),
            f"interpretation.{field} does not lead with the derived ratio for {key}",
        )
    require(
        len(interpretation["release_candidate_factors"]) == 3,
        "release candidate factors must stay the three declared contributors",
    )

    # ---------------------------------------------------------------- caveats
    # The limitation sentences are NOT verbatim in the systems note, so the
    # caveat checks below are deliberately JSON-internal structural checks: a
    # caveat quietly deleted or softened into a positive claim fires even while
    # the prose still reads fine. Note-side linkage is required only for terms
    # whose presence in the note was confirmed by inspection; "sample size" is
    # confirmed ABSENT from the note and must not be required from it.
    limitations = interpretation["limitations"]
    require(
        isinstance(limitations, list) and len(limitations) == len(CAVEAT_BOUNDARIES),
        f"limitations must hold exactly the {len(CAVEAT_BOUNDARIES)} published claim boundaries",
    )
    require(
        all(isinstance(item, str) and item.strip() for item in limitations),
        "every limitation must be a non-empty string",
    )
    require(
        len(set(limitations)) == len(limitations),
        "limitations must be distinct; duplicated text usually means a boundary was dropped",
    )
    # Each published limitation must hedge: quantify, deny, or scope. A bare
    # positive claim masquerading as a limitation is the failure mode here.
    for item in limitations:
        require(
            any(cue in item.lower() for cue in CAVEAT_CUES),
            f"limitation lost its hedge and now reads as a claim: {item!r}",
        )

    # Boundary 1: the three controls are single-sample, and must be named.
    sample_size_caveat = next((item for item in limitations if "n=1" in item), None)
    require(sample_size_caveat is not None, "limitations lost the n=1 sample-size caveat")
    require(
        "sample size" in sample_size_caveat,
        "the n=1 caveat must state that it is about sample size",
    )
    require(
        sum("n=1" in item for item in limitations) == 1,
        "exactly one limitation may carry the n=1 sample-size caveat",
    )
    for key in controls:
        require(
            CONTROL_CAVEAT_TOKENS[key] in sample_size_caveat,
            f"the n=1 caveat no longer names the {key} control it covers",
        )
    require(
        all(control["sample_size"] == 1 for control in controls.values()),
        "the n=1 caveat only holds while every control is published as n=1",
    )

    # Boundaries 2-5: each must survive as a denial/scope, not a claim.
    for boundary, required_terms, cues in CAVEAT_BOUNDARIES:
        matched = [
            item
            for item in limitations
            if all(term in item for term in required_terms)
            and any(cue in item.lower() for cue in cues)
        ]
        require(
            len(matched) == 1,
            f"claim boundary {boundary!r} is not stated exactly once as a caveat "
            f"(found {len(matched)} matching limitations)",
        )

    for term in CONFIRMED_CAVEAT_NOTE_TERMS:
        require(term in note, f"systems note lost the caveat term the JSON relies on: {term!r}")

    # ------------------------------------------------ cross-artifact linkage
    # Every published cell of the note must equal the JSON value it restates.
    # These are built from JSON values, so tampering with a number forces a
    # matching prose edit or this check fires.
    abbrev = data["source"]["chain_abbrev"]
    require(f"`{' -> '.join(abbrev)}`" in note, "systems note source chain does not match the JSON chain")

    chain_rows = table_rows_after(note, "| Step | Commit |", 2, "systems note")
    require([row[0] for row in chain_rows] == EXPECTED_STEP_LABELS, "systems note chain step labels mismatch")
    require(
        [row[1].strip("`") for row in chain_rows] == EXPECTED_CHAIN_FULL,
        "systems note chain commits do not match the JSON full chain",
    )

    run_rows = table_rows_after(note, "| Run | Prefill seconds |", 9, "systems note")
    require(len(run_rows) == len(runs), "systems note release table row count mismatch")
    for run, row in zip(runs, run_rows):
        label = f"systems note release row {run['run']}"
        expected_cells = [
            published(run["run"]),
            published(run["prefill_seconds"]),
            published(run["decode_seconds"]),
            published(run["decode_tokens_per_second"]),
            published(run["rss_gb"]),
            f"{published(run['expert_hit_rate_percent'])}%",
            published(run["expert_bytes_fetched_gb"]),
            published(run["metal_cpu_fallbacks"]),
            published(run["exit_code"]),
        ]
        require(row == expected_cells, f"{label} cells {row} do not match the JSON run {expected_cells}")

    settings_sentence = (
        f"Metal {enabled_label(release_settings['metal'])}, "
        f"pipeline {enabled_label(release_settings['pipeline'])}, "
        f"direct I/O {enabled_label(release_settings['direct_io'])}, "
        f"MTP {enabled_label(release_settings['mtp'])}, "
        f"autopin {enabled_label(release_settings['autopin'])}, "
        f"cap raise {enabled_label(release_settings['cap_raise'])}, "
        f"cap `{published(release_settings['cap'])}`, "
        f"RAM target `{published(release_settings['ram_gb'])} GB`, and "
        f"{published(release_settings['pipeline_workers'])} pipeline workers"
    )
    require(settings_sentence in note, f"systems note profile settings sentence does not restate the JSON settings: {settings_sentence}")

    headline_sentence = (
        f"three-run median of `{published(aggregate['median_decode_tokens_per_second'])}` decode tok/s over "
        f"{published(generated_tokens)} generated tokens, "
        f"`{published(aggregate['median_rss_gb'])} GB` median observed RSS, "
        f"`{published(aggregate['median_expert_hit_rate_percent'])}%` expert hit rate, and "
        "zero Metal CPU fallbacks"
    )
    require(headline_sentence in note, f"systems note headline sentence does not match the JSON aggregate: {headline_sentence}")

    oob = controls["upstream_out_of_box"]
    headline_ratio = (
        f"`{published(oob['profile_to_control_speedup_from_decode_time'])}x` end-to-end versus one upstream "
        f"out-of-box run: the release-profile median decode time was `{published(published_median_decode)}` seconds "
        f"and the upstream out-of-box decode time was `{published(oob['decode_seconds'])}` seconds"
    )
    require(headline_ratio in note, f"systems note headline ratio sentence is not derivable: {headline_ratio}")

    median_sentence = (
        f"`{published(aggregate['median_prefill_seconds'])}` seconds prefill, "
        f"`{published(aggregate['median_decode_seconds'])}` seconds decode, "
        f"`{published(aggregate['median_decode_tokens_per_second'])}` decode tok/s, and "
        f"`{published(aggregate['median_rss_gb'])} GB` observed RSS"
    )
    require(median_sentence in note, f"systems note median sentence does not match the JSON aggregate: {median_sentence}")

    control_rows = table_rows_after(note, "| Control | Source |", 7, "systems note")
    require(len(control_rows) == len(CONTROL_NOTE_ROWS), "systems note controls table row count mismatch")
    for (key, (note_label, chain_index)), row in zip(CONTROL_NOTE_ROWS.items(), control_rows):
        control = controls[key]
        label = f"systems note control row {key}"
        expected_cells = [
            note_label,
            f"`{abbrev[chain_index]}`",
            published(control["sample_size"]),
            published(control["decode_seconds"]),
            published(control["decode_tokens_per_second"]),
            f"{published(control['profile_to_control_speedup_from_decode_time'])}x",
        ]
        require(row[:6] == expected_cells, f"{label} cells {row[:6]} do not match the JSON control {expected_cells}")

    oob_note_cell = control_rows[0][6]
    require(
        f"pinned expert budget {published(observed['pinned_expert_gb'])} GB" in oob_note_cell,
        "systems note out-of-box pinned budget does not match the JSON observation",
    )
    require(
        f"effective cache cap per layer {published(observed['effective_cache_cap_per_layer'])}" in oob_note_cell,
        "systems note out-of-box cache cap does not match the JSON observation",
    )
    require(
        f"{observed['backend']} backend" in oob_note_cell and f"MTP {'on' if observed['mtp'] else 'off'}" in oob_note_cell,
        "systems note out-of-box backend/MTP wording does not match the JSON observation",
    )

    # --------------------------------------------------- printed-precision gate
    # Gates compare printed values at printed precision: anything re-derived
    # must reproduce the *rounded* published number, never a full-precision
    # value that silently moves the gate. Each figure below must also render
    # exactly as the systems note prints it, so a float whose str() form ever
    # drifts from the published text is caught here.
    for value, description in (
        (aggregate["median_decode_tokens_per_second"], "median decode tok/s"),
        (aggregate["median_prefill_seconds"], "median prefill seconds"),
        (aggregate["median_decode_seconds"], "median decode seconds"),
        (aggregate["median_rss_gb"], "median RSS GB"),
        (aggregate["median_expert_hit_rate_percent"], "median expert hit rate percent"),
        (runs[0]["expert_bytes_fetched_gb"], "expert bytes fetched GB"),
        (release_settings["cap"], "profile cap"),
        (release_settings["ram_gb"], "profile RAM target GB"),
        (release_settings["pipeline_workers"], "profile pipeline workers"),
        (oob["profile_to_control_speedup_from_decode_time"], "out-of-box ratio"),
        (controls["same_head_cpu_only"]["profile_to_control_speedup_from_decode_time"], "same-head ratio"),
        (
            controls["upstream_matched_settings"]["profile_to_control_speedup_from_decode_time"],
            "matched-settings ratio",
        ),
    ):
        require(
            published(value) in note,
            f"{description} does not render as published in the systems note: {published(value)!r}",
        )

    acceptance = data["acceptance"]
    require(
        f"acceptance suite exited with code `{published(acceptance['grouped_int4_metal_acceptance_exit_code'])}`" in note,
        "systems note acceptance exit code does not match the JSON",
    )
    require(
        f"resource tests reported {published(acceptance['profile_resource_tests_passed'])} passing tests" in note,
        "systems note resource test count does not match the JSON",
    )
    require(
        f"`{acceptance['grouped_int4_representative_max_abs_error']:.2e}`" in note,
        "systems note representative grouped-int4 error does not match the JSON",
    )
    require(
        f"`{acceptance['grouped_int4_tail_group_max_abs_error']:.2e}`" in note,
        "systems note tail-group grouped-int4 error does not match the JSON",
    )

    boundary_terms = ["SAOD", "quality parity", "expert bank", "sanitized"]
    for term in boundary_terms:
        require(term in note, f"systems note boundary language dropped: {term}")

    print(
        "OK: GLM-5.2 Colibri m5max-128 packet verified "
        f"({CHECK_COUNT} checks, {len(runs)} release runs, {len(controls)} controls, "
        f"median {published(aggregate['median_decode_tokens_per_second'])} decode tok/s, "
        f"headline {published(oob['profile_to_control_speedup_from_decode_time'])}x)."
    )


if __name__ == "__main__":
    main()
