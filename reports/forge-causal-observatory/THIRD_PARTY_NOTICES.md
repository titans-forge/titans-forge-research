# Attribution And Dependencies

This research should be attributed to Titans Forge LLC,
Forge Causal Observatory, saved-evidence verification release v0.1.0 (2026).
This release is not a peer-reviewed paper.

The original lab used Google DeepMind's [Tracr](https://github.com/google-deepmind/tracr),
whose inspected source tree carries the Apache License 2.0. It also used JAX,
jaxlib, NumPy and dm-haiku. Per-seed original environment version metadata is
preserved in the evidence. These are not install requirements for this package.

The reported proposing model was
[mlx-community/Qwen2.5-Coder-14B-Instruct-4bit](https://huggingface.co/mlx-community/Qwen2.5-Coder-14B-Instruct-4bit),
served with MLX-LM. No model weights, third-party runtime source, Tracr source
or upstream license grants are included or relicensed here. These names identify
the experiment's dependencies; they do not imply endorsement or affiliation.

The verifier is new standard-library-only saved-data validation code. It is not
Tracr, MLX or a port of their model/runtime implementations. Licensor-controlled
new code, documentation and synthetic export are covered by LICENSE only to
the extent Licensor holds the necessary rights. Upstream terms are unchanged.
