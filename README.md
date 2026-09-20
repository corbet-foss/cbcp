# cbcp

**BCP 47 locale-ID casting and vendor code mapping, identical in every language.**

[![crates.io](https://img.shields.io/crates/v/cbcp.svg)](https://crates.io/crates/cbcp) [![npm](https://img.shields.io/npm/v/@corbet-foss/cbcp.svg)](https://www.npmjs.com/package/@corbet-foss/cbcp) [![PyPI](https://img.shields.io/pypi/v/cbcp.svg)](https://pypi.org/project/cbcp/) [![JSR](https://jsr.io/badges/@corbet-foss/cbcp)](https://jsr.io/@corbet-foss/cbcp)

```js
import { normalizeLocaleId, toBcp47, deeplTarget } from '@corbet-foss/cbcp';

normalizeLocaleId(' DE_Ch '); // 'de-ch' — storage and wire form
toBcp47('de-ch');             // 'de-CH' — display form
deeplTarget('en');            // 'EN-GB' — vendor contract
```

```rust
use cbcp::{normalize_locale_id, to_bcp47, deepl_target};

assert_eq!(normalize_locale_id(" DE_Ch "), "de-ch");
assert_eq!(to_bcp47("de-ch"), "de-CH");
assert_eq!(deepl_target("en"), "EN-GB");
```

```python
from cbcp import normalize_locale_id, to_bcp47, deepl_target

assert normalize_locale_id(" DE_Ch ") == "de-ch"
assert to_bcp47("de-ch") == "de-CH"
assert deepl_target("en") == "EN-GB"
```

```typst
#import "cbcp.typ": normalize-locale-id, to-bcp47, deepl-target
#assert.eq(normalize-locale-id(" DE_Ch "), "de-ch")
#assert.eq(to-bcp47("de-ch"), "de-CH")
#assert.eq(deepl-target("en"), "EN-GB")
```

## Rule

Two spellings, one rule. **Lowercase** (`de-ch`) is stored and sent:
filesystem paths, keys, bundle IDs, URLs, document metadata. **BCP 47**
(`de-CH`) is displayed: UI labels and vendor adapters that demand their own
casing. `tests/vectors/*.json` is the executable contract every port
implements verbatim — same names, same inputs, same expectations.

`cbcp` is the syntax layer below correspondence: no locale resolution, no
country keywords, no variant mapping, no greetings. Those live in `cletter`,
which composes this crate. Vendor adapters (`deepl_*`, `google_language`)
transliterate canonical codes into vendor-expected codes and track vendor
documentation; a vendor change is a new `cbcp` minor version.

## Install

| Environment | Command |
|---|---|
| Rust / Cargo | `cargo add cbcp` |
| Node.js / npm | `npm install @corbet-foss/cbcp` |
| Deno | `deno add jsr:@corbet-foss/cbcp` |
| Python / pip | `python -m pip install cbcp` |

See [installation](docs/installation.md) for details and [releasing](docs/releasing.md)
for the vector-first release process.

## License

Copyright 2026 Julian Y. Richard Corbet. Licensed under
[LGPL-3.0-only WITH LGPL-3.0-linking-exception](<LICENSES/LGPL-3.0-only WITH LGPL-3.0-linking-exception.txt>).
See [LICENSE.md](LICENSE.md).
Contributions are subject to the [Contributor License Agreement](CLA.md).
