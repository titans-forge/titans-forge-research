# Consumer Trillion-Parameter MoE Research Report

- Date: 2026-07-22
- Status: final for the current mechanism-screening phase
- Proxy model: Qwen3.5-122B-A10B MLX mixed 3/6-bit (`Q`)
- Target question: can a very large sparse MoE be made interactive on consumer Apple Silicon without keeping its complete expert tree resident?

## Executive Judgment

The research rejects the simplest versions of the consumer-trillion-model thesis but preserves a narrower, technically plausible path.

1. **Caching and static allocation alone are insufficient.** Semantic prompt coherence did not produce robust expert locality, calibration-only cache allocation was worse than uniform LRU, and within-stream route-history predictors did not materially beat a static popularity control.
2. **Architecture-native cross-layer prediction is the first strong deployable signal.** A layer-pair conditional map trained with complete prompt-group holdouts improved equal-budget expert recall by 12.16-19.13 percentage points over target-layer popularity and won all 24 held-out prompt groups at every tested depth from 1 to 32 layers.
3. **Prompt-conditioned activation structure is real but incomplete.** Session-adaptive bases consistently improved MoE inputs and prefix-seen expert outputs, yet regressed every prefix-unseen cohort and retained absolute output errors near 0.97.
4. **A plain global expert-axis dictionary is also insufficient.** Rank 64 beat random controls in every seed/layer comparison but still produced 0.834 mean held-out relative L2 and approximately 1.006 p95 expert error.
5. **The leading systems mechanism is now exact-model streaming with deadline-aware architecture-native prefetch.** Queue-constrained replay confirmed that cross-layer predictions can reduce modeled exposed stall, but static top-k admission cannot simultaneously meet the recall and read-amplification gates. The bottleneck has moved from route prediction to transfer admission and scheduling. Hybrid expert compression remains a secondary lane pending a model-native fidelity reference.

There is no current evidence that a 744B or trillion-parameter model can be compressed below 100 GB at acceptable quality by the claimed SAOD method. The exact SAOD implementation remains unpublished and independently unverified. Science Forge has established useful necessary conditions, eliminated weak mechanism families, and exercised the first direct functional instrument. The strict replay gate failed, so no deployed-model fidelity claim is made from that instrument.

## Question Decomposition

The project separated four questions that are often conflated:

1. **Capacity:** can the representation fit in local memory?
2. **Scheduling:** can required expert bytes arrive before their deadlines?
3. **Fidelity:** can compact expert representations preserve held-out expert transformations?
4. **System performance:** after dense weights, KV cache, construction, transfer, dequantization, and compute are counted, is end-to-end decoding interactive?

No capacity or I/O result is treated as a quality or throughput result.

## Capacity Boundary

For public GLM-5.2 dimensions, the projection-surrogate screen estimated the following 4-bit all-expert coefficient storage with 16-bit layer-shared bases:

| Equal rank | Projected experts | Shared bases | Combined |
|---:|---:|---:|---:|
| 64 | 3.516 GiB | 0.110 GiB | 3.625 GiB |
| 128 | 7.031 GiB | 0.220 GiB | 7.251 GiB |
| 256 | 14.063 GiB | 0.439 GiB | 14.502 GiB |
| 512 | 28.125 GiB | 0.879 GiB | 29.004 GiB |

This establishes arithmetic capacity only. If separate 16-bit bases are required per expert, rank 256 reaches 126.563 GiB before the dense core, KV cache, and runtime. Basis scope and precision are load-bearing.

The modeled 4-bit routed-expert tree is 337.5 GiB. At the measured 6.675 GB/s cold-read rate, a perfect sequential construction pass has a lower bound of 54.3 seconds. Random access, projection compute, dequantization, and contention increase that time.

## Routing And Paging Findings

### Prefill semantic-locality control

Four equal 256-token conditions were captured across all 48 routed layers. At cache capacity 64 experts per layer, semantic warm-hit rate was 80.431% versus 84.905% for a matched token permutation. At capacity 128, semantic hit rate was 93.492% versus 94.588% for the control. Coding reduced misses by 24.454% relative to the domain-interleaved condition, below the predeclared 30% gate.

