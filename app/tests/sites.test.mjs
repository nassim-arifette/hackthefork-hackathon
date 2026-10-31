import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import ts from 'typescript';

// Exercise the production TypeScript module without emitting build artifacts.
const source = readFileSync(new URL('../src/sites.ts', import.meta.url), 'utf8');
const compiled = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020 } }).outputText;
const api = {};
new Function('exports', compiled)(api);
const { makeSiteGeo, selectSupply, searchSites } = api;
const costs = { kappa: 0.12, forfait: 5, detour: 1.3, qualite: 0.1, tri: 180 };
const parcel = (dep, tonnes, lon = 2, lat = 48) => ({ dep, culture: 'ble', tonnes, surface: tonnes / 1.44, lon, lat });
const close = (actual, expected, tolerance = 1e-8) => assert.ok(Math.abs(actual - expected) <= tolerance, `${actual} ≠ ${expected}`);

test('gross collection is converted to net; a delivered purchase quote includes collection once', () => {
  const parcels = [parcel('77', 12)], prices = { '77': 100 };
  const geo = makeSiteGeo(parcels, prices, costs, [2, 48]);
  close(geo.collecte[0], 5 / 0.9);
  assert.equal(selectSupply(parcels, geo, costs, { volume: 10, price: 105, mode: 'collection' }).reached, false);
  const selection = selectSupply(parcels, geo, costs, { volume: 10, price: 106, mode: 'collection' });
  close(selection.farmPerT + selection.collectionPerT, 106);
  close(selection.landedPerT, 306);
  close(selection.budget, 12 * 306);
  assert.equal(selection.tonnes, 12); // Whole parcel, two tonnes of declared surplus.
  assert.deepEqual(selection.indices, [0]);
});

test('full-cost supply can prefer a farther parcel with a lower farm payment', () => {
  const parcels = [parcel('77', 10), parcel('78', 10, 2.5)], prices = { '77': 200, '78': 100 };
  const geo = makeSiteGeo(parcels, prices, costs, [2, 48]);
  const selection = selectSupply(parcels, geo, costs, { volume: 10, price: 1, mode: 'landed' });
  assert.deepEqual(selection.indices, [1]);
  close(selection.landedPerT, 100 + geo.collecte[1] + 200);
  assert.ok(selection.reached); // Delivered-price slider is irrelevant in this mode.
});

test('an off-grid current site is retained if no candidate improves its objective', async () => {
  const parcels = [parcel('77', 10, 2.123456, 48.654321)], prices = { '77': 100 };
  const current = makeSiteGeo(parcels, prices, costs, [2.123456, 48.654321]);
  const result = await searchSites(parcels, prices, costs, { volume: 10, price: 200, mode: 'collection' }, current);
  assert.deepEqual(result.site, current.site);
  assert.equal(result.improved, false);
});

test('unattainable volume is explicit and preserves the current site', async () => {
  const parcels = [parcel('77', 10)], prices = { '77': 100 };
  const current = makeSiteGeo(parcels, prices, costs, [2, 48]);
  const result = await searchSites(parcels, prices, costs, { volume: 11, price: 1000, mode: 'landed' }, current);
  assert.equal(result.selection.reached, false);
  assert.equal(result.selection.objective, Infinity);
  assert.deepEqual(result.site, current.site);
});

const json = (name) => JSON.parse(readFileSync(new URL(`../src/data/${name}.json`, import.meta.url), 'utf8'));
const real = json('parcels').map((p) => ({ dep: p[1], culture: p[2], surface: p[3], tonnes: p[6], lon: p[8], lat: p[9] }));
const prices = Object.fromEntries(json('thresholds').par_departement.map((d) => [d.dep, d.p_star]));
for (const volume of [300, 5000]) for (const price of [1500, 1600]) {
  test(`actual parcels: ${volume} t at ${price} €/t, one evaluator and no regression`, async () => {
    const current = makeSiteGeo(real, prices, costs, [2.95, 48.55]);
    const request = { volume, price, mode: 'collection' };
    const initial = selectSupply(real, current, costs, request);
    if (price === 1600) close(initial.tonnes, volume === 300 ? 309.7 : 5011.6, 1e-6);
    if (price === 1500) {
      const oldSite = volume === 300 ? [2.53429, 49.04568] : [3.12829, 48.55168];
      const previous = selectSupply(real, makeSiteGeo(real, prices, costs, oldSite), costs, request);
      assert.ok(previous.objective > initial.objective, 'Historical distance-only result is worse for eligible supply');
    }
    const result = await searchSites(real, prices, costs, request, current);
    assert.ok(result.selection.reached);
    assert.ok(result.selection.objective <= initial.objective + 1e-10);
    const evaluated = selectSupply(real, makeSiteGeo(real, prices, costs, result.site), costs, request);
    assert.deepEqual(result.selection.indices, evaluated.indices);
    close(result.selection.objective, evaluated.objective);
    close(result.selection.tonnes, result.selection.indices.reduce((s, i) => s + real[i].tonnes, 0));
  });
}

test('production full-cost search matches the independently reproduced Python benchmark', async () => {
  const benchmark = JSON.parse(readFileSync(new URL('../../experiments/sites/selected_parcels.json', import.meta.url), 'utf8'));
  const expected = benchmark.find((row) => row.scenario === 'landed_central' && row.parameters.target_t === 300).result;
  const current = makeSiteGeo(real, prices, costs, [2.95, 48.55]);
  const result = await searchSites(real, prices, costs, { volume: 300, price: 1600, mode: 'landed' }, current);
  close(result.site[0], expected.longitude);
  close(result.site[1], expected.latitude);
  close(result.selection.objective, expected.objective_eur_net_t);
  close(result.selection.tonnes, expected.expected_net_t);
  const raw = json('parcels');
  assert.deepEqual(result.selection.indices.map((i) => raw[i][0]), expected.selected_ids);
});
