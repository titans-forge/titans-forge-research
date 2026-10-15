# Titans Forge Medical Research

**Citation-audited research edition | October 15, 2026 | Research only**

These reports ask testable questions about mitochondrial biology, sleep and cognition. They do not demonstrate that a supplement combination works, or that manipulating sleep or mitophagy prevents dementia. They are AI-assisted research syntheses and hypotheses, not peer-reviewed clinical guidance.

## Read the Reports

| Collection | Question | Start here |
| --- | --- | --- |
| Mitochondrial combination: six reports | What do component studies actually support, and what would an informative combination study need to test? | [Evidence landscape](mitochondrial-combination/README.md) |
| The Brain's Night Shift, v6 | Could sleep disruption and impaired mitochondrial quality control jointly identify vulnerability to cognitive decline? | [Research hypothesis](sleep-mitophagy/report.md) |

## What Was Corrected

A kidney pilot used **MitoQ**, not PQQ or ordinary CoQ10. Reviews were mislabeled as trials, a mixed hydrogen/PQQ product was attributed too narrowly, and several primary null results were obscured by positive secondary endpoints. The previous automated rankings, evidence-row counts and simulated detection probabilities are withdrawn from this edition, not cosmetically recalibrated. Sleep biomarker concentrations are now distinguished from clearance flux and dementia outcomes.

[Correction history](CORRECTIONS.md) | [Source ledger](SOURCES.md) | [Structured evidence](evidence.json)

## Scope and Verification

The October 15 check resolved 34 DOI records to PubMed-linked bibliographic records and abstracts. Four additional lookup requests were unresolved and excluded; that is not evidence that those publications do not exist. This is a convenience selection of earlier draft references, not a new systematic literature search or an exhaustive trial-registry update.

Citation identity and abstract-level interpretation were checked. A complete Titans Forge medical-rubric appraisal of full methods, supplements, registration, multiplicity, conflicts and selective reporting remains outstanding. No reader should infer that a reputable source or a verified identifier makes a claim accurate.

Run from this directory using Python 3.9 or newer:

```sh
python3 verify.py
python3 -m unittest discover -s tests -v
```

The verifier checks package integrity, citation links, declared classifications and selected claim boundaries. It does not reproduce experiments, authenticate study conduct, establish scientific validity or prove clinical safety. Hashes bind this edition's files; they are not signatures or independent attestations.

## Publication Boundaries

No source full texts, copied abstracts, patient data, private case material, grant documents, weights or operational logs are included. Earlier local Word/PDF versions and figures are not part of this release because they do not carry these corrections. Original working drafts are retained privately, not silently relabeled as validated evidence.

Published by Titans Forge LLC. Cite the report title, edition date and repository commit. Third-party articles retain their own rights; this package redistributes metadata and original summaries, not the articles. No new license grant is implied by this edition; other repository sections retain their existing terms.