**Decision:** semantic coherence alone does not justify prompt-conditioned expert seeding.

### Equal-byte cache allocation

At a 14.496 GB cache budget:

| Policy | Expert bytes/token |
|---|---:|
| Uniform per-layer LRU | 397,957,632 |
| Calibration frequency static | 459,576,576 |
| Calibration miss-byte weighted | 453,418,752 |
| Nondeployable equal-budget oracle | 222,628,608 |

Weighted allocation was 13.94% worse than uniform LRU on aggregate and worse on all four workloads. The oracle was 44.06% better than uniform.

**Decision:** stop calibration-only layer allocation as the primary mechanism; avoidable I/O exists, but this allocator cannot find it.

### Decode-time causal prefetch

The cache-correct three-prompt smoke replay used leave-one-prompt-out fitting, a nonpreemptive earliest-deadline-first transfer queue, and measured 6.675 GB/s bandwidth. At capacity 64 and five tokens per second:

| Policy | Needed-miss recall | Precision | Residual bytes | Total bytes |
|---|---:|---:|---:|---:|
| No-prefetch LRU | 0.00% | 0.00% | 21.537 GB | 21.537 GB |
| Cross-prompt popularity | 17.14% | 82.30% | 17.847 GB | 22.331 GB |
| Best layer-signature map (`d2`) | 18.73% | 82.37% | 17.504 GB | 22.401 GB |
| Bandwidth-constrained oracle | 90.49% | 100.00% | 2.047 GB | 21.537 GB |

The best deployable map improved recall by only 1.59 percentage points over popularity and increased total reads 4.01% over no-prefetch. Its per-prompt recall ranged from 15.10% to 21.63%. The constrained oracle retained 63.07% recall at ten tokens per second.

**Decision:** do not promote route-history prediction. Retain the oracle result as evidence that better causal signals or architecture-level locality could exploit physical headroom.

### Architecture-native cross-layer lookahead

A subsequent stratified screen tested a different signal family: selected routes at layer `k` predict routes at layer `k+d` in the same decode call. The map was trained on 23 prompt groups and evaluated on the completely held-out twenty-fourth group, repeated for all 24 folds. Conditional and target-layer-popularity policies received the same eight-expert prediction budget.

| Lookahead | Median router lead | Popularity recall | Conditional recall | Delta | Held-out groups with >=5 pp gain |
|---:|---:|---:|---:|---:|---:|
| 1 layer | not retained in the depth artifact | 27.83% | 46.96% | +19.13 pp | 24/24 |
| 2 layers | 1.16 ms | 27.90% | 46.02% | +18.12 pp | 24/24 |
| 4 layers | 2.33 ms | 27.76% | 44.95% | +17.18 pp | 24/24 |
| 8 layers | 4.66 ms | 27.61% | 43.26% | +15.64 pp | 24/24 |
| 16 layers | 9.31 ms | 29.16% | 41.90% | +12.74 pp | 24/24 |
| 24 layers | 13.98 ms | 29.04% | 41.20% | +12.16 pp | 24/24 |
| 32 layers | 18.64 ms | 27.92% | 40.82% | +12.90 pp | 24/24 |

Same-ID carry-forward was strongly negative; the useful signal comes from learned layer-pair relationships, not shared identity semantics across layers. The predictive advantage remains material at 16-32 layers, where the Q proxy exposes approximately 9-19 ms of router-offset lead.

**Decision:** promote architecture-native layer-pair prediction to the primary research lane. This is a predictor result, not yet an end-to-end throughput result. The next gate is measured exposed stall under cache, request-setup, random-read, bandwidth, and dequantization constraints.

### Queue-constrained architecture-native replay

The promoted causal replay instrument then applied separate conditional and popularity caches, one nonpreemptive transfer link, recorded layer offsets, measured 6.675 GB/s cold-read bandwidth, 4,718,592 bytes per expert, complete prompt-group holdouts, and no future-route access. The full 24-prompt, 576-call, 48-layer trace was replayed at depths 1, 2, 4, 8, 16, 24, and 32 with a 64-expert cache and up to eight admitted loads.

