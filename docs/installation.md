# Installation

| Environment | Command |
|---|---|
| Rust / Cargo | `cargo add cbcp` |
| Node.js / npm | `npm install @corbet-labs/cbcp` |
| pnpm | `pnpm add @corbet-labs/cbcp` |
| Yarn | `yarn add @corbet-labs/cbcp` |
| Bun | `bun add @corbet-labs/cbcp` |
| Deno | `deno add jsr:@corbet-labs/cbcp` |
| Python / pip | `python -m pip install cbcp` |
| Python / uv | `uv add cbcp` |

Both JavaScript packages have zero dependencies. The npm package ships compiled
ESM (`import`), CommonJS (`require`) and TypeScript declarations for both module
modes, so plain Node.js 20+, Bun, bundlers and browsers load it without a
TypeScript loader. The JSR package publishes the `.ts` sources, which Deno
imports directly. Python 3.10+. Typst consumers vendor `typst/cbcp.typ`
alongside its notice, following the family snapshot practice.

Every release publishes the same version to crates.io, npm, JSR and PyPI. The
Typst package is not on Typst Universe; each release run retains a checked
`@local` archive (`cbcp-X.Y.Z-typst.tar.gz`) as a workflow artifact.
