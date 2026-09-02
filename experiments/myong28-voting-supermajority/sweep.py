# SPDX-License-Identifier: Apache-2.0
"""Sweep the voting threshold to locate the boundary where outcomes flip.

Example::

    python sweep.py
"""

import re
import subprocess
import tempfile
from pathlib import Path

BASE = Path(__file__).parent / "voting_supermajority.yaml"
THRESHOLDS = [0.5, 0.5001, 0.6, 0.6666, 0.6667, 0.67, 0.7, 0.85]


def run(threshold: float) -> list[str]:
    """Run the voting scenario at `threshold` and return per-round results."""
    text = BASE.read_text()
    text = re.sub(r"threshold: [\d.]+", f"threshold: {threshold}", text)
    with tempfile.TemporaryDirectory() as tmp:
        cfg = Path(tmp) / "s.yaml"
        trace = Path(tmp) / "t.jsonl"
        cfg.write_text(re.sub(r"trace: .*", f"trace: {trace}", text))
        subprocess.run(["nest", "run", str(cfg)], capture_output=True, check=True)
        return sorted(set(re.findall(r'"msg":"(result:[^"]*)"', trace.read_text())))


if __name__ == "__main__":
    print(f"{'threshold':>10} | {'passed':>6} | rounds")
    for t in THRESHOLDS:
        results = run(t)
        passed = sum("passed" in r for r in results)
        detail = " ".join(r.split(":")[2][0].upper() for r in results)
        print(f"{t:>10} | {passed:>4}/5 | {detail}")
