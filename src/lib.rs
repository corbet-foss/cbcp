//! Deterministic BCP 47 locale-ID casting and vendor code mapping.
//!
//! `cbcp` is the syntax layer below correspondence libraries: it casts locale
//! identifiers between their spellings without interpreting them. No tables of
//! meaning live here — no locale resolution, no country keywords, no variant
//! mapping, no greetings. Those belong to `cletter` and friends, which compose
//! this crate.
//!
//! Two spellings, one rule:
//!
//! - **Storage/wire form** is lowercase (`de-ch`): filesystem paths, R2 keys,
//!   bundle variant IDs, URLs, PDF metadata. Produced by
//!   [`normalize_locale_id`].
//! - **Display form** is BCP 47 (`de-CH`): UI labels and vendor adapters that
//!   demand their own casing. Produced by [`to_bcp47`].
//!
//! Vendor adapters ([`deepl_source`], [`deepl_target`], [`google_language`])
//! transliterate canonical codes into vendor-expected codes. They track vendor
//! documentation; a vendor change is a new `cbcp` minor version.
//!
//! `tests/vectors/*.json` is the executable contract every port (Rust,
//! TypeScript, Python, Typst) implements verbatim.

/// ASCII whitespace trimmed at both edges by [`normalize_locale_id`]:
/// space, tab, LF, CR, VT, FF. Nothing else is stripped — notably neither
/// U+FEFF (BOM) nor U+0085 (NEL), which remain for caller validation.
const TRIM: &[char] = &[' ', '\t', '\n', '\r', '\u{0B}', '\u{0C}'];

/// Normalize an explicit locale ID's spelling without inference or fallback.
///
/// Trims ASCII whitespace at both edges, replaces underscores with hyphens,
/// lowercases ASCII A-Z. Preserves all subtags (including ones absent from any
/// correspondence table), empty segments, and non-ASCII characters. Does not
/// validate, discard subtags, choose a region, or default empty input.
#[must_use]
pub fn normalize_locale_id(input: &str) -> String {
    input
        .trim_matches(TRIM)
        .chars()
        .map(|c| match c {
            '_' => '-',
            'A'..='Z' => (c as u8 - b'A' + b'a') as char,
            _ => c,
        })
        .collect()
}

/// Project a locale ID into BCP 47 display casing.
///
/// Composition: [`normalize_locale_id`] first, then per-subtag casing —
/// language lowercase, 4-letter script in title case, 2-letter or 3-digit
/// region uppercase, anything else lowercase:
///
/// - `EN_CH` → `en-CH`, `de-ch` → `de-CH`
/// - `zh-hant-tw` → `zh-Hant-TW`, `es-419` → `es-419`
#[must_use]
pub fn to_bcp47(code: &str) -> String {
    let normalized = normalize_locale_id(code);
    let mut out = String::with_capacity(normalized.len());
    for (i, subtag) in normalized.split('-').enumerate() {
        if i > 0 {
            out.push('-');
        }
        out.push_str(&bcp47_subtag(i == 0, subtag));
    }
    out
}

fn bcp47_subtag(first: bool, subtag: &str) -> String {
    if first {
        return subtag.to_ascii_lowercase();
    }
    let alpha = subtag.bytes().all(|b| b.is_ascii_alphabetic());
    let digit = subtag.bytes().all(|b| b.is_ascii_digit());
    if subtag.len() == 4 && alpha {
        // Script: title case.
        let mut chars = subtag.chars();
        let head = chars.next().unwrap_or_default().to_ascii_uppercase();
        let tail: String = chars.as_str().to_ascii_lowercase();
        return format!("{head}{tail}");
    }
    if (subtag.len() == 2 && alpha) || (subtag.len() == 3 && digit) {
        // Region: uppercase (letters unaffected when numeric).
        return subtag.to_ascii_uppercase();
    }
    subtag.to_ascii_lowercase()
}

/// Extract the base ISO 639 language from a locale ID, lowercased.
/// `DE-CH` → `de`, `en` → `en`. Never fails; may return garbage for garbage.
#[must_use]
pub fn base_language(code: &str) -> String {
    normalize_locale_id(code)
        .split('-')
        .next()
        .unwrap_or_default()
        .to_ascii_lowercase()
}

