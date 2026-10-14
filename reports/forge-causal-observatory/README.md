# Forge Causal Observatory

**v0.1.0 - saved-evidence verification release**

An auditable research pilot comparing a local language-model mask selector
against a deterministic selector that uses shared causal measurements.
The goal is to check behavior-preserving masks rather than score how plausible
an explanation sounds. This package contains synthetic records and a portable
verifier, not the private Forge runtime or a complete experiment-replay engine.

## Latest Paired Pilot

| Seed | Agent: Worst Preservation | Cheap Baseline: Worst Preservation | Agent / Cheap Gate |
| --- | --- | --- | --- |
| 211 | 43/61 (70.5%) | 56/61 (91.8%) | FAIL / FAIL |
| 223 | 52/61 (85.2%) | 61/61 (100%) | FAIL / PASS |
| 227 | 39/61 (63.9%) | 54/61 (88.5%) | FAIL / FAIL |

Agent passes: **0/3**. Cheap passes: **1/3**. Thresholds were not relaxed and
all three planned trials are included. All masks passed complement damage.
This pilot provides no evidence of an agent advantage over the cheap selector.
It does not establish a population ranking or general coding capability.

## Verify From A Clean Checkout

Python 3.9 or newer, standard library only. No installation, network access,
API keys, models, Apple hardware, environment variables or Forge service needed.

```sh
python3 -B scripts/verify.py
python3 -B -m unittest discover -s tests -v
```

The verifier checks the file manifest, split and choice identities, baseline
selection, raw saved logits, reported counts, budgets and unchanged gates.
A successful verifier exits 0 and reports `evidence_integrity: PASS`.
Scientific FAIL outcomes remain FAIL; they do not make valid evidence invalid.
Corruption or inconsistent claims cause a nonzero exit. The commands can also
be invoked by absolute script path from a different working directory.

## Read Next

- [Methods](METHODS.md): task, mask geometry, shared information and gates.
- [Results](RESULTS.md): every paired outcome, cost and limitations.
- [Export boundary](EXPORT.md): what was transformed and what stays private.
- [Release notes](RELEASE_NOTES.md): scope and initial release.
- [Attribution](THIRD_PARTY_NOTICES.md) and [licensing](LICENSING.md).

The trained toy network saw all 121 inputs. The 60/61 split withholds
intervention measurements, not training inputs. Retaining 15/16 groups does
not prove a minimal circuit. Host-written gate text is not agent reasoning.
Saved-data checks cannot prove experiment execution authenticity or reproduce
the interventions themselves. No production, safety or generalization claim.

Released by Titans Forge LLC on 2026-10-14 under the custom
[Forge Research Hosting and Distribution License 1.0](LICENSE).
Public use and private internal use are free. Companies strictly above
US$1 million in gross annual revenue need a separate license for public
hosting/distribution; the educational exemption is retained. This is a
source-available release, not unrestricted open source.

Location: `reports/forge-causal-observatory/` in the Titans Forge research
repository. Run the two commands inside that directory.
