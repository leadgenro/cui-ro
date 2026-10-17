import { test, before, after } from "node:test";
import assert from "node:assert/strict";
import { createServer } from "node:http";
import { lookup, LeadgenError } from "../leadgen.js";

// The optional lookup helper, against a local fake server (no network).
const seen = [];
let server;
let base;

before(async () => {
  server = createServer((req, res) => {
    const url = new URL(req.url, "http://x");
    seen.push({ path: url.pathname, query: Object.fromEntries(url.searchParams), key: req.headers["x-api-key"] ?? null });
    const spent = req.headers["x-api-key"] === "spent";
    const body = spent
      ? { error: "daily_limit_reached", message: "25 lookups a day", get_a_key: "https://leadgen.adrianhomelab.com/start" }
      : { results: [{ cui: url.searchParams.get("query"), companyName: "TEST SRL" }] };
    res.writeHead(spent ? 429 : 200, { "Content-Type": "application/json" });
    res.end(JSON.stringify(body));
  });
  await new Promise((r) => server.listen(0, "127.0.0.1", r));
  base = `http://127.0.0.1:${server.address().port}`;
});

after(() => new Promise((r) => server.close(r)));

test("lookup without a key", async () => {
  seen.length = 0;
  const data = await lookup("RO 0002816464", { baseUrl: base });
  assert.equal(data.results[0].cui, "2816464");
  assert.deepEqual(seen, [{ path: "/lookup_business", query: { query: "2816464", max_results: "1" }, key: null }]);
});

test("lookup with a key", async () => {
  seen.length = 0;
  await lookup("14399840", { apiKey: "lg_test", baseUrl: base });
  assert.equal(seen[0].key, "lg_test");
});

test("an invalid CUI never calls", async () => {
  seen.length = 0;
  await assert.rejects(lookup("14399841", { baseUrl: base }), RangeError);
  assert.equal(seen.length, 0);
});

test("HTTP errors carry status and body", async () => {
  await assert.rejects(lookup("14399840", { apiKey: "spent", baseUrl: base }), (e) => {
    assert.ok(e instanceof LeadgenError);
    assert.equal(e.status, 429);
    assert.equal(e.body.error, "daily_limit_reached");
    assert.match(e.message, /25 lookups a day/);
    return true;
  });
});
