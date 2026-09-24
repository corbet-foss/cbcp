#!/usr/bin/env python3
"""Focused package checks; CI providers supply scheduling and credentials."""

import argparse
from email.parser import BytesParser
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tarfile
import tempfile
import time
import tomllib
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = tomllib.loads((ROOT / "Cargo.toml").read_text())["package"]
NAME, VERSION = PACKAGE["name"], PACKAGE["version"]
JS = ROOT / "js" / "@corbet-labs" / NAME

# The JavaScript package ships its TypeScript sources without a build step, so
# installed-package consumers run under Bun and Deno, which load .ts directly.
# Every consumer runs the complete shared vector suite from tests/vectors.
VERIFY_API = """import vectors from './vectors.json' with { type: 'json' };
const FNS = {
    normalize_locale_id: (api, input) => api.normalizeLocaleId(input),
    to_bcp47: (api, input) => api.toBcp47(input),
    base_language: (api, input) => api.baseLanguage(input),
    is_well_formed: (api, input) => api.isWellFormed(input),
    locale_eq: (api, input) => api.localeEq(input[0], input[1]),
    deepl_source: (api, input) => api.deeplSource(input),
    deepl_target: (api, input) => api.deeplTarget(input),
    google_language: (api, input) => api.googleLanguage(input),
};
export function verify(api) {
    for (const vector of vectors) {
        const actual = FNS[vector.fn](api, vector.input);
        if (JSON.stringify(actual) !== JSON.stringify(vector.expected)) {
            throw new Error(`${vector.name}: ${JSON.stringify(actual)} !== ${JSON.stringify(vector.expected)}`);
        }
    }
    if (!vectors.length) throw new Error('No shared vectors ran');
    console.log(`${vectors.length} shared vectors passed`);
}
"""
CONSUMER = f"""import {{ verify }} from './verify-api.mjs';
verify(await import('@corbet-labs/{NAME}'));
"""


def js_helpers(directory):
    """Write the vector-driven API verifier next to a consumer."""
    vectors = []
    for path in sorted((ROOT / "tests" / "vectors").glob("*.json")):
        vectors.extend(json.loads(path.read_text(encoding="utf-8")))
    (directory / "vectors.json").write_text(json.dumps(vectors, ensure_ascii=False))
    (directory / "verify-api.mjs").write_text(VERIFY_API)
    (directory / "consumer.mjs").write_text(CONSUMER)
    return (directory / "verify-api.mjs").as_uri()


def run(*args, cwd=None, env=None):
    print("+ " + " ".join(map(str, args)), flush=True)
    subprocess.run(list(map(str, args)), cwd=ROOT if cwd is None else cwd, env=env, check=True)


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def artifact_directory():
    base, commit = os.environ.get("ARTIFACT_ROOT"), os.environ.get("CI_COMMIT_SHA", "")
    if not base or not Path(base).is_absolute() or not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("Package checks require an absolute ARTIFACT_ROOT and exact CI_COMMIT_SHA")
    directory = Path(base) / NAME / commit
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def preserve(path, data):
    """Install immutable evidence without replacing a different existing artifact."""
    try:
        with path.open("xb") as stream:
            stream.write(data)
    except FileExistsError:
        if path.read_bytes() != data:
            raise ValueError(f"Existing release artifact differs: {path.name}") from None


