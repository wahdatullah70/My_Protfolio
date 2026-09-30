import importlib.util
import pathlib
import sys
import unittest

MODULE_PATH = pathlib.Path(__file__).resolve().parents[1] / "slurm_ops.py"
spec = importlib.util.spec_from_file_location("slurm_ops", MODULE_PATH)
slurm_ops = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = slurm_ops
spec.loader.exec_module(slurm_ops)


class SlurmOpsTests(unittest.TestCase):
    def test_parse_nodes(self):
        nodes = slurm_ops.parse_nodes("n1|idle|16|64000|(null)\nn2|drain|32|128000|gpu:a100:1\n")
        self.assertEqual(len(nodes), 2)
        self.assertEqual(nodes[0].name, "n1")
        self.assertEqual(nodes[1].state, "drain")

    def test_parse_jobs(self):
        jobs = slurm_ops.parse_jobs("42|compute|demo|user|RUNNING|00:01:00|1|n1\n")
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0].job_id, "42")
        self.assertEqual(jobs[0].state, "running")

    def test_warning_report(self):
        nodes = slurm_ops.parse_nodes("n1|idle|16|64000|(null)\nn2|drain|32|128000|(null)\n")
        jobs = slurm_ops.parse_jobs(
            "42|compute|demo|user|RUNNING|00:01:00|1|n1\n"
            "43|compute|blocked|user|PENDING|00:00:00|2|Resources\n"
        )
        report = slurm_ops.build_report(nodes, jobs, "test")
        self.assertEqual(report["status"], "warning")
        self.assertEqual(report["summary"]["node_alerts"], 1)
        self.assertEqual(report["summary"]["job_alerts"], 1)

    def test_healthy_report(self):
        nodes = slurm_ops.parse_nodes("n1|idle|16|64000|(null)\n")
        jobs = slurm_ops.parse_jobs("42|compute|demo|user|RUNNING|00:01:00|1|n1\n")
        report = slurm_ops.build_report(nodes, jobs, "test")
        self.assertEqual(report["status"], "healthy")
        self.assertEqual(report["summary"]["node_alerts"], 0)
        self.assertEqual(report["summary"]["job_alerts"], 0)


if __name__ == "__main__":
    unittest.main()
