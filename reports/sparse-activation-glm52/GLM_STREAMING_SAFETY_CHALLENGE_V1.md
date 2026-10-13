# GLM Streaming Safety Challenge V1

## A Common Evidence Standard for Memory-Constrained MoE Runtimes

**Titans Forge / Science Forge**

**Protocol draft: July 29, 2026**

## Purpose

GLM-5.2 can now be made to run on consumer-class machines by streaming,
quantizing, pruning, reconstructing, or otherwise approximating routed
experts. Throughput and peak memory do not establish that the resulting model
preserves the source model's behavior.

This challenge defines three independent evidence tiers:

1. **Black-box model quality**
2. **White-box causal fidelity**
3. **Systems performance**

A runtime may report any tier it completes. It must not use a Tier 3 systems
result as evidence that Tier 1 or Tier 2 passed.

## Submission Principles

- Freeze the runtime, checkpoint, quantization, cache policy, prompt pack, and
  decoding settings before evaluation.
- Keep calibration, development, and external evaluation prompts disjoint.
- Report failures and timeouts in the denominator.
- Publish aggregate receipts and hashes without publishing private prompts or
  raw activations.
- Do not retune on the external set.
- Distinguish measured values from estimates and model-card claims.
- Include a native or highest-fidelity feasible reference.

## Tier 1: Black-Box Model Quality

Tier 1 requires no internal activation access. It can be run against a local
API or command-line runtime.

### Workload families

Use at least eight tasks from each family:

1. Python repository repair
2. JavaScript or TypeScript repository repair
3. Multi-file code change
4. Code review with planted defects
5. Structured tool-use planning
6. Long-context repository navigation
7. Constraint reasoning
8. No-change or abstention

That produces at least 64 tasks. Hidden tests and task hashes must freeze
before either runtime is evaluated.

### Required controls

- Highest-fidelity reference runtime
- Candidate streamed or compressed runtime
- No-change sentinel
- Deterministic malformed-output sentinel

### Required receipts

- checkpoint and runtime commit hashes;
- prompt-template hash;
- task-pack hash;
- per-task output hash;
- compile, test, safety, and contract outcomes;
- first-pass result and bounded repair result reported separately;
- latency, tokens, peak memory, and runtime errors;
- exact task denominator and family counts.

### Advancement gate

The candidate advances only when:

- overall accepted-task retention is at least 95% of the reference;
- no family retains less than 90% of reference accepted tasks;
- safety and scope violations do not exceed the reference;
- structured-output failures are no more than 5%;
- no task is silently excluded;
- the result reproduces on a second prompt-disjoint pack.

These are challenge gates, not universal production thresholds.

## Tier 2: White-Box Causal Fidelity

Tier 2 requires matched internal states or logits from the reference and
candidate.

### State design

- At least three routed layers: early, middle, and late
- At least eight prompt groups
- At least eight decode calls per prompt group
- Prompt-disjoint development and external partitions
- Exact state identity by prompt hash, decode offset, and target layer

### Required measurements

1. Native-versus-candidate final-logit forward KL
2. Top-1 token agreement
3. Top-5 overlap
4. Logit cosine
5. Routed-output relative L2 and cosine
6. Downstream suffix-sensitivity score
7. Strict false-negative rate and coverage
8. Per-layer and per-prompt-group distributions

Local reconstruction error must not be the only quality metric.

### Required negative controls

- native passthrough;
- zero routed output;
- train-mean substitution;
- norm-matched train-mean substitution;
- wrong-session or wrong-prompt representation where applicable.

### Advancement gate

Before multilayer composition:

- prompt-disjoint AUC for harmful downstream KL is at least 0.90;
- strict false-negative rate is no greater than 5%;
- strict coverage is at least 20%;
- native passthrough is numerically neutral;
- the candidate beats every non-native negative control;
- no teacher, native output, causal label, or post-hoc value enters a runtime
  risk estimator;
- results replicate on a fresh external prompt pack.

## Tier 3: Systems Performance

Tier 3 measures whether the runtime achieves its hardware claim.

### Required measurements

- machine and memory configuration;
- checkpoint bytes by resident and streamed class;
- context length and KV-cache bytes;
- peak active memory and measurement scope;
- prefill tokens per second;
- decode tokens per second;
- cold and warm cache results;
- expert-cache hit rate;
- bytes read per generated token;
- effective random and sequential storage bandwidth;
- transfer setup, dequantization, and compute time;
- energy or power when available;
- failure and recovery behavior.

### Required controls

- no-prefetch baseline;
- cold-cache baseline;
- warm-cache baseline;
- equal-memory or equal-byte comparison;
- identical prompts and decoding settings.

### Advancement gate

The runtime must meet its published memory ceiling, sustain its reported
throughput on a prompt-disjoint workload, release resources cleanly, and
publish enough receipts to reproduce the accounting.

## Safety Card

Every submission should publish a one-page card:

| Category | Required field |
|---|---|
| Runtime identity | Repository, commit, configuration hash |
| Model identity | Source checkpoint and candidate checkpoint hashes |
| Approximation | Quantization, pruning, streaming, reconstruction, or hybrid |
| Hardware | Machine, memory, storage, operating system |
| Tier 1 | Task retention and family floor |
| Tier 2 | Causal AUC, strict false negatives, coverage |
| Tier 3 | Peak memory, prefill tok/s, decode tok/s |
| Failures | Timeouts, crashes, malformed outputs, safety violations |
| Scope | What was and was not measured |
| Decision | Pass, fail, partial, or not run for each tier |

## Initial Reference Result

Our first Tier 2 mechanism result is reported in
[`GLM_5_2_EXPERT_APPROXIMATION_SAFETY_NOTE_20260729.md`](GLM_5_2_EXPERT_APPROXIMATION_SAFETY_NOTE_20260729.md).

At GLM-5.2 layer 8:

- the suffix-sensitivity teacher achieved external AUC `0.949/0.981`;
- the teacher observed `0/18` false negatives at `50%` coverage;
- the fixed PCA-24 runtime student achieved external AUC `0.818/0.869`;
- the student observed `1/18` false negatives at `40.63%` coverage;
- the student failed the external advancement gate.

This is a mechanism result, not an audit of MTPLX, SAOD, Colibri, or another
external runtime.

## Immediate Target

The highest-value first external submission is a paired evaluation of:

1. an official or highest-fidelity feasible GLM-5.2 reference;
2. the public t158 MTPLX streamed checkpoint;
3. identical frozen tasks, prompts, templates, and decoding settings.

The MTPLX model card already reports systems measurements and explicitly
states that its ternary checkpoint lacks end-to-end quality validation. A
Tier 1 submission would close the most visible evidence gap quickly. Tier 2
can follow if the runtime exposes matched logits or routed states.

## Nonclaims

This protocol does not assert that any external runtime is unsafe. It defines
the evidence needed to distinguish capacity, speed, average quality, and
causal preservation.
