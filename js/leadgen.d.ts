export const BASE_URL: string;

export class LeadgenError extends Error {
  /** HTTP status: 429 when the daily limit is reached, 401 for a bad key. */
  status: number;
  /** The decoded response body (it carries `get_a_key` on 401/402/429). */
  body: unknown;
}

export interface LookupOptions {
  /** A free key from https://leadgen.adrianhomelab.com/start, sent as X-API-Key. */
  apiKey?: string;
  baseUrl?: string;
  signal?: AbortSignal;
}

/** GET /lookup_business?query=<cui>. Rejects with RangeError for an invalid CUI (no request made). */
export function lookup(cui: string | number, options?: LookupOptions): Promise<any>;
