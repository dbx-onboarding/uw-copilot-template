#!/usr/bin/env python3
"""
Print the resolved resource names for a given company_config.yaml.
Useful when setting up monitoring, documenting a deployment,
or verifying that config produces the expected names.

Usage:
    python scripts/generate_job_names.py
    python scripts/generate_job_names.py --config /path/to/config.yaml
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from uw_copilot.config import Config

parser = argparse.ArgumentParser(description="Print resolved resource names from company_config.yaml")
parser.add_argument("--config", help="Path to company_config.yaml (auto-discovered if omitted)")
args = parser.parse_args()

cfg = Config(args.config) if args.config else Config()
cfg.print_summary()

print("\nDAB Job Names:")
print(f"  uw-copilot-pipeline-setup")
print(f"  uw-copilot-intake")
print(f"  uw-copilot-infra-start")
print(f"  uw-copilot-infra-stop")
print(f"  uw-copilot-app-deploy")