def export(check, paths):
    directory = artifact_directory()
    manifest = {}
    for source in paths:
        source = Path(source)
        preserve(directory / source.name, source.read_bytes())
        manifest[source.name] = digest(source)
    preserve(directory / "SOURCE_COMMIT", (os.environ["CI_COMMIT_SHA"] + "\n").encode())
    receipt = {
        "schema": 1, "package": NAME, "version": VERSION, "check": check,
        "commit": os.environ["CI_COMMIT_SHA"],
        "source_sha256": os.environ.get("SOURCE_SHA256"),
        "tool_revision": os.environ.get("CCID_REVISION"),
        "dependency_manifest_sha256": os.environ.get("DEPENDENCY_MANIFEST_SHA256"),
        "artifacts": manifest,
    }
    preserve(directory / f"{check}.json", (json.dumps(receipt, indent=2, sort_keys=True) + "\n").encode())
    hashes = {path.name: digest(path) for path in directory.iterdir()
              if path.is_file() and path.suffix in {".crate", ".tgz", ".whl", ".gz"}}
    # This aggregate index is derived; individual artifacts and receipts are immutable.
    index = directory / f".SHA256SUMS.{os.getpid()}"
    index.write_text("".join(f"{value}  {name}\n" for name, value in sorted(hashes.items())))
    index.replace(directory / "SHA256SUMS")
    print(json.dumps({"artifact_directory": str(directory), "receipt": receipt}, sort_keys=True))


def metadata():
    run("python3", "scripts/check-versions.py")
    # cbcp has no generated tables; its only synchronized copies are the
    # distribution license texts written by scripts/sync-licenses.sh.
    generated = [ROOT / "py" / "LICENSES", JS / "LICENSES"]
    paths = [p for entry in generated for p in (entry.rglob("*") if entry.is_dir() else [entry]) if p.is_file()]
    before = {str(path.relative_to(ROOT)): digest(path) for path in paths}
    run("bash", ROOT / "scripts/sync-licenses.sh")
    paths = [p for entry in generated for p in (entry.rglob("*") if entry.is_dir() else [entry]) if p.is_file()]
    after = {str(path.relative_to(ROOT)): digest(path) for path in paths}
    if before != after:
        changed = sorted(key for key in before.keys() | after.keys() if before.get(key) != after.get(key))
        raise ValueError("Synchronized license copies differ: " + ", ".join(changed))


def js_install():
    run("bun", "install", "--frozen-lockfile", cwd=JS)


def javascript():
    js_install()
    run("bun", "run", "typecheck", cwd=JS)
    run("bun", "run", "conformance", cwd=JS)


def npm_tarball():
    return JS / f"corbet-labs-{NAME}-{VERSION}.tgz"


def pack_check(manager, tarball):
    """Install the packed artifact outside the repository's module-resolution tree."""
    with tempfile.TemporaryDirectory(prefix=f"{NAME}-consumer-") as temporary:
        consumer = Path(temporary)
        (consumer / "package.json").write_text('{"name":"package-consumer","private":true,"type":"module"}\n')
        shutil.copyfile(tarball, consumer / "package.tgz")
        commands = {
            "npm": ["npm", "install", "--ignore-scripts", "--no-audit", "--no-fund", "./package.tgz"],
            "pnpm": ["npx", "--yes", "pnpm@10.15.1", "add", "--ignore-scripts", "./package.tgz"],
            "yarn": ["npx", "--yes", "yarn@1.22.22", "add", "--ignore-scripts", "./package.tgz"],
            "bun": ["bun", "add", "--ignore-scripts", "./package.tgz"],
        }
        run(*commands[manager], cwd=consumer)
        installed = consumer / "node_modules" / "@corbet-labs" / NAME
        published = json.loads((installed / "package.json").read_text())
        source = json.loads((JS / "package.json").read_text())
        if published["version"] != VERSION or published["license"] != source["license"]:
            raise ValueError("Installed version or license differs")
        expected = {path.name: path.read_bytes() for path in (ROOT / "LICENSES").iterdir() if path.is_file()}
        actual = {path.name: path.read_bytes() for path in (installed / "LICENSES").iterdir() if path.is_file()}
        if actual != expected:
            raise ValueError("Installed license inventory or texts differ")
        js_helpers(consumer)
        run("bun", "consumer.mjs", cwd=consumer)
        print(f"@corbet-labs/{NAME}: {manager} installation passed")


