# Changelog

All notable changes to `cbcp` are documented here. The project follows
Semantic Versioning. Every port ships the same version with the same vectors.

## 0.1.2 - 2026-09-25

- The npm package now ships compiled ESM, CommonJS and TypeScript declarations
  (`dist/`, built on `prepack`) and loads in plain Node.js; previously it pointed
  at `src/index.ts`, which Node.js refuses to strip inside `node_modules`.
- The npm package no longer publishes `tests/`.
- Package checks install the packed npm tarball and run every shared vector under
  plain Node.js through both `import` and `require`, and type-check its
  declarations in both module modes. JSR still publishes the TypeScript sources.

## 0.1.1 - 2026-09-24

- Repository moved to github.com/corbet-foss/cbcp; registry metadata points there.
- Released from a single tag through CI (crates.io and JSR trusted publishing;
  npm and PyPI uploaded from the same release bundle).
- Drop the duplicate space-named license file in `LICENSES/` (a byte copy of
  `LGPL-3.0-linking-exception.txt`); JSR rejects paths with spaces.
- `jsr.json` declares `LGPL-3.0-only`, matching the published JSR metadata; the
  linking exception text ships in every package.

## 0.1.0 - 2026-09-13

- License under LGPL-3.0-only WITH LGPL-3.0-linking-exception: combined works
  link statically or dynamically without Minimal Corresponding Source, Minimal
  Application Code or installation information; library modifications stay LGPL.
- Initial API: `normalize_locale_id`, `to_bcp47`, `base_language`,
  `is_well_formed`, `locale_eq`, `deepl_source`, `deepl_target`,
  `google_language` across Rust, TypeScript, Python and Typst.
- Shared conformance vectors in `tests/vectors/`.
