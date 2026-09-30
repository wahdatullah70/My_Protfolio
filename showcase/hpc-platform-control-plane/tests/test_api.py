import importlib.util
import sys
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
spec = importlib.util.spec_from_file_location("app_module", ROOT / "app.py")
app_module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = app_module
spec.loader.exec_module(app_module)
client = TestClient(app_module.app)


class APITests(unittest.TestCase):
    def test_health(self):
        response = client.get("/healthz")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_ready(self):
        response = client.get("/readyz")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["mode"], "fixture")

    def test_cluster_report(self):
        response = client.get("/api/v1/cluster")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "critical")
        self.assertEqual(payload["summary"]["nodes_total"], 4)

    def test_incidents(self):
        response = client.get("/api/v1/incidents")
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.json()["incidents"]), 0)

    def test_metrics(self):
        response = client.get("/metrics")
        self.assertEqual(response.status_code, 200)
        self.assertIn("hpc_nodes_total 4", response.text)


if __name__ == "__main__":
    unittest.main()
