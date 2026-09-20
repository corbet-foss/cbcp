#!/usr/bin/env bash
# Copy the canonical LICENSES texts into the Python and JavaScript
# distributions. Root LICENSES/ stays canonical; never edit the copies.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cp "$HERE"/LICENSES/*.txt "$HERE/py/LICENSES/"
cp "$HERE"/LICENSES/*.txt "$HERE/js/@corbet-foss/cbcp/LICENSES/"
git -C "$HERE" status --short LICENSES py/LICENSES js/@corbet-foss/cbcp/LICENSES || true
