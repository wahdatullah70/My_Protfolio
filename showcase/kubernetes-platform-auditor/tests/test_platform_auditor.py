import importlib.util
import pathlib
import sys
import unittest

MODULE_PATH = pathlib.Path(__file__).resolve().parents[1] / "platform_auditor.py"
spec = importlib.util.spec_from_file_location("platform_auditor", MODULE_PATH)
platform_auditor = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = platform_auditor
spec.loader.exec_module(platform_auditor)


class PlatformAuditorTests(unittest.TestCase):
    def test_running_but_unready_pod_is_unhealthy(self):
        pod = {"metadata": {"namespace": "default", "name": "api"}, "status": {"phase": "Running", "containerStatuses": [{"name": "api", "ready": False, "restartCount": 0, "state": {"running": {}}}]}}
        result = platform_auditor.pod_status(pod)
        self.assertFalse(result["healthy"])
        self.assertIn("containers_not_ready", result["reasons"])

    def test_crashloop_and_restarts_are_detected(self):
        pod = {"metadata": {"namespace": "default", "name": "worker"}, "status": {"phase": "Running", "containerStatuses": [{"name": "worker", "ready": False, "restartCount": 8, "state": {"waiting": {"reason": "CrashLoopBackOff"}}}]}}
        result = platform_auditor.pod_status(pod, restart_threshold=5)
        self.assertIn("CrashLoopBackOff", result["waiting_reasons"])
        self.assertIn("high_restarts=8", result["reasons"])

    def test_node_pressure_is_reported(self):
        node = {"metadata": {"name": "worker"}, "status": {"conditions": [{"type": "Ready", "status": "True"}, {"type": "DiskPressure", "status": "True"}], "nodeInfo": {}}}
        result = platform_auditor.node_status(node)
        self.assertTrue(result["ready"])
        self.assertEqual(result["pressure_conditions"], ["DiskPressure"])

    def test_build_report_warning(self):
        nodes = {"items": [{"metadata": {"name": "n1"}, "status": {"conditions": [{"type": "Ready", "status": "True"}], "nodeInfo": {}}}]}
        pods = {"items": [{"metadata": {"namespace": "ns", "name": "p1"}, "status": {"phase": "Pending", "containerStatuses": []}}]}
        report = platform_auditor.build_report(nodes, pods)
        self.assertEqual(report["status"], "warning")
        self.assertEqual(report["summary"]["unhealthy_pods"], 1)


if __name__ == "__main__":
    unittest.main()
