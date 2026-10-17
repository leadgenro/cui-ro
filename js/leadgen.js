// Optional: look a CUI up in Leadgen's public REST API (registry record, ANAF status).
// Separate from the validator on purpose: importing "cui-ro" never touches the network.
// Free limits (https://leadgen.adrianhomelab.com/docs): 5 lookups a day per IP without a key,
// 25 a day with a free key from https://leadgen.adrianhomelab.com/start; resets 00:00 UTC.
// The CUI is checked locally first, so an invalid one never spends a lookup.
import { isValid, normalize } from "./index.js";

export const BASE_URL = "https://leadgen.adrianhomelab.com";

export class LeadgenError extends Error {
  constructor(status, body) {
    const detail = body && typeof body === "object" ? body.message ?? body.error ?? body.detail : body;
    super(`Leadgen API returned HTTP ${status}: ${detail}`);
    this.name = "LeadgenError";
    this.status = status;
    this.body = body;
  }
}

/** GET /lookup_business?query=<cui>; resolves to the decoded JSON. */
export async function lookup(cui, { apiKey, baseUrl = BASE_URL, signal } = {}) {
  if (!isValid(cui)) throw new RangeError(`not a valid CUI: ${JSON.stringify(cui)}`);
  const url = new URL("/lookup_business", baseUrl);
  url.searchParams.set("query", normalize(cui));
  url.searchParams.set("max_results", "1");
  const headers = { Accept: "application/json" };
  if (apiKey) headers["X-API-Key"] = apiKey;
  const res = await fetch(url, { headers, signal });
  const text = await res.text();
  let body;
  try {
    body = JSON.parse(text);
  } catch {
    body = text;
  }
  if (!res.ok) throw new LeadgenError(res.status, body);
  return body;
}
