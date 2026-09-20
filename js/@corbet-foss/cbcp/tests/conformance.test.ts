import { describe, it, expect } from 'bun:test';
import { readFileSync, readdirSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import * as cbcp from '../src/index.ts';

const FNS: Record<string, (input: unknown) => unknown> = {
    normalize_locale_id: (i) => cbcp.normalizeLocaleId(i as string),
    to_bcp47: (i) => cbcp.toBcp47(i as string),
    base_language: (i) => cbcp.baseLanguage(i as string),
    is_well_formed: (i) => cbcp.isWellFormed(i as string),
    locale_eq: (i) => cbcp.localeEq((i as string[])[0]!, (i as string[])[1]!),
    deepl_source: (i) => cbcp.deeplSource(i as string),
    deepl_target: (i) => cbcp.deeplTarget(i as string),
    google_language: (i) => cbcp.googleLanguage(i as string),
};

const dir = join(dirname(fileURLToPath(import.meta.url)), '..', '..', '..', '..', 'tests', 'vectors');

for (const file of readdirSync(dir).filter((f) => f.endsWith('.json')).sort()) {
    const vectors = JSON.parse(readFileSync(join(dir, file), 'utf8'));
    describe(file, () => {
        for (const v of vectors) {
            it(v.name, () => {
                expect(FNS[v.fn]!(v.input)).toEqual(v.expected);
            });
        }
    });
}
