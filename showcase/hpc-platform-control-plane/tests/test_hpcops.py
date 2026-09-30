import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("hpcops", ROOT / "hpcops.py")
hpcops = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = hpcops
spec.loader.exec_module(hpcops)


class HPCOpsTests(unittest.TestCase):
    def test_elapsed_seconds(self):
        self.assertEqual(hpcops.elapsed_seconds("00:23:00"), 1380)
        self.assertEqual(hpcops.elapsed_seconds("1-01:00:00"), 90000)

    def test_fixture_report_detects_incidents(self):
        report = hpcops.load_fixture_report(ROOT / "fixtures", ROOT / "policy.json")
        self.assertEqual(report["status"], "critical")
        self.assertEqual(report["summary"]["nodes_total"], 4)
        self.assertEqual(report["summary"]["jobs_running"], 2)
        self.assertEqual(report["summary"]["jobs_pending"], 1)
        types = {i["type"] for i in report["incidents"]}
        self.assertTrue({"node_state", "pending_job", "job_state", "accounting_failure", "memory_pressure", "disk_pressure", "gpu_temperature"}.issubset(types))

    def test_prometheus_output(self):
        report = hpcops.load_fixture_report(ROOT / "fixtures", ROOT / "policy.json")
        metrics = hpcops.prometheus_metrics(report)
        self.assertIn("hpc_nodes_total 4", metrics)
        self.assertIn("hpc_jobs_pending 1", metrics)
        self.assertIn("hpc_incidents_critical", metrics)


if __name__ == "__main__":
    unittest.main()
