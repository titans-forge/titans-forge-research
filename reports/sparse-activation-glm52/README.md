# Consumer Trillion-Parameter MoE Research

Publication preparation: October 13, 2026. This edition preserves July 2026
evidence; it is not a fresh benchmark or the latest runtime qualification.
See [publication scope](PUBLICATION_SCOPE.md) for exclusions and later-work status.

This package investigates whether very large sparse Mixture-of-Experts models can run interactively on consumer Apple Silicon without keeping the complete expert tree resident.

## Current Judgment

The work does not establish consumer trillion-parameter feasibility. It now
establishes five narrower findings:

1. Cross-layer router selections contain a strong causal signal that generalizes across complete held-out prompt groups.
2. Queue-constrained replay shows that this signal can reduce modeled exposed stall.
3. Static top-k transfer admission cannot meet the joint recall, stall, and read-amplification gates. The primary research lane is now calibrated, deadline-aware transfer admission.
4. On GLM-5.2 layer 8, a downstream suffix-sensitivity teacher generalized
   across a prompt-disjoint external set with AUC `0.949/0.981`, zero observed
   false negatives, and 50% coverage. A fixed cheap PCA-24 student fell from
   sealed AUC `0.926` to external AUC `0.818` and failed the external safety
   gate.
5. A measured GLM-5.2 Colibri grouped-int4 Metal release profile on an Apple
   M5 Max 128 GB machine reached a three-run median of `0.91` decode tok/s over
   64 generated tokens with `59.33 GB` median observed RSS, `54.2%` expert hit
   rate, and zero Metal CPU fallbacks.

The strongest conservative replay point used two admitted candidates at depth 2 and a 16-expert cache. It reduced modeled exposed stall by 5.63 seconds relative to equal-budget popularity with 1.04% read amplification, but achieved only a 3.45 percentage-point recall advantage. Increasing admission to four candidates crossed the aggregate recall gate but raised amplification to 11.56%.

The July 31 systems result is an end-to-end profile comparison, not a pure kernel speedup claim: the release-profile median decode time was 70.37 seconds versus one upstream out-of-box run at 454.57 seconds, a recomputed `6.46x` ratio. The same-head CPU-only control was `1.31x`, and the upstream matched-profile control was `1.37x`; all controls were n=1.

## Contents

- [GLM-5.2 Colibri grouped-int4 Metal systems note](GLM_5_2_COLIBRI_GROUPED_INT4_METAL_20260731.md)
- [GLM-5.2 Colibri M5 Max 128 GB benchmark JSON](results/glm_5_2_colibri_m5max128_benchmark_v1.json)
- [GLM-5.2 Colibri release verifier](verify_glm_5_2_colibri_m5max128_release.py)
- [GLM-5.2 expert-approximation safety note](GLM_5_2_EXPERT_APPROXIMATION_SAFETY_NOTE_20260729.md)
- [GLM Streaming Safety Challenge V1](GLM_STREAMING_SAFETY_CHALLENGE_V1.md)
- [GLM-5.2 aggregate evidence receipt](results/glm_5_2_suffix_risk_external_validation_v1.json)
- [Research report, Markdown](CONSUMER_TRILLION_MOE_RESEARCH_REPORT_V1.md)
- [Admission sweep aggregate](results/router_native_prefetch_admission_sweep_v1.json)
- [Conditional/popularity blend sweep aggregate](results/router_native_prefetch_blend_sweep_v1.json)

## Reproducibility Boundary

The published JSON files contain aggregate replay results, configuration, source-trace hashes, output filenames, artifact hashes, and sanitized GLM-5.2 Colibri benchmark observations. They intentionally exclude raw prompts, token IDs, activations, expert weights, model caches, absolute local paths, internal workflow identifiers, private prompts, raw terminal metadata, and internal execution logs.

The July 29 replay evidence is Qwen3.5-122B-A10B proxy evidence, not GLM-5.2 or trillion-parameter target-model validation. Replay estimates serialized transfer and exposed stall from recorded router offsets; it is not a measurement of target-runtime asynchronous I/O or end-to-end tokens per second.

The July 31 GLM-5.2 Colibri systems note is measured target-runtime evidence for one hardware/profile setting. It does not establish official higher-precision GLM quality parity, broad coding qualification, SAOD, or consumer trillion-parameter feasibility. Observed RSS is a process-memory measurement and is not a claim that the complete on-disk expert bank was resident.

## Artifact Hashes

| Artifact | SHA-256 |
|---|---|
| `figures/glm_suffix_risk_generalization_gap_v1.svg` | `36de30f598d8d3578b02720f271bc908b15ba63d7960d16d63a34b06461fb3fb` |
| `results/glm_5_2_suffix_risk_external_validation_v1.json` | See `PUBLICATION_SHA256.json`; this edition removes two internal approval identifiers. |
| `results/router_native_prefetch_admission_sweep_v1.json` | `d931f38309d23df6a959dedad6f9d004b16c66ca8c10d29ca888f3c75751fca8` |
| `results/router_native_prefetch_blend_sweep_v1.json` | `bdd3f90ab76661b1b2aa5d077e5fce3e1349551faf780bc53a16440103893220` |

## Next Falsifier

For the safety lane, expand teacher-labeled training data, freeze a third prompt
pack, and test runtime-cheap nonlinear students without using causal outcomes
for fitting. Require prompt-disjoint external AUC of at least `0.90`,
false-negative rate no greater than `5%`, and coverage of at least `20%`.

For the streaming lane, train probability calibration only on non-evaluation
prompt groups. Score each transfer by expected avoided demand stall minus
transfer, queueing, and cache-displacement costs. Only then proceed to measured
asynchronous target-runtime throughput.

For the GLM-5.2 Colibri systems lane, repeat the controls, add cold-start and longer-decode profiles, and keep quality evaluation separate from systems throughput until an external task suite is frozen.
