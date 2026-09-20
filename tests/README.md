# Conformance vectors

Each file holds an array of `{name, fn, input, expected}` objects. `input`
is a string, or an array of strings for two-argument functions
(`locale_eq`). Every port (Rust, TypeScript, Python, Typst) runs every vector
verbatim — same names, same inputs, same expectations.

| File | Functions |
|---|---|
| `locale_ids.json` | `normalize_locale_id`, `is_well_formed`, `locale_eq` |
| `display.json` | `to_bcp47`, `base_language` |
| `vendor.json` | `deepl_source`, `deepl_target`, `google_language` |

`normalize_locale_id` cases mirror cletter's `explicit_locale_ids` vectors:
no inference, no fallback, unknown subtags survive, only the six ASCII
whitespace characters trim, BOM/NEL are preserved for caller validation.