def js_package():
    artifact_directory()
    js_install()
    run("npm", "pack", cwd=JS)
    tarball = npm_tarball()
    pack_check("npm", tarball)
    run("deno", "publish", "--dry-run", "--allow-dirty", cwd=JS)
    with tempfile.TemporaryDirectory(prefix=f"{NAME}-deno-") as temporary:
        verifier = js_helpers(Path(temporary))
        source = (JS / "src" / "index.ts").as_uri()
        run("deno", "eval", f"import {{verify}} from '{verifier}'; import * as api from '{source}'; verify(api);", cwd=JS)
    export("js-package", [tarball])


def jsr_package():
    """Validate and archive only the exact JSR publication inputs."""
    artifact_directory()
    shutil.copyfile(ROOT / "README.md", JS / "README.md")
    shutil.copytree(ROOT / "LICENSES", JS / "LICENSES", dirs_exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=f"{NAME}-jsr-") as temporary:
        stage = Path(temporary) / "source"
        stage.mkdir()
        for name in ("src", "README.md", "LICENSES", "package.json", "jsr.json"):
            source = JS / name
            if source.is_dir():
                shutil.copytree(source, stage / name)
            else:
                shutil.copyfile(source, stage / name)
        run("deno", "publish", "--dry-run", "--allow-dirty", cwd=stage)
        output = Path(temporary) / f"{NAME}-{VERSION}-jsr.tar.gz"
        with output.open("wb") as stream:
            with gzip.GzipFile(filename="", fileobj=stream, mode="wb", mtime=0) as compressed:
                with tarfile.open(fileobj=compressed, mode="w") as archive:
                    for path in sorted(stage.rglob("*")):
                        if not path.is_file():
                            continue
                        relative = path.relative_to(stage)
                        # Deno may create its own cache/lock; publish only the selected inputs.
                        if relative.parts[0] not in {"src", "README.md", "LICENSES", "package.json", "jsr.json"}:
                            continue
                        data = path.read_bytes()
                        info = tarfile.TarInfo(relative.as_posix())
                        info.size, info.mode, info.mtime = len(data), 0o644, 0
                        archive.addfile(info, io.BytesIO(data))
        export("jsr-package", [output])


def js_manager(manager):
    # Additional managers consume a previous verified tarball from this exact source.
    directory = artifact_directory()
    receipt = json.loads((directory / "js-package.json").read_text())
    tarball = directory / npm_tarball().name
    if receipt["commit"] != os.environ["CI_COMMIT_SHA"] or receipt["artifacts"].get(tarball.name) != digest(tarball):
        raise ValueError("JavaScript artifact identity differs from its receipt")
    pack_check(manager, tarball)
    export(f"js-{manager}", [tarball])


def dependencies(directory, kind):
    source = os.environ.get("DEPENDENCY_MANIFEST")
    expected = os.environ.get("DEPENDENCY_MANIFEST_SHA256")
    if not source and not expected:
        return []
    if not source or not expected or digest(source) != expected:
        raise ValueError("Dependency manifest SHA-256 mismatch")
    manifest = json.loads(Path(source).read_text())
    if manifest.get("schema") != 1:
        raise ValueError("Dependency manifest requires schema 1")
    result = []
    for item in manifest["artifacts"]:
        if item["kind"] != kind:
            continue
        source = Path(item["path"])
        payload = source.read_bytes()
        if hashlib.sha256(payload).hexdigest() != item["sha256"]:
            raise ValueError("Dependency artifact SHA-256 mismatch")
        copied = directory / source.name
        preserve(copied, payload)
        result.append((item["name"], copied))
    return result


def python_package():
    artifact_directory()
    with tempfile.TemporaryDirectory(prefix=f"{NAME}-python-") as temporary:
        scratch = Path(temporary)
        output = scratch / "dist"
        run("uv", "build", "py", "--out-dir", output)
        wheels, sdists = list(output.glob("*.whl")), list(output.glob("*.tar.gz"))
        if len(wheels) != 1 or len(sdists) != 1:
            raise ValueError("Expected exactly one Python wheel and sdist")
        venv = scratch / "consumer"
        run("uv", "venv", venv)
        python = venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        wheels_to_install = [path for _, path in dependencies(scratch, "wheel")]
        run("uv", "pip", "install", "--python", python, *wheels_to_install, wheels[0])
        run(python, ROOT / "py/scripts/conformance.py", cwd=scratch)
        python_consumer(python, wheels[0], sdists[0], scratch)
        export("python-package", [*wheels, *sdists])


