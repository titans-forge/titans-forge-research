# Publication scope — October 13, 2026

This is a curated historical evidence edition, not a new experiment.

## Distinct evidence lanes

- Routing and admission: Qwen3.5-122B-A10B proxy traces and modeled replay.
  Modeled stall improvements are not measured GLM throughput improvements.
- Expert approximation: GLM layer-specific teacher/student results, including
  failed generalization and numerical-fidelity gates. Not broad model quality.
- Systems: July 31 GLM-5.2 Colibri grouped-int4 Metal observations on M5 Max
  128 GB. Three release runs; each comparison control has one run. The 6.46x
  profile ratio does not isolate asynchronous loading or a single kernel.

The complete expert bank was not resident. Process RSS is not checkpoint size.
None of these results demonstrates interactive trillion-parameter inference.

## Later work

Subsequent controls and an October native-router lookahead diagnostic exist
outside this historical package. They must receive separate sanitized aggregate
receipts, provenance and verification before publication. Do not read July's
0.91 tok/s as current performance or compare dates as matched experiments.

## Provenance and redaction

Historical source: JCapone83/AI-Research, consumer-trillion-moe, whose last
tracked package commit at preparation was
`6f1ad49be75a3b5e9160501191842db11642c59f`.
The verifier is the current local strengthened version, not represented as
identical to that commit. The manifest binds the exact staged bytes.

The staging edition removes internal approval identifiers from the report and
suffix-risk JSON, and omits the Word file and private working state. Numerical
observations remain unchanged. Historical source hashes inside receipts refer
to their original artifacts, not necessarily files distributed here.

No weights, raw prompts, activations, token streams, private logs, agent sessions,
credentials or production launchers are included. Aggregate evidence cannot
reproduce inference without the omitted runtime, checkpoint and inputs.

Existing repository/source rights remain unchanged. This preparation does not
assign a new software or model license. Third-party model/runtime rights remain
separate; public availability is not a blanket reuse grant.

## Offline checks

From the repository root, run `python3 tools/check_sparse_publication.py`.
This checks file hashes, bounded hygiene, local Markdown links and the GLM
packet's arithmetic/claim consistency. It does not rerun inference, authenticate
the original observations or prove absence of every possible secret.