| Lookahead | Conditional recall | Popularity recall | Modeled stall saved | Read amplification | Decision |
|---:|---:|---:|---:|---:|---|
| 1 | 0.08% | 0.05% | 1.60 s | 123.87% | fail closed |
| 2 | 7.99% | 3.93% | 1.50 s | 117.09% | fail closed |
| 4 | 7.90% | 3.93% | 1.23 s | 114.71% | fail closed |
| 8 | 7.55% | 3.90% | 1.14 s | 107.74% | fail closed |
| 16 | 6.70% | 3.80% | 1.10 s | 91.04% | fail closed |
| 24 | 6.68% | 3.76% | 0.83 s | 94.93% | fail closed |
| 32 | 7.21% | 3.72% | 0.55 s | 111.92% | fail closed |

The low D1 completed-by-deadline recall is physically consistent: one layer supplies insufficient time for most 4.72 MB expert transfers. D2 provides the best tested balance of route value and lead time, but admitting eight candidates spends too many bytes.

A 27-cell admission sweep varied lookahead 2/8/16, cache capacity 16/32/64 experts per layer, and one/two/four admitted candidates. The strongest conservative point was D2, capacity 16, two admitted candidates: conditional replay saved 5.63 seconds of modeled exposed stall over equal-budget popularity with 1.04% read amplification, but its recall advantage was only 3.45 percentage points. At the same depth and capacity, four admissions crossed the aggregate recall gate at +5.43 points and saved 3.42 seconds, but amplification rose to 11.56%.

An 11-cell blend sweep tested the missing three-admission point and conditional/popularity weights from 0.5/0.5 through 1.0/0.0. The best sub-5% amplification blend, three admissions at 0.7 conditional weight, saved 4.56 seconds with 4.27% amplification but achieved only +3.73 recall points and passed the per-prompt five-point threshold on 0/24 groups. The nearest aggregate-recall result, four admissions at 0.85 conditional weight, reached +4.99 points on 14/24 groups while incurring 10.41% amplification. No configuration passed all preregistered gates.

**Decision:** retain cross-layer prediction, reject static top-k loading as the complete scheduler, and make deadline-aware transfer admission the primary research lane. A candidate should be admitted only when its calibrated probability, cache state, transfer completion deadline, expected avoided demand stall, and displacement cost imply positive expected value. This remains proxy replay evidence, not measured target-model throughput.

## Representation Findings

### Prompt-only activation bases

Eight prompt groups, three layers, 64 prefix and continuation rows per layer/session, ranks 8/16/32/64, and eight matched-control seeds produced 768 paired cells per cohort.

| Cohort | Adaptive wins | Mean adaptive error | Mean matched error | Delta |
|---|---:|---:|---:|---:|
| All expert outputs | 480/768 | 0.96916 | 0.97074 | -0.00158 |
| Prefix-seen outputs | 607/768 | 0.94803 | 0.95914 | -0.01111 |
| Prefix-unseen outputs | 207/768 | 0.98319 | 0.97858 | +0.00461 |
| MoE inputs | 580/768 | 0.74183 | 0.75447 | -0.01264 |

All eight resampling seeds favored adaptive input bases; all eight favored adaptive seen-expert outputs; zero favored adaptive unseen-expert outputs. Unseen experts regressed for every prompt group. Absolute output fidelity remained unsuitable for replacement.

**Decision:** prompt conditioning contains useful session signal but cannot be the full representation.

### Global expert-axis dictionary

The weight-space screen preserved 256/256 identities, used disjoint calibration/evaluation rows, and tested four seeds on layers 0, 23, and 47.

| Layer | Rank-64 learned L2 | p95 expert L2 | Random L2 | Learned wins |
|---:|---:|---:|---:|---:|
| 0 | 0.8063 | 1.0197 | 0.8658 | 4/4 |
| 23 | 0.8471 | 1.0007 | 0.8664 | 4/4 |
| 47 | 0.8493 | 0.9979 | 0.8661 | 4/4 |
| Aggregate | 0.8342 | 1.0061 | 0.8661 | 12/12 |

