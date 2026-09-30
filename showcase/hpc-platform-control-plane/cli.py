#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

from hpcops import load_fixture_report, prometheus_metrics


def markdown(report: dict) -> str:
    s = report["summary"]
    lines = [
        "# HPC Platform Control Plane Report",
        "",
        f"Status: **{report['status'].upper()}**",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "|---|---:|",
    ]
    for key, value in s.items():
        lines.append(f"| {key} | {value} |")
    lines += ["", "## Incidents", ""]
    if not report["incidents"]:
        lines.append("No incidents detected.")
    else:
        lines += ["| Severity | Type | Subject | Message |", "|---|---|---|---|"]
        for item in report["incidents"]:
            lines.append(f"| {item['severity']} | {item['type']} | {item['subject']} | {item['message']} |")
    return "\n".join(lines) + "\n"


def main():
    p = argparse.ArgumentParser(description="Generate an HPC operations report from deterministic fixtures")
    p.add_argument("--fixture-dir", type=Path, default=Path(__file__).parent / "fixtures")
    p.add_argument("--policy", type=Path, default=Path(__file__).parent / "policy.json")
    p.add_argument("--json-out", type=Path)
    p.add_argument("--markdown-out", type=Path)
    p.add_argument("--metrics-out", type=Path)
    p.add_argument("--pretty", action="store_true")
    args = p.parse_args()

    report = load_fixture_report(args.fixture_dir, args.policy)
    text = json.dumps(report, indent=2 if args.pretty else None)
    print(text)
    if args.json_out:
        args.json_out.write_text(json.dumps(report, indent=2) + "\n")
    if args.markdown_out:
        args.markdown_out.write_text(markdown(report))
    if args.metrics_out:
        args.metrics_out.write_text(prometheus_metrics(report))
    raise SystemExit(0 if report["status"] == "healthy" else 2)


if __name__ == "__main__":
    main()
