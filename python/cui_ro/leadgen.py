"""Optional: look a CUI up in Leadgen's public REST API (registry record, ANAF status).

This module is separate from the validator on purpose: ``import cui_ro`` never
touches the network, and nothing here runs unless you call ``lookup``.

    from cui_ro.leadgen import lookup
    data = lookup("RO 14399840")                 # or lookup(cui, api_key="lg_...")
    for firm in data["results"]:
        print(firm["cui"], firm["companyName"])

Free limits (https://leadgen.adrianhomelab.com/docs): 5 lookups a day per IP
without a key, 25 a day with a free key from https://leadgen.adrianhomelab.com/start;
the day resets at 00:00 UTC. The CUI is checked locally first, so an invalid
one never spends a lookup.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request

from . import __version__, is_valid, normalize

BASE_URL = "https://leadgen.adrianhomelab.com"


class LeadgenError(Exception):
    """An HTTP error from the API; ``status`` and the decoded ``body`` are attached.
    429 means the daily limit is reached; the body says when it resets and how to get a key."""

    def __init__(self, status: int, body):
        self.status = status
        self.body = body
        detail = (body.get("message") or body.get("error") or body.get("detail")) if isinstance(body, dict) else body
        super().__init__(f"Leadgen API returned HTTP {status}: {detail}")


def lookup(cui, api_key: str | None = None, *, timeout: float = 30, base_url: str = BASE_URL) -> dict:
    """GET /lookup_business?query=<cui> and return the decoded JSON.

    ``api_key`` is sent as the X-API-Key header when given. Raises ValueError
    for an invalid CUI (before any request) and LeadgenError for an HTTP error.
    """
    if not is_valid(cui):
        raise ValueError(f"not a valid CUI: {cui!r}")
    query = urllib.parse.urlencode({"query": normalize(cui), "max_results": 1})
    req = urllib.request.Request(f"{base_url.rstrip('/')}/lookup_business?{query}")
    req.add_header("Accept", "application/json")
    req.add_header("User-Agent", f"cui-ro/{__version__} (python)")
    if api_key:
        req.add_header("X-API-Key", api_key)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace")
        try:
            body = json.loads(raw)
        except ValueError:
            body = raw
        raise LeadgenError(e.code, body) from None
