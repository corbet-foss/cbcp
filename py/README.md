# cbcp (Python)

Python port of the `cbcp` Rust crate: deterministic BCP 47 locale-ID casting
and vendor code mapping. Zero dependencies, Python 3.10+.

See the [repository README](../README.md) for the rule and the
[vectors](../tests/README.md) for the contract.

```sh
python -m cbcp normalize " DE_Ch "
python -m cbcp bcp47 de-ch
python -m cbcp deepl-target en
```
