import pathlib
import sys
import unittest

from fastapi.testclient import TestClient

PROJECT_DIR = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

import app  # noqa: E402


class InfraHealthApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app.app)

    def test_healthz(self):
        response = self.client.get("/healthz")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["service"], "Infra Health API")
        self.assertEqual(payload["version"], "1.1.0")

    def test_readyz(self):
        response = self.client.get("/readyz")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "ready")
        self.assertEqual(payload["checks"]["filesystem"], "ok")
        self.assertIsInstance(payload["checks"]["root_free_bytes"], int)

    def test_system_endpoint_shape(self):
        response = self.client.get("/api/v1/system")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        for key in ("timestamp", "service", "version", "hostname", "uptime_seconds", "load_average", "memory", "disk"):
            self.assertIn(key, payload)
        self.assertEqual(payload["service"], "Infra Health API")
        self.assertEqual(payload["disk"]["path"], "/")
        self.assertIn("used_percent", payload["disk"])


if __name__ == "__main__":
    unittest.main()
