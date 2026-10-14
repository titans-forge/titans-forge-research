# Results And Interpretation

Original paired pilot: 2026-10-12. Public review package: 2026-10-14.

| Seed | Agent Keep: Zero / Mean / Resample | Cheap Keep: Zero / Mean / Resample | Agent / Cheap Gate |
| --- | --- | --- | --- |
| 211 | 46/61, 50/61, 43/61 | 61/61, 61/61, 56/61 | FAIL / FAIL |
| 223 | 54/61, 55/61, 52/61 | 61/61, 61/61, 61/61 | FAIL / PASS |
| 227 | 40/61, 46/61, 39/61 | 60/61, 61/61, 54/61 | FAIL / FAIL |

Agent: 0/3 passing masks. Cheap: 1/3. The cheap selector's weakest-method
preservation was higher on each seed. Keep agreement equaled accuracy.
All six masks passed the complement-damage gate. The failed masks are retained.

All three paired trials completed without infrastructure failures or retries.
They used the same qualified local proposer. Choices were 16, 16 and 6;
output-token counts were 7, 7 and 6. Total scientific generation was three
local calls / 20 output tokens, with no cloud calls. This is not a coding test.

The original lab audits checked 4,320 discovery outcomes / 47,520 logits and
4,374 scoring outcomes / 48,114 logits, plus 18 corrupted-evidence controls.
The public verifier checks the same saved numerical coverage and the exported
identities, including 363 training outcome records. Its tests are separate
public-package tests, not a new experiment or another model attempt.

## Historical Context (Not An Exhaustive Public Archive)

Earlier work exercised compiled fixtures, independent task oracles, multiple
replacement methods, parity controls, learned checkpoints and mask-size
frontiers. A prior local proposal failed its novel-mask contract and was not
silently repaired. Compact choices and a strengthened measured baseline were
then tested. This export includes the complete latest paired pilot only; it
does not reproduce or export every historical experiment or operational log.

The existing local upstream also received bounded lifecycle repair and a
controlled recovery qualification. An initial recovery-check failure was
retained and corrected. That operational work is not part of this numerical
release and is not evidence of long-term service reliability.

## What These Results Do Not Establish

- Three seeds do not establish a population ranking or statistical superiority.
- The baseline itself failed two seeds; it is not universally qualified.
- All 121 inputs were trained on; evaluation is not unseen-input generalization.
- Retaining 15/16 groups is not proof of a minimal or unique circuit.
- A choice is not a model-authored mechanism explanation or faithful reasoning.
- Saved logits and reported traces do not prove source execution authenticity.
- No production readiness, healthcare safety, model safety or coding-quality claim.

The next research question would be choice-order/opaque-label sensitivity and
resampling robustness under a separately frozen protocol. No such follow-up
was run or implied by preparing this package. Commercial work remains separate.
