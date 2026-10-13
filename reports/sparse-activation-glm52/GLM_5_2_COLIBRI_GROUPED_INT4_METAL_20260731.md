# GLM-5.2 Colibri grouped-int4 Metal systems note, 2026-07-31

This note publishes a conservative release packet for a measured GLM-5.2 Colibri grouped-int4 Metal run on an Apple M5 Max 128 GB machine. The release profile reached a three-run median of `0.91` decode tok/s over 64 generated tokens, `59.33 GB` median observed RSS, `54.2%` expert hit rate, and zero Metal CPU fallbacks.

The headline comparison is `6.46x` end-to-end versus one upstream out-of-box run: the release-profile median decode time was `70.37` seconds and the upstream out-of-box decode time was `454.57` seconds. This is an end-to-end profile comparison, not a pure kernel speedup. The matched controls stay beside the headline: the same-head CPU-only control was `0.69` tok/s and `92.48` seconds, a `1.31x` ratio, and upstream `ecade075` with matched profile settings was `0.67` tok/s and `96.08` seconds, a `1.37x` ratio.

## Source Chain

The exact source chain for the measured release candidate is:

`ecade075 -> 18568e8 -> 208a115 -> de85d2e`

In full commit form, the chain is:

| Step | Commit |
|---|---|
| Upstream base | `ecade075cfc2eae684097ea7de5570c3786ce199` |
| grouped-int4 Metal support | `18568e8084db1fe5efdc8804229c616dfa192450` |
| residual fallback correction | `208a11522d15dc0333b95d132f51cffb1bff3a6a` |
| m5max-128 profile defaults | `de85d2e27006b2c8c3790b91ff597aeb6dc1fff1` |

Grouped-int4 Metal support, elimination of the residual per-layer fallback, and deterministic profile defaults jointly produced this release candidate.

## Release Runs

All three release-profile runs used the `m5max-128` profile with Metal enabled, pipeline enabled, direct I/O enabled, MTP disabled, autopin disabled, cap raise disabled, cap `32`, RAM target `96 GB`, and 8 pipeline workers.

| Run | Prefill seconds | Decode seconds | Decode tok/s | Observed RSS GB | Expert hit rate | Expert bytes fetched GB | Metal CPU fallbacks | Exit code |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 16.05 | 70.58 | 0.91 | 59.35 | 54.2% | 367.236 | 0 | 0 |
| 2 | 15.68 | 69.62 | 0.92 | 59.29 | 54.2% | 367.236 | 0 | 0 |
| 3 | 15.27 | 70.37 | 0.91 | 59.33 | 54.2% | 367.236 | 0 | 0 |

Median release-profile values were `15.68` seconds prefill, `70.37` seconds decode, `0.91` decode tok/s, and `59.33 GB` observed RSS.

## Controls

| Control | Source | n | Decode seconds | Decode tok/s | Ratio from decode time | Notes |
|---|---|---:|---:|---:|---:|---|
| Upstream out-of-box | `ecade075` | 1 | 454.57 | 0.14 | 6.46x | Observed CPU backend, MTP on, no pipeline, no direct I/O, pinned expert budget 47.2 GB, effective cache cap per layer 28. |
| Same-head CPU-only | `de85d2e` | 1 | 92.48 | 0.69 | 1.31x | Same release candidate with Metal disabled. |
| Upstream matched settings | `ecade075` | 1 | 96.08 | 0.67 | 1.37x | Upstream base run with settings matched to the release profile. |

Each control is n=1. The upstream out-of-box auto-configuration depends on available memory and usage history, so the `6.46x` figure should be read as one paired end-to-end profile comparison, not as a universal default-performance multiplier.

## Acceptance Evidence

The grouped-int4 Metal acceptance suite exited with code `0`. The profile resource tests reported 40 passing tests. Representative grouped-int4 max absolute error was `1.19e-06`, and the tail-group max absolute error was `2.09e-07`.

## Boundaries

This packet does not claim SAOD, sub-100-GB checkpoint size, official higher-precision GLM-5.2 quality parity, broad coding qualification, or consumer trillion-parameter feasibility. Observed RSS is a process-memory measurement and does not include the complete on-disk expert bank. The public benchmark JSON is sanitized and excludes local absolute paths, internal workflow IDs, private prompts, and raw terminal metadata.

The benchmark JSON for this note is `results/glm_5_2_colibri_m5max128_benchmark_v1.json`. The deterministic verifier is `verify_glm_5_2_colibri_m5max128_release.py`.
