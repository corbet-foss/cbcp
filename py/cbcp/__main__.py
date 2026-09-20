"""Command-line entrypoint: ``python -m cbcp normalize " DE_Ch "``."""

from __future__ import annotations

import argparse
import json
import sys

from . import (
    normalize_locale_id,
    to_bcp47,
    base_language,
    is_well_formed,
    locale_eq,
    deepl_source,
    deepl_target,
    google_language,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="cbcp", description="BCP 47 locale-ID casting")
    parser.add_argument("--json", action="store_true", help="emit result as JSON")
    parser.add_argument("fn", choices=[
        "normalize", "bcp47", "base", "well-formed", "eq",
        "deepl-source", "deepl-target", "google",
    ])
    parser.add_argument("args", nargs="*")
    ns = parser.parse_args(argv)
    if ns.fn == "eq" and len(ns.args) != 2:
        parser.error("eq needs exactly two locale IDs")
    if ns.fn != "eq" and len(ns.args) != 1:
        parser.error("needs exactly one locale ID")
    result = {
        "normalize": lambda a: normalize_locale_id(a[0]),
        "bcp47": lambda a: to_bcp47(a[0]),
        "base": lambda a: base_language(a[0]),
        "well-formed": lambda a: is_well_formed(a[0]),
        "eq": lambda a: locale_eq(a[0], a[1]),
        "deepl-source": lambda a: deepl_source(a[0]),
        "deepl-target": lambda a: deepl_target(a[0]),
        "google": lambda a: google_language(a[0]),
    }[ns.fn](ns.args)
    if ns.json:
        print(json.dumps({"result": result}))
    else:
        print(str(result).lower() if isinstance(result, bool) else result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
