"""
Standalone Audit Script
Run a full bias audit from the command line and print/save results.

Usage:
    python run_audit.py                          # demo audit
    python run_audit.py --model models/my.pkl   # audit your model
    python run_audit.py --samples 10000         # larger dataset
    python run_audit.py --output report.json    # save report
"""

import argparse
import json
import pickle
import sys
from pathlib import Path
from data_generator import generate_synthetic_data
from audit_engine import run_audit

SEVERITY_COLORS = {
    "CRITICAL": "\033[91m",  # red
    "HIGH":     "\033[93m",  # yellow
    "MEDIUM":   "\033[33m",  # orange-ish
    "LOW":      "\033[92m",  # green
    "PASS":     "\033[92m",
    "MINIMAL":  "\033[92m",
}
RESET = "\033[0m"
BOLD  = "\033[1m"


def color(text, severity):
    c = SEVERITY_COLORS.get(severity, "")
    return f"{c}{text}{RESET}"


def print_report(report):
    print(f"\n{'='*60}")
    print(f"{BOLD}  Fair Loan AI — Bias Audit Report{RESET}")
    print(f"{'='*60}")
    print(f"  Audit ID  : {report['audit_id']}")
    print(f"  Timestamp : {report['timestamp']}")
    print(f"  Samples   : {report['dataset']['total_samples']:,}")

    risk = report['risk_score']
    level = report['risk_level']
    rbi = "✓ YES" if report['rbi_compliant'] else "✗ NO"
    print(f"\n  {BOLD}Risk Score : {color(f'{risk}/100  ({level})', level)}{RESET}")
    print(f"  RBI Compliant: {rbi}")

    print(f"\n{'─'*60}")
    print(f"  {BOLD}Overall Model Metrics{RESET}")
    om = report['overall_metrics']
    print(f"  Accuracy     : {om['accuracy']:.2%}")
    print(f"  Approval Rate: {om['approval_rate']:.2%}")
    print(f"  F1 Score     : {om['f1_score']:.2%}")
    print(f"  Total Approved / Rejected: {om['total_approved']:,} / {om['total_rejected']:,}")

    print(f"\n{'─'*60}")
    print(f"  {BOLD}Bias Analysis by Attribute{RESET}")

    for attr, data in report['bias_analysis'].items():
        sev = data['severity']
        print(f"\n  [{color(sev, sev)}] {attr.upper()}")
        print(f"  {data['summary']}")
        print(f"  {'Group':<20} {'Approval':>10} {'DI Ratio':>10} {'Status':>12}")
        print(f"  {'─'*55}")
        for group, val in data['disparate_impact'].items():
            status = "⚠ FLAGGED" if val['flagged'] else "✓ OK"
            status_colored = color(status, "CRITICAL" if val['flagged'] else "PASS")
            print(f"  {str(group):<20} {val['approval_rate']:>9.1%} {val['di_ratio']:>10.3f}  {status_colored}")

    print(f"\n{'─'*60}")
    print(f"  {BOLD}Mitigation Suggestions{RESET}")
    for m in report['mitigation_suggestions']:
        pri_color = color(f"[{m['priority']}]", "CRITICAL" if m['priority'] == "HIGH" else "MEDIUM")
        print(f"  {pri_color} {m['technique']} ({m['attribute']})")
        print(f"       {m['description']}")
        if 'fairlearn_api' in m:
            print(f"       API: {m['fairlearn_api']}")
        print()

    print(f"\n{'─'*60}")
    print(f"  {BOLD}Regulatory Notes{RESET}")
    for note in report['regulatory_notes']:
        print(f"  • {note}")
    print(f"\n{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(description="Fair Loan AI — CLI Bias Auditor")
    parser.add_argument("--model", type=str, help="Path to .pkl model file")
    parser.add_argument("--samples", type=int, default=5000, help="Number of synthetic samples")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--output", type=str, help="Save report to JSON file")
    parser.add_argument("--quiet", action="store_true", help="Only output JSON")
    args = parser.parse_args()

    print("Generating synthetic data...")
    df = generate_synthetic_data(n_samples=args.samples, seed=args.seed)

    model = None
    model_type = "demo"

    if args.model:
        model_path = Path(args.model)
        if not model_path.exists():
            print(f"Error: Model file not found: {args.model}")
            sys.exit(1)
        print(f"Loading model: {args.model}")
        with open(model_path, "rb") as f:
            model = pickle.load(f)
        model_type = "uploaded"

    print("Running bias audit...")
    report = run_audit(df, model=model, model_type=model_type)

    if not args.quiet:
        print_report(report)

    if args.output:
        with open(args.output, "w") as f:
            json.dump(report, f, indent=2)
        print(f"Report saved to: {args.output}")
    else:
        if args.quiet:
            print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
