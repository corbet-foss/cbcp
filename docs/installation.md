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

The npm and JSR packages ship pure `.ts` sources with zero dependencies. Bun,
Deno and TypeScript-aware bundlers import them directly; plain Node.js refuses
to strip types inside `node_modules`, so Node.js consumers need a bundler or
TypeScript loader. Python 3.10+. Typst consumers vendor `typst/cbcp.typ`
alongside its notice, following the family snapshot practice.

Every release publishes the same version to crates.io, npm, JSR and PyPI. The
Typst package is not on Typst Universe; each release run retains a checked
`@local` archive (`cbcp-X.Y.Z-typst.tar.gz`) as a workflow artifact.
