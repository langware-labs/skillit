"""Run eval cases for an activation rule.

Usage:
    python eval.py                     # Run from inside a rule directory
    python eval.py /path/to/rule_dir   # Run for a specific rule
"""

import sys
from pathlib import Path

# Add scripts dir to path for imports
SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from memory.rule_engine import ActivationRule


def main() -> int:
    if len(sys.argv) > 1:
        rule_dir = Path(sys.argv[1])
    else:
        rule_dir = Path(__file__).resolve().parent

    rule = ActivationRule(path=rule_dir)
    evaluation = rule.run_eval()
    print(evaluation.summary_table())
    return 0 if evaluation.all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
