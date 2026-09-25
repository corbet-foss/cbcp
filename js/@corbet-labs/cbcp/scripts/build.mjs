// Build runnable packages; consumers never need a TypeScript loader.
// Plain Node.js refuses to strip types inside node_modules, so the npm package
// ships compiled ESM, CommonJS and declarations. JSR keeps publishing src/*.ts.
import { copyFileSync, mkdirSync, readFileSync, rmSync } from 'node:fs';
import { spawnSync } from 'node:child_process';

rmSync('dist', { recursive: true, force: true });
mkdirSync('dist', { recursive: true });
const types = spawnSync('node', ['node_modules/typescript/bin/tsc', '-p', 'tsconfig.build.json'], { stdio: 'inherit' });
if (types.status !== 0) process.exit(types.status ?? 1);
// The declarations only export functions, so the same text types both modes.
copyFileSync('dist/types/index.d.ts', 'dist/types/index.d.cts');
// cbcp has no dependencies and no Node APIs: the ESM build also serves browsers.
for (const [file, format] of [['index.js', 'esm'], ['index.cjs', 'cjs']]) {
    const result = await Bun.build({
        entrypoints: ['src/index.ts'],
        target: 'browser', format, packages: 'external',
        minify: false,
    });
    if (!result.success) throw new AggregateError(result.logs, `Failed to build ${file}`);
    if (result.outputs.length !== 1) throw new Error(`Unexpected outputs for ${file}`);
    await Bun.write(`dist/${file}`, result.outputs[0]);
}
const pkg = JSON.parse(readFileSync('package.json', 'utf8'));
console.log(`Built ${pkg.name}@${pkg.version}: ESM, CommonJS, declarations`);