Rank-256 identity controls reconstructed at numerical precision. The rank-64 basis found non-random shared structure but not enough individual expert fidelity.

**Decision:** reject a plain global expert-axis dictionary as a standalone reconstruction. It may remain useful as a coarse prior or residual component.

## Leading Architecture

The primary design is now **exact-model streaming with deadline-aware architecture-native causal prefetch**:

1. Fit layer-pair conditional maps using disjoint prompt groups and fixed prediction budgets.
2. Combine conditional scores with target-layer popularity and current cache residency.
3. Add small hidden-state or full-router-logit probes only if they improve prompt-held-out prediction.
4. Score every candidate by expected avoided stall minus transfer, queueing, and cache-displacement cost; admit only positive-value transfers that can complete before demand.
5. Promote only on reduced exposed stall and improved end-to-end decode throughput, not recall alone.
6. Retain exact expert weights as the authoritative model; use session-adaptive compression only as a separately gated secondary mechanism.

This priority reflects the current evidence: cross-layer routing structure is strong and causal, physical oracle headroom exists, and the tested compression mechanisms remain far from functional fidelity.

## Functional Instrument Result

The governed functional stack now includes:

- a model-independent SwiGLU projection evaluator with session, static, wrong-prompt, and random controls;
- an in-memory cache-correct Q activation observer;
- a selected-expert MLX bridge that slices packed weights, scales, and biases before dequantization;
- a lease-governed one-prompt Q runner that publishes only after cleanup and release.

The first real layer-0 run loaded and captured Q, reached the selected-expert bridge, then failed closed during conversion of an already-selected MLX `bfloat16` value to NumPy. It used 18.55 seconds wall time, 44.06 GB maximum RSS, and 62.07 GB peak footprint. The runtime lease released and no partial result was published.

The bounded device-side `float32` conversion repair passed 18 tests in both verifier and MLX environments and independent verification. Human promotion committed repair `be897053de2db72028a26a821f682c2217cfe247` in its isolated worktree. Internal workflow identifiers are omitted from this publication edition.

The repaired strict rerun completed model loading, cache-correct capture, selected packed-weight slicing, dequantization, and host conversion. It then failed closed because unprojected host replay exceeded the predeclared `0.001` relative-L2 tolerance against Q's captured expert output. Wall time was 18.62 seconds, maximum RSS was 35.96 GB, peak memory footprint was 62.38 GB, the runtime lease released, and no success artifact was published.

Post-audit controls localized that discrepancy. Source review confirmed that the observer captures each unweighted expert output before router-score reduction, that the host evaluator uses the same `silu(gate) * up -> down` operation order as MLX, and that selected expert slices are dequantized before host conversion. A direct one-row comparison between MLX `gather_qmm` and the selected-slice host replay measured `0.01408` relative L2 with `0.999905` cosine. Repeating the comparison on the cache-correct prompt capture measured `0.02207` relative L2 with `0.999757` cosine, `0.01978` median row error, and `0.03980` p95 row error across four selected continuation rows.

The discrepancy is therefore high-cosine numerical execution drift between the quantized MLX kernel and the host-dequantized evaluator, not a roughly `0.92` semantic replay failure. Router weighting, gate/up reversal, and expert-slot misalignment are not supported by the controls. The `0.001` gate remains unchanged and the projection result remains non-promotable. The next reference must compare the unprojected and projected candidates through one model-native execution path before any runtime-fidelity tolerance is calibrated.

A separate permissive diagnostic run was used only to expose the rank curve; it does not convert the failed reference check into a pass. It captured 64 prefix rows, 64 continuation rows, and four held-out rows for the most frequent continuation identity.

| Rank | Relative L2 | P50 row L2 | P95 row L2 | Cosine |
|---:|---:|---:|---:|---:|
| 8 | 0.9504 | 0.8932 | 0.9691 | 0.3112 |
| 16 | 0.9235 | 0.8283 | 0.9520 | 0.3835 |
| 32 | 0.9281 | 0.8285 | 0.9575 | 0.3725 |
| 64 | 0.9226 | 0.8186 | 0.9524 | 0.3858 |