def python_consumer(python, wheel, sdist, cwd):
    """Verify wheel/sdist license inventories, metadata and installed entrypoints."""
    expected = {path.name: path.read_bytes() for path in (ROOT / "LICENSES").iterdir() if path.is_file()}
    with zipfile.ZipFile(wheel) as archive:
        files = archive.namelist()
        if f"{NAME}/py.typed" not in files:
            raise ValueError("Wheel is missing py.typed")
        metadata_paths = [path for path in files if path.endswith(".dist-info/METADATA")]
        if len(metadata_paths) != 1:
            raise ValueError("Expected one wheel distribution")
        fields = BytesParser().parsebytes(archive.read(metadata_paths[0]))
        if fields["Name"] != NAME or fields["Version"] != VERSION or fields["License-Expression"] != PACKAGE["license"]:
            raise ValueError("Wheel identity or license expression differs")
        licenses = {path.rsplit("/", 1)[1]: archive.read(path) for path in files if "/LICENSES/" in path}
        if licenses != expected:
            raise ValueError("Wheel license inventory or texts differ")
    with tarfile.open(sdist, "r:gz") as archive:
        licenses = {member.name.rsplit("/", 1)[1]: archive.extractfile(member).read()
                    for member in archive.getmembers() if member.isfile() and "/LICENSES/" in member.name}
        if licenses != expected:
            raise ValueError("Source distribution license inventory or texts differ")
    entrypoint = Path(python).parent / (NAME + (".exe" if os.name == "nt" else ""))
    for command in ([python, "-m", NAME], [entrypoint]):
        output = subprocess.check_output([*map(str, command), "--json", "normalize", " DE_Ch "], cwd=cwd, text=True)
        if json.loads(output) != {"result": "de-ch"}:
            raise ValueError("Installed command-line output differs")
    print(f"Python {NAME}: installed module, console entrypoint, wheel/sdist licenses and metadata passed")


def typst_package():
    artifact_directory()
    run("uv", "run", "--with", "typst==0.15.0", "python", "scripts/package-typst.py")
    export("typst-package", [ROOT / "dist" / f"{NAME}-{VERSION}-typst.tar.gz"])


def rust_package():
    artifact_directory()
    run("cargo", "package", "--locked")
    target = Path(os.environ.get("CARGO_TARGET_DIR", ROOT / "target"))
    export("rust-package", [target / "package" / f"{NAME}-{VERSION}.crate"])


def rust_dependencies():
    """Pre-publication integration only; registry packaging remains a separate check."""
    artifact_directory()
    with tempfile.TemporaryDirectory(prefix=f"{NAME}-rust-dependencies-") as temporary:
        scratch = Path(temporary)
        crates = dependencies(scratch, "crate")
        if not crates:
            raise ValueError("rust-dependencies requires exact verified sibling crate artifacts")
        source = scratch / "source"
        shutil.copytree(ROOT, source, ignore=shutil.ignore_patterns(".git", "target", "node_modules", "dist"))
        patches = ["[patch.crates-io]"]
        for name, crate in crates:
            destination = scratch / (name + "-dependency")
            destination.mkdir()
            with tarfile.open(crate, "r:gz") as archive:
                archive.extractall(destination, filter="data")
            roots = list(destination.iterdir())
            if len(roots) != 1 or not roots[0].is_dir():
                raise ValueError("Expected one crate package root")
            metadata = tomllib.loads((roots[0] / "Cargo.toml").read_text())["package"]
            if metadata["name"] != name:
                raise ValueError("Dependency crate name differs from the manifest")
            patches.append(f"{json.dumps(name)} = {{path = {json.dumps(str(roots[0]))}}}")
        config = scratch / "dependencies.toml"
        config.write_text("\n".join(patches) + "\n")
        # Only this private scratch lock is changed. Published source keeps registry resolution.
        run("cargo", "--config", config, "generate-lockfile", "--offline", cwd=source)
        run("cargo", "fmt", "--check", cwd=source)
        run("cargo", "--config", config, "clippy", "--locked", "--all-targets", "--", "-D", "warnings", cwd=source)
        run("cargo", "--config", config, "test", "--locked", cwd=source)
        export("rust-dependencies", [])


