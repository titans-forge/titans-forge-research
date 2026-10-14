# Methods

## Task And Fixture

The toy research task is `(a + b) % 11` for integers a and b from 0 through 10.
Each of the three fresh seeds (211, 223, 227) used one training attempt with
1,200 Adam updates and learning rate 0.01. All 121 input pairs were used in
training; each fixture reported 121/121 correct. This is not fine-tuning of
the proposing language model. The saved version metadata describes the
original experiment environment, not dependencies of this verifier.

## Intervention Geometry

There are 16 fine output-activation groups: attention-output channel groups
and MLP-output blocks. A mask retains exactly 15 groups. Keep experiments
replace omitted groups; complement experiments retain only the omitted group.
The replacement methods are zero, discovery-activation mean, and deterministic
discovery resampling. Resampling donors are selected from the 60 discovery
cases, not from evaluation outcomes. The public export preserves the opaque
donor plans but does not include an implementation that replays interventions.

## Information And Selection

Both selectors received the same 16 opaque unit IDs, kinds and weight norms,
and accuracy/agreement counts for eight common 15-unit masks under all three
methods. Common omissions include the lowest-norm unit, lowest-norm units of
each kind, and seeded additional omissions until eight distinct masks exist.

Both may choose any of the 16 omissions, including already measured ones.
The cheap selector maximizes the minimum count across all methods AND both
accuracy and agreement. Ties maximize the total of those six counts, then
choose the lexicographically smallest omitted opaque ID. There is no fitted
scorer, hidden catalogue access or extra discovery for the cheap selector.

The local proposer was the reported MLX model
`mlx-community/Qwen2.5-Coder-14B-Instruct-4bit`. It received choices in opaque-ID
order and returned one integer choice. Each seed allowed one call, at most
64 generated tokens and 120 seconds, with no retries or tools. Bare JSON or
one exact JSON fence was accepted. Metadata and gate prose were host-authored.
The exact safe messages, compact facts and raw answer text are exported;
server IDs, hardware fingerprints, timestamps and networking details are not.

Both final masks were sealed before evaluation. Each selector was charged
the eight shared masks plus three discovery probes of its final candidate,
even if that candidate had already been measured. No evaluation-driven
selection, replacement seed or baseline-only rescue occurred in this pilot.

## Split, Controls And Gates

The 121 pairs are ordered by a salted SHA-256 key; the first 60 are discovery
and the remaining 61 are evaluation. Public records contain the exact split
and salt. Inputs are disjoint for intervention measurements only.

Every final mask has three keep and three complement evaluation conditions.
Full/empty masks, no-op/self replacement, coarse/fine parity and an attention
ablation control were checked in the original apparatus. Raw full/empty and
paired logits are exported. Some control assertions, including the attention
control's summary, are retained reports rather than independently replayed
controls. `trace: true` is also a retained assertion, not a public replay proof.

Frozen gates, required under EVERY replacement method:

- Full-model accuracy >= 99% (61/61 for this evaluation size).
- Keep accuracy AND agreement with the full model >= 95% (at least 58/61).
- Full-model minus complement accuracy >= 25 percentage points.

The verifier reconstructs counts with first-index argmax over 11 saved logits,
then computes these same gates. It distinguishes a scientifically failed mask
from corrupted evidence. It checks exactly 24 common discovery conditions,
six final-candidate discovery conditions, six full/empty controls and 12 paired
keep/complement conditions per seed. Saved runtime accounting is 31 charged
calls / 1,680 sequence examples for discovery and 33 / 1,883 for scoring.
These counts include apparatus overhead and are not language-model API calls.