These values are far beyond the predeclared rank-64 p95 stop threshold of `0.25`, but they are not accepted deployed-model fidelity measurements because the strict unprojected reference replay failed. They support a conservative stop decision, not a quantitative quality claim.

## Gate Outcomes

1. **Reference replay:** fail. Unprojected host replay measured relative L2 `0.02207` against captured Q output, above the unchanged `0.001` gate, while retaining cosine `0.999757`.
2. **Lifecycle and redaction:** pass. Both reruns released the lease; the strict run published no success artifact; the diagnostic artifact contains aggregate receipts only.
3. **Finite, non-neutral rank curve:** observed in the diagnostic run, but not promoted to validated fidelity evidence.
4. **Rank-64 stop threshold:** negative indication. Diagnostic p95 row relative L2 was `0.9524`, versus the `0.25` threshold.
5. **Expansion decision:** stop. Do not run the eight-prompt, three-layer pure internal-direction tournament.
6. **Cross-layer predictor:** pass as a research signal. Conditional mapping beat equal-budget popularity by at least five points on all 24 held-out prompt groups at every tested depth.
7. **Queue-constrained predictor promotion:** fail closed. Static admission reduced modeled exposed stall at several operating points but no tested point met both recall and read-amplification gates.
8. **Runtime promotion:** pending. The best conservative replay saved 5.63 modeled seconds at 1.04% amplification, but no end-to-end tokens-per-second improvement has been measured.

## Recommendations

1. **Make deadline-aware admission the primary lane.** Replace fixed top-k loading with a calibrated expected-value scheduler that accounts for completion probability, expected avoided demand stall, queue occupancy, and cache displacement.
2. **Calibrate probabilities out of prompt.** Convert conditional route scores into held-out hit probabilities by layer pair and lead depth; reject any admission threshold selected on evaluation prompts.
3. **Measure setup, dequantization, and asynchronous execution on hardware.** The current 6.675 GB/s term includes the measured cold-access pattern, but target runtime validation must separately observe request setup, dequantization overlap, queue occupancy, and tokens per second.
4. **Add bounded router probes only if admission remains prediction-limited.** Compare route-only mapping with small hidden-state or full-router-logit probes under prompt-group splits and identical byte budgets.
5. **Keep strict promotion gates.** Require at least five recall points over popularity on 18 of 24 prompt groups, lower exposed stall, and no more than 5% extra reads relative to the equal-budget control.
6. **Build a model-native reference path before reusing the compression bridge for quality claims.** Evaluate baseline and projected candidates through the same MLX arithmetic and retain the `0.001` structural gate until that control exists.
7. **Keep compression secondary.** Revisit a hybrid prior-plus-session residual only after reference validity; do not restart the pure prompt-derived branch.
8. **Keep the bandwidth-constrained oracle as a systems upper bound.** It establishes workload-specific headroom, not a deployable policy or a general ceiling.
9. **Require external SAOD disclosure before treating it as reproduced:** basis scope, rank schedule, precision, construction location/cost, and held-out/free-run degradation.
10. **Do not claim consumer trillion-parameter feasibility yet.** Required future gates include end-to-end decode throughput, full memory accounting, model-quality preservation, and replication on the target architecture.

## Evidence Index

