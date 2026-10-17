"""The optional lookup helper, against a local fake server (no network)."""
import json
import os
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cui_ro.leadgen import LeadgenError, lookup  # noqa: E402


class Fake(BaseHTTPRequestHandler):
    seen = []

    def do_GET(self):
        url = urlparse(self.path)
        Fake.seen.append({"path": url.path, "query": parse_qs(url.query),
                          "key": self.headers.get("X-API-Key")})
        if self.headers.get("X-API-Key") == "spent":
            status, body = 429, {"error": "daily_limit_reached", "message": "25 lookups a day",
                                 "get_a_key": "https://leadgen.adrianhomelab.com/start"}
        else:
            q = parse_qs(url.query)["query"][0]
            status, body = 200, {"results": [{"cui": q, "companyName": "TEST SRL"}]}
        raw = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def log_message(self, *args):
        pass


class Lookup(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = HTTPServer(("127.0.0.1", 0), Fake)
        cls.base = f"http://127.0.0.1:{cls.server.server_port}"
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def setUp(self):
        Fake.seen.clear()

    def test_without_key(self):
        data = lookup("RO 0002816464", base_url=self.base)
        self.assertEqual(data["results"][0]["cui"], "2816464")
        self.assertEqual(Fake.seen, [{"path": "/lookup_business",
                                      "query": {"query": ["2816464"], "max_results": ["1"]}, "key": None}])

    def test_with_key(self):
        lookup("14399840", api_key="lg_test", base_url=self.base)
        self.assertEqual(Fake.seen[0]["key"], "lg_test")

    def test_invalid_cui_never_calls(self):
        with self.assertRaises(ValueError):
            lookup("14399841", base_url=self.base)
        self.assertEqual(Fake.seen, [])

    def test_http_error(self):
        with self.assertRaises(LeadgenError) as cm:
            lookup("14399840", api_key="spent", base_url=self.base)
        self.assertEqual(cm.exception.status, 429)
        self.assertEqual(cm.exception.body["error"], "daily_limit_reached")
        self.assertIn("25 lookups a day", str(cm.exception))

    def test_core_import_does_not_load_the_helper(self):
        import subprocess
        code = "import sys, cui_ro; cui_ro.is_valid('19'); print('cui_ro.leadgen' in sys.modules)"
        out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                             cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))), check=True)
        self.assertEqual(out.stdout.strip(), "False")


if __name__ == "__main__":
    unittest.main()
