/**
 * Deterministic BCP 47 locale-ID casting and vendor code mapping.
 *
 * Pure TypeScript port of the cbcp Rust crate: zero dependencies, zero Node
 * APIs, synchronous, no I/O. See `tests/vectors/*.json` for the executable
 * contract shared with the Rust, Python and Typst ports.
 *
 * Two spellings, one rule: lowercase (`de-ch`) for storage and wire,
 * BCP 47 (`de-CH`) for display. Vendor adapters transliterate canonical
 * codes into vendor-expected codes.
 */

// Explicit trim set: space, tab, LF, CR, VT, FF. Do NOT use String.trim() —
// it strips a different (Unicode) set and would eat caller-validation
// characters such as U+FEFF or U+0085.
const TRIM = new Set([' ', '\t', '\n', '\r', '\v', '\f']);

function trimAsciiWs(s: string): string {
    let a = 0;
    let b = s.length;
    while (a < b && TRIM.has(s[a]!)) a++;
    while (b > a && TRIM.has(s[b - 1]!)) b--;
    return s.slice(a, b);
}

// ASCII-only lowercase. Do NOT use toLowerCase() — it folds non-ASCII
// (e.g. U+0130) and would violate the preserve-everything-else rule.
function lowerAscii(s: string): string {
    return s.replace(/[A-Z]/g, (c) => String.fromCharCode(c.charCodeAt(0) + 32));
}

function upperAscii(s: string): string {
    return s.replace(/[a-z]/g, (c) => String.fromCharCode(c.charCodeAt(0) - 32));
}

function isAsciiAlpha(s: string): boolean {
    return /^[A-Za-z]+$/.test(s);
}

function isAsciiDigit(s: string): boolean {
    return /^[0-9]+$/.test(s);
}

/**
 * Normalize an explicit locale ID's spelling without inference or fallback.
 * Trim ASCII whitespace, `_` → `-`, ASCII lowercase. Preserves all subtags,
 * empty segments and non-ASCII characters.
 */
export function normalizeLocaleId(input: string): string {
    return lowerAscii(trimAsciiWs(input).replace(/_/g, '-'));
}

function bcp47Subtag(first: boolean, subtag: string): string {
    if (first) return lowerAscii(subtag);
    if (subtag.length === 4 && isAsciiAlpha(subtag)) {
        return upperAscii(subtag[0]!) + lowerAscii(subtag.slice(1));
    }
    if ((subtag.length === 2 && isAsciiAlpha(subtag)) || (subtag.length === 3 && isAsciiDigit(subtag))) {
        return upperAscii(subtag);
    }
    return lowerAscii(subtag);
}

/**
 * Project a locale ID into BCP 47 display casing: `EN_CH` → `en-CH`,
 * `zh-hant-tw` → `zh-Hant-TW`.
 */
export function toBcp47(code: string): string {
    return normalizeLocaleId(code).split('-').map((s, i) => bcp47Subtag(i === 0, s)).join('-');
}

/**
 * Base ISO 639 language, lowercased. `DE-CH` → `de`.
 */
export function baseLanguage(code: string): string {
    return lowerAscii(normalizeLocaleId(code).split('-')[0] ?? '');
}

/**
 * Structural well-formedness only: `ll`/`lll` alpha, then `-xx…` segments
 * of 2–8 alphanumerics. No registry involved.
 */
export function isWellFormed(code: string): boolean {
    const parts = code.split('-');
    const first = parts[0] ?? '';
    if (!/^[A-Za-z]{2,3}$/.test(first)) return false;
    return parts.slice(1).every((p) => /^[A-Za-z0-9]{2,8}$/.test(p));
}

/**
 * Case- and separator-insensitive locale equality. `localeEq("DE_CH",
 * "de-ch")` is true.
 */
export function localeEq(a: string, b: string): boolean {
    return normalizeLocaleId(a) === normalizeLocaleId(b);
}

/**
 * DeepL source language code: uppercase ISO 639 base. `de-CH` → `DE`.
 */
export function deeplSource(code: string): string {
    return upperAscii(baseLanguage(code));
}

/**
 * DeepL target language code. Regional defaults (`EN-GB`, `PT-PT`,
 * `ZH-HANS`) are explicit product-wide contracts; unmapped codes fall back
 * to the uppercase base.
 */
export function deeplTarget(code: string): string {
    switch (normalizeLocaleId(code)) {
        case 'en': return 'EN-GB';
        case 'en-gb': return 'EN-GB';
        case 'en-us': return 'EN-US';
        case 'pt': return 'PT-PT';
        case 'pt-br': return 'PT-BR';
        case 'zh': return 'ZH-HANS';
        default: return upperAscii(baseLanguage(code));
    }
}

/**
 * Google language code (Maps/Places/Translate): lowercase ISO 639 base.
 * `de-CH` → `de`.
 */
export function googleLanguage(code: string): string {
    return baseLanguage(code);
}
