"""Deterministic BCP 47 locale-ID casting and vendor code mapping.

Pure-Python port of the cbcp Rust crate: zero dependencies, no I/O.
See tests/vectors/*.json for the executable contract shared with the
Rust, TypeScript and Typst ports.

Two spellings, one rule: lowercase (de-ch) for storage and wire,
BCP 47 (de-CH) for display.
"""

from __future__ import annotations

__all__ = [
    "normalize_locale_id",
    "to_bcp47",
    "base_language",
    "is_well_formed",
    "locale_eq",
    "deepl_source",
    "deepl_target",
    "google_language",
]

# Explicit trim set: space, tab, LF, CR, VT, FF. Do NOT use bare str.strip():
# it removes Unicode whitespace (U+FEFF, U+0085) that callers validate.
_TRIM = " \t\n\r\x0b\x0c"

_ASCII_UPPER = {chr(c): chr(c + 32) for c in range(ord("A"), ord("Z") + 1)}
_ASCII_LOWER = {chr(c): chr(c - 32) for c in range(ord("a"), ord("z") + 1)}


def _lower_ascii(s: str) -> str:
    # ASCII-only: str.lower() would fold non-ASCII (e.g. U+0130).
    return "".join(_ASCII_UPPER.get(c, c) for c in s)


def _upper_ascii(s: str) -> str:
    return "".join(_ASCII_LOWER.get(c, c) for c in s)


def normalize_locale_id(code: str) -> str:
    """Trim ASCII whitespace, ``_`` → ``-``, ASCII lowercase.

    Preserves all subtags, empty segments and non-ASCII characters.
    No inference, no fallback, no validation.
    """
    return _lower_ascii(code.strip(_TRIM).replace("_", "-"))


def _bcp47_subtag(first: bool, subtag: str) -> str:
    if first:
        return _lower_ascii(subtag)
    if len(subtag) == 4 and subtag.isascii() and subtag.isalpha():
        return _upper_ascii(subtag[:1]) + _lower_ascii(subtag[1:])
    if (len(subtag) == 2 and subtag.isascii() and subtag.isalpha()) or (
        len(subtag) == 3 and subtag.isascii() and subtag.isdigit()
    ):
        return _upper_ascii(subtag)
    return _lower_ascii(subtag)


def to_bcp47(code: str) -> str:
    """Project into BCP 47 display casing: ``EN_CH`` → ``en-CH``."""
    return "-".join(
        _bcp47_subtag(i == 0, s) for i, s in enumerate(normalize_locale_id(code).split("-"))
    )


def base_language(code: str) -> str:
    """Base ISO 639 language, lowercased: ``DE-CH`` → ``de``."""
    return _lower_ascii(normalize_locale_id(code).split("-", 1)[0])


def is_well_formed(code: str) -> bool:
    """Structural check only: ``ll``/``lll`` alpha, then ``-xx`` segments of
    2–8 alphanumerics. No registry involved."""
    parts = code.split("-")
    first = parts[0]
    if not (2 <= len(first) <= 3 and first.isascii() and first.isalpha()):
        return False
    return all(
        2 <= len(p) <= 8 and p.isascii() and p.isalnum() for p in parts[1:]
    )


def locale_eq(a: str, b: str) -> bool:
    """Case- and separator-insensitive equality."""
    return normalize_locale_id(a) == normalize_locale_id(b)


def deepl_source(code: str) -> str:
    """DeepL source code: uppercase base. ``de-CH`` → ``DE``."""
    return _upper_ascii(base_language(code))


def deepl_target(code: str) -> str:
    """DeepL target code. Regional defaults (``EN-GB``, ``PT-PT``,
    ``ZH-HANS``) are explicit product-wide contracts; unmapped codes fall
    back to the uppercase base."""
    lower = normalize_locale_id(code)
    return {
        "en": "EN-GB",
        "en-gb": "EN-GB",
        "en-us": "EN-US",
        "pt": "PT-PT",
        "pt-br": "PT-BR",
        "zh": "ZH-HANS",
    }.get(lower, _upper_ascii(base_language(code)))


def google_language(code: str) -> str:
    """Google language code: lowercase base. ``de-CH`` → ``de``."""
    return base_language(code)
