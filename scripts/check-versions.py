"""Require aligned versions and the complete LGPL distribution notices."""
import json
import os
from pathlib import Path
import subprocess
import tomllib

root = Path(__file__).resolve().parent.parent
crate = tomllib.loads((root / "Cargo.toml").read_text())["package"]
name = crate["name"]
version = crate["version"]
license_id = crate["license"]
assert license_id == "LGPL-3.0-only WITH LGPL-3.0-linking-exception"
package = root / "js/@corbet-labs" / name
for manifest in ("package.json", "jsr.json"):
    metadata = json.loads((package / manifest).read_text())
    assert metadata["version"] == version
    # JSR publish validation only accepts bare SPDX ids
    # (https://jsr.io/schema/config-file.v1.json): jsr.json declares plain
    # LGPL-3.0-only while every other manifest carries the full WITH
    # expression. The linking exception text ships in LICENSES/**.
    expected_license = "LGPL-3.0-only" if manifest == "jsr.json" else license_id
    assert metadata["license"] == expected_license
for manifest, key in (("py/pyproject.toml", "project"), ("typst.toml", "package")):
    metadata = tomllib.loads((root / manifest).read_text())[key]
    assert metadata["version"] == version
    assert metadata["license"] == license_id
expected = {path.name: path.read_bytes() for path in (root / "LICENSES").iterdir() if path.is_file()}
for filename in ("LGPL-3.0-only.txt", "LGPL-3.0-linking-exception.txt", "GPL-3.0-only.txt"):
    assert expected[filename], f"Missing complete {filename}"
assert (root / "LICENSE").read_bytes().endswith(expected["LGPL-3.0-only.txt"])
assert b"Copyright 2026 Julian Y. Richard Corbet" in (root / "LICENSE").read_bytes()
# The Python and JavaScript distributions carry committed copies made by
# scripts/sync-licenses.sh; they must match the canonical texts exactly.
for directory in (root / "py/LICENSES", package / "LICENSES"):
    assert {path.name: path.read_bytes() for path in directory.iterdir() if path.is_file()} == expected, directory
lock = tomllib.loads((root / "Cargo.lock").read_text())
assert any(item["name"] == name and item["version"] == version and "source" not in item for item in lock["package"])
# JSR rejects package paths containing whitespace. No file may carry one, and no
# document may point at the retired combined license file name (assembled so
# this gate does not match itself), in plain or URL-encoded form.
retired_names = ["LGPL-3.0-only" + separator + "WITH" + separator + "LGPL-3.0-linking-exception.txt"
                 for separator in (" ", "%20")]
for directory, directories, files in os.walk(root):
    directories[:] = [item for item in directories if item not in {".git", "node_modules", "target", "dist"}]
    for filename in [*directories, *files]:
        assert not any(character.isspace() for character in filename), f"Whitespace in path: {directory}/{filename}"
    for filename in files:
        text = (Path(directory) / filename).read_bytes().decode("utf-8", "ignore")
        assert not any(item in text for item in retired_names), f"Retired license file reference: {directory}/{filename}"
# Shared license lint: no retired license text may survive in tracked files
# (the pattern is assembled so this gate does not match itself), and every
# remaining notice file must carry a REUSE.toml annotation.
retired = "F" + "SL"
found = subprocess.run(["git", "grep", "-il", retired, "--", "."],
                       cwd=root, capture_output=True, text=True).stdout
assert not found, f"Retired license references remain:\n{found}"
reuse = (root / "REUSE.toml").read_text()
for directory in ("LICENSES", "py/LICENSES", f"js/@corbet-labs/{name}/LICENSES"):
    for path in sorted((root / directory).iterdir()):
        if path.is_file():
            assert f"{directory}/{path.name}" in reuse, f"Missing REUSE annotation: {directory}/{path.name}"
print(f"{name}: all distributions at {version}, license {license_id}")