/// Structural well-formedness only: `ll` or `lll` alpha, then `-xx…`
/// segments of 2–8 alphanumerics. No registry involved — `xx-yy` passes,
/// `en__US` and `""` do not.
#[must_use]
pub fn is_well_formed(code: &str) -> bool {
    let mut parts = code.split('-');
    match parts.next() {
        Some(first)
            if (2..=3).contains(&first.len()) && first.bytes().all(|b| b.is_ascii_alphabetic()) => {
        }
        _ => return false,
    }
    for part in parts {
        if !(2..=8).contains(&part.len()) || !part.bytes().all(|b| b.is_ascii_alphanumeric()) {
            return false;
        }
    }
    true
}

/// Case- and separator-insensitive locale equality via normalization.
/// `locale_eq("DE_CH", "de-ch")` is true.
#[must_use]
pub fn locale_eq(a: &str, b: &str) -> bool {
    normalize_locale_id(a) == normalize_locale_id(b)
}

/// `DeepL` source language code: uppercase `ISO 639` base. `de-CH` → `DE`.
#[must_use]
pub fn deepl_source(code: &str) -> String {
    base_language(code).to_ascii_uppercase()
}

/// `DeepL` target language code. Regional defaults (`EN-GB`, `PT-PT`,
/// `ZH-HANS`) are explicit product-wide contracts: every tool renders the
/// same default for a bare language. Anything unmapped falls back to the
/// uppercase base.
#[must_use]
pub fn deepl_target(code: &str) -> String {
    let lower = normalize_locale_id(code);
    match lower.as_str() {
        "en" | "en-gb" => "EN-GB".to_owned(),
        "en-us" => "EN-US".to_owned(),
        "pt" => "PT-PT".to_owned(),
        "pt-br" => "PT-BR".to_owned(),
        "zh" => "ZH-HANS".to_owned(),
        _ => base_language(code).to_ascii_uppercase(),
    }
}

/// `Google` language code (Maps/Places/Translate): lowercase `ISO 639` base.
/// `de-CH` → `de`.
#[must_use]
pub fn google_language(code: &str) -> String {
    base_language(code)
}

#[cfg(test)]
mod vector_tests {
    use std::path::PathBuf;

    fn apply(fn_name: &str, input: &serde_json::Value) -> serde_json::Value {
        let s = |v: &serde_json::Value| v.as_str().unwrap_or("").to_owned();
        match fn_name {
            "normalize_locale_id" => {
                serde_json::Value::String(super::normalize_locale_id(&s(input)))
            }
            "to_bcp47" => serde_json::Value::String(super::to_bcp47(&s(input))),
            "base_language" => serde_json::Value::String(super::base_language(&s(input))),
            "is_well_formed" => serde_json::Value::Bool(super::is_well_formed(&s(input))),
            "locale_eq" => {
                let pair = input.as_array().cloned().unwrap_or_default();
                let (a, b) = (pair.first(), pair.get(1));
                match (a, b) {
                    (Some(a), Some(b)) => serde_json::Value::Bool(super::locale_eq(&s(a), &s(b))),
                    _ => serde_json::Value::Null,
                }
            }
            "deepl_source" => serde_json::Value::String(super::deepl_source(&s(input))),
            "deepl_target" => serde_json::Value::String(super::deepl_target(&s(input))),
            "google_language" => serde_json::Value::String(super::google_language(&s(input))),
            _ => panic!("unknown vector fn: {fn_name}"),
        }
    }

    #[test]
    fn conformance_vectors() {
        let dir = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("tests/vectors");
        let mut files: Vec<_> = std::fs::read_dir(&dir)
            .expect("tests/vectors readable")
            .map(|e| e.expect("dir entry").path())
            .filter(|p| p.extension().is_some_and(|e| e == "json"))
            .collect();
        files.sort();
        assert!(!files.is_empty(), "at least one vector file");
        for file in files {
            let raw = std::fs::read_to_string(&file).expect("vector file readable");
            let vectors: Vec<serde_json::Value> =
                serde_json::from_str(&raw).expect("vectors parse");
            for v in &vectors {
                let name = v["name"].as_str().unwrap_or("?");
                let actual = apply(v["fn"].as_str().unwrap_or(""), &v["input"]);
                assert_eq!(actual, v["expected"], "{} ({})", name, file.display());
            }
        }
    }
}
