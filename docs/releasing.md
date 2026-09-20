# Releasing

Vector-first: behavior changes land in `tests/vectors/*.json` before any
port. Every port runs every vector verbatim.

1. Add or adjust vectors. A vendor documentation change (DeepL, Google) is a
   minor version bump by policy; everything else follows SemVer.
2. Implement in Rust (`src/lib.rs`), TypeScript (`js/`), Python (`py/`),
   Typst (`typst/`). Keep the function mapping 1:1 across ports.
3. Run `bash scripts/sync-licenses.sh`; the tree must stay clean afterwards.
4. Verify locally:
   - `cargo test` (vector runner plus unit tests, warning-free)
   - `bun test` and `tsc --noEmit -p ./tsconfig.json` in `js/@corbet-foss/cbcp`
   - `python3 py/scripts/conformance.py` with `PYTHONPATH=py`
   - `typst compile --root . typst/tests/test.typ -f pdf <out>`
5. Bump all four manifests to the same version (`Cargo.toml`,
   `js/@corbet-foss/cbcp/package.json` + `jsr.json`, `py/pyproject.toml`,
   `typst.toml`), update `CHANGELOG.md`.
6. Publish Rust (crates.io), JavaScript (npm + JSR), Python (PyPI) and Typst
   (registry) from the same tag. Verify installed artifacts per registry
   before announcing.