| Artifact | SHA-256 |
|---|---|
| `saod_initial_assessment_v1.md` | `f266acbcef29d88270b8a4d86a7ea307032c919df4bc20129fa7d942c0f8805f` |
| `routing_traces/experiment_result.md` | `e5108d46c4ce4769a4f325ab9d2ec7c59bedf4f8396f50939268ccfb4463d5c7` |
| `mechanism_tournament/c01_decision_v1.json` | `0057d5dd5b04442e67b508421a409e4d7dc8bbeb4a71694f2fd048c273096d43` |
| `mechanism_tournament/c02_c03_decode_decision_packet_v1.md` | `2eeb207e33101ea9cc933ae08428366a025ebd6cc5b122f24027d6622fbec39a` |
| `activation_subspace_runs/q_activation_matched_seeds_0_7_v1.json` | `665e9bb83513ca65e829cc8b4e4c0e34cb12f14ea87b9a724a6e64f466e86af4` |
| `activation_subspace_runs/q_expert_dictionary_layers_0_23_47_v1_summary.json` | `e8972b30a14f70529214ab38076e96d88a7eb6a7b94f428ba41882763de168e9` |
| `prompt_conditioned_internal_direction_protocol_v1.json` | `7ef1d23088c1b7471510aa890f27f6284f5bf3d0faad8c8fa4247b9e60913ddd` |
| `activation_subspace_runs/q_prompt_conditioned_layer0_smoke_failure_v1.json` | `8c244bd4ffbf1d2b44fba5ae6b7aae49ab22886f16be3a9013169f6b3d508a59` |
| `activation_subspace_runs/q_prompt_conditioned_layer0_strict_replay_failure_v1.json` | `d446cddc4407ff31f39ea72b222283d8dec91419df9813aea3b2c05b86122243` |
| `activation_subspace_runs/q_prompt_conditioned_layer0_diagnostic_v1.json` | `26cb504a64774c950128f43fae04c0d7d98d74e70e0415099ec951b1d0243cbe` |
| `activation_subspace_runs/q_reference_replay_diagnosis_v1.json` | `4231223b154d719106e9b5a070fb7c258cf1636f424bf712f4f3d4c49ae50ef7` |
| `activation_subspace_runs/q_prompt_conditioned_layer0_strict_diagnostic_v2.json` | `f26fe8914e9a4f97413609d5c487d09e8cf31572292e2eef267b75d114d13f7d` |
| `mechanism_tournament/router_native_lookahead_d1_k8_v1.json` | `30df0b0d11cbdbf1f12c2d071dc93bf32575010423c06e122110d0ce61b28b46` |
| `mechanism_tournament/router_native_lookahead_operational_depths_v1.json` | `179183a308cae4ad795db2fdbb6da17ff83ffb5c0767c2ec678fcf6eb340a4d3` |
| `mechanism_tournament/router_native_lookahead_long_depths_v1.json` | `71c7831528af1bd00d635c0e4f8242580302f7cfd422895b46bcf1207e371b5d` |
| `mechanism_tournament/router_native_prefetch_queue_d1_k8_c64_bw6675_v1.json` | `c8ba4e75148159c406c2bf86858514c981d6b745da9d40cf075a111e99065a85` |
| `mechanism_tournament/router_native_prefetch_admission_sweep_v1.json` | `d931f38309d23df6a959dedad6f9d004b16c66ca8c10d29ca888f3c75751fca8` |
| `mechanism_tournament/router_native_prefetch_blend_sweep_v1.json` | `bdd3f90ab76661b1b2aa5d077e5fce3e1349551faf780bc53a16440103893220` |

## Scope And Epistemic Limits

- Q is a 122B-A10B proxy, not GLM-5.2 or a trillion-parameter model.
- The SAOD screenshots are claims, not a public reproducible implementation.
- Decode replay models serialized transfer and exposed stall from recorded offsets; it does not measure target-runtime asynchronous I/O or end-to-end tokens per second.
- Activation and weight reconstruction are not logit fidelity or task quality.
- Prompt groups are bounded engineering workloads, not a population sample.
- No raw prompt text, token IDs, activation arrays, weight arrays, or expert identifiers are persisted in result artifacts.

## Current Grade

**A research process; no consumer-trillion feasibility proof.** The program is falsification-driven, cache-correct, hash-bound, lease-governed, controlled, and explicit about invalid or diagnostic-only evidence. It has eliminated several attractive but weak standalone mechanisms, found a strong causal predictor that generalizes across prompt groups, and shown that fixed top-k admission wastes too many bytes even when it lowers modeled stall. The highest-value next experiment is a calibrated deadline-aware admission scheduler, followed by target-runtime asynchronous-I/O validation. The model-native reference remains a secondary prerequisite for any renewed compression work.