def published(channel):
    with tempfile.TemporaryDirectory(prefix=f"{NAME}-{channel}-") as temporary:
        scratch = Path(temporary)
        if channel in {"npm", "jsr"}:
            verifier = js_helpers(scratch)
            (scratch / "package.json").write_text('{"private":true,"type":"module"}\n')
        if channel == "npm":
            run("npm", "install", "--ignore-scripts", "--no-audit", "--no-fund", f"@corbet-labs/{NAME}@{VERSION}", cwd=scratch)
            run("bun", "consumer.mjs", cwd=scratch)
        elif channel == "jsr":
            run("deno", "eval", "--min-dep-age=0", f"import * as api from 'jsr:@corbet-labs/{NAME}@{VERSION}'; import {{verify}} from '{verifier}'; verify(api);", cwd=scratch)
        elif channel == "python":
            venv = scratch / "consumer"
            run("uv", "venv", venv)
            python = venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
            run("uv", "pip", "install", "--python", python, f"{NAME}=={VERSION}")
            run(python, ROOT / "py/scripts/conformance.py", cwd=scratch)
            run(python, "-m", NAME, "--help", cwd=scratch)


CHECKS = {
    "metadata": metadata,
    "javascript": javascript,
    "js-package": js_package,
    "jsr-package": jsr_package,
    "js-pnpm": lambda: js_manager("pnpm"),
    "js-yarn": lambda: js_manager("yarn"),
    "js-bun": lambda: js_manager("bun"),
    "python-package": python_package,
    "typst-package": typst_package,
    "rust-package": rust_package,
    "rust-dependencies": rust_dependencies,
    "published-npm": lambda: published("npm"),
    "published-jsr": lambda: published("jsr"),
    "published-python": lambda: published("python"),
}

TOOLS = {
    "metadata": [("python3", "--version")],
    "javascript": [("node", "--version"), ("bun", "--version")],
    "js-package": [("node", "--version"), ("bun", "--version"), ("npm", "--version"), ("deno", "--version")],
    "jsr-package": [("python3", "--version"), ("deno", "--version")],
    "python-package": [("python3", "--version"), ("uv", "--version")],
    "typst-package": [("python3", "--version"), ("uv", "--version")],
    "rust-package": [("rustc", "--version"), ("cargo", "--version")],
    "rust-dependencies": [("rustc", "--version"), ("cargo", "--version")],
}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("check", choices=CHECKS)
    arguments = parser.parse_args()
    started = time.monotonic()
    for command in TOOLS.get(arguments.check, []):
        run(*command)
    if arguments.check in {"metadata", "javascript", "js-package", "jsr-package", "js-pnpm", "js-yarn", "js-bun", "python-package", "typst-package"}:
        # Build tools write generated files and dependency trees. Keep ccid's
        # verified input tree unchanged so successful Rust freshness is reusable.
        with tempfile.TemporaryDirectory(prefix=f"{NAME}-check-") as temporary:
            source = Path(temporary) / NAME
            shutil.copytree(ROOT, source, ignore=shutil.ignore_patterns(".git", "target", "node_modules", "dist"))
            ROOT = source
            JS = ROOT / "js" / "@corbet-labs" / NAME
            CHECKS[arguments.check]()
    else:
        CHECKS[arguments.check]()
    print(json.dumps({"check": arguments.check, "status": "passed", "seconds": round(time.monotonic() - started, 3)}))
