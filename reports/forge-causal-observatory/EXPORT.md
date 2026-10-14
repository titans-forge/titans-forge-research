# Public Export Boundary

This is an allowlisted derivative export, not a copy of the live lab folder.
The original frozen records are not modified. Raw numerical logits, counts,
unit norms, split pairs, gates and proposal choices retain their values.

## Included

- All three seeds from the latest paired pilot, including every failed gate.
- Synthetic task pairs, training outcome records and checkpoint hash identities.
- Public discovery packets, shared/candidate/control/paired saved logits.
- Opaque unit masks and opaque donor plans; exact safe proposal messages.
- Raw model answer text, finish reason, usage totals and per-call token ceiling.
- Original artifact byte counts/SHA-256 identified by neutral role labels.
- A new public manifest for the exported files and standalone verification code.

## Transformations

Real architecture group IDs in retained-unit lists and donor-plan keys become
the original opaque IDs through the recorded one-to-one mapping. No numerical
outcome is changed. Private source locations, ledger IDs, process IDs, health
endpoints, service metadata, server timestamps and hardware fingerprints are
excluded rather than replaced with plausible stand-ins. Only the declared
fields of each original document are exported; unknown fields are not copied.

Original hashes identify the private publisher-held input artifacts; some
original documents contain excluded fields. Readers cannot recompute those
original hashes from the sanitized derivative. `MANIFEST.json` hashes the
actual public bytes and can be checked independently. Neither manifest is a
digital signature or independent attestation of experiment execution.

## Excluded

No private Forge kernel, workflow database, memory store, customer material,
account credentials, operational logs, runtime supervisor, launch configuration,
model weights, toy checkpoints, environment, cache or third-party source tree.
The exporter and its private source-binding receipt stay outside this package.

## Scope Of Reproducibility

A fresh checkout can reproduce saved-evidence validation and every reported
gate without the original machine or private runtime. It cannot rerun training,
regenerate logits or repeat the causal interventions. Full experiment replay
would require a separately reviewed portable runtime release. This package
must not be described as that release.

The manifest's strict inventory and rejection tests check integrity and common
privacy hazards. They do not substitute for owner review or comprehensive
secret detection. Adding any file requires re-export and a new manifest.
