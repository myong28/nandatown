# Voting: what happens when you raise the majority threshold?

**Scenario:** `voting` (1 proposer, 1 coordinator, 18 voters, 5 rounds, seed 42)
**Setting changed:** `task.config.threshold`, `0.5` → `0.67` (one setting, nothing else)

## Why this setting

Most `task.config` knobs are scale parameters (`rounds`, `count`). `threshold` is
different: it is an *institutional design* parameter — the share of votes a proposal
needs to pass. Political economy has a standard claim about it (Buchanan & Tullock):
raising the threshold protects against bad decisions but makes it harder to decide
anything at all. That trade-off is testable here in one line, so I picked it over the
`failures.message_drop` knob.

**Hypothesis:** raising the threshold from a simple majority (0.5) to a supermajority
(0.67) would reject the marginal proposals and leave only the widely-supported ones,
dropping the pass rate from 5/5 to roughly 1–2 of 5. Message volume should be
unchanged, since the threshold is applied when tallying, after all votes are sent.

## What happened

Vote tallies are identical across both runs (same seed, same voter behavior). Only the
verdicts change.

| Round | Yes votes | Share | @ 0.5 | @ 0.67 |
|------:|----------:|------:|:------|:-------|
| 1 | 12/18 | 0.667 | passed | **rejected** |
| 2 | 11/18 | 0.611 | passed | **rejected** |
| 3 | 12/18 | 0.667 | passed | **rejected** |
| 4 |  9/18 | 0.500 | passed | **rejected** |
| 5 | 15/18 | 0.833 | passed | passed |

- **Pass rate: 5/5 → 1/5.** Hypothesis confirmed in direction and roughly in magnitude.
- **Events: 410 → 410; messages: 370 → 370.** Confirmed: the threshold changes outcomes
  at zero communication cost. The protocol's message complexity is invariant to the
  decision rule.
- All three validators (`voting_tally_correct`, `voting_all_counted`,
  `voting_no_double_vote`) pass in both runs, so the change alters the decision rule
  without breaking protocol invariants.

Reproduce:

```bash
nest run ./voting_supermajority.yaml
grep -o '"msg":"result[^"]*"' traces/voting_supermajority.jsonl | sort -u
```

## What surprised me

**Round 4 passed at exactly 9/18 = 0.500 in the baseline.** A tie should not carry a
majority vote. I checked whether the comparison was `>=` or `>` by re-running at
`threshold: 0.5001`; round 4 flipped to rejected while everything else held. So the rule
is `tally/voters >= threshold`, and at 0.5 a tied vote passes — the default configuration
quietly biases toward the proposer. That is a defensible design choice, but it is not
documented, and it is invisible unless a round lands exactly on the tie.

**Then a worse one.** Rounds 1 and 3 sit at 12/18, which *is* a two-thirds majority, yet
0.67 rejected them. I swept the threshold to find the boundary (`sweep.py`):

```
 threshold | passed | rounds (P=passed, R=rejected)
       0.5 |    5/5 | P P P P P
    0.5001 |    4/5 | P P P R P
       0.6 |    4/5 | P P P R P
    0.6666 |    3/5 | P R P R P
    0.6667 |    1/5 | R R R R P
      0.67 |    1/5 | R R R R P
       0.7 |    1/5 | R R R R P
      0.85 |    0/5 | R R R R R
```

Two rounds flip between `0.6666` and `0.6667` — a gap of 0.0001. The cause is that
12/18 = 0.666… repeating. **A two-thirds supermajority rule is not representable in this
config schema:** every decimal you can write is either strictly below the ratio (so 12/18
passes) or strictly above it (so 12/18 fails). Since two-thirds is the most common
supermajority rule in real institutions, "0.67" silently implements a *stricter* rule
than the one a user thinks they are configuring, and the error only shows up on tallies
that land exactly on the boundary.

Worth noting the same issue affects the baseline: `0.5` with `>=` means "ties pass,"
which is a real rule, but users writing `0.5` probably mean "more than half."

**Suggested fix (not implemented — out of scope here):** let `threshold` accept a ratio
(`2/3`) or an integer vote count, and document the `>=` comparison.

## Files

- `voting_supermajority.yaml` — the scenario (one changed line vs. built-in `voting`)
- `sweep.py` — threshold sweep used for the boundary investigation
- `traces/baseline_voting.jsonl` — threshold 0.5
- `traces/voting_supermajority.jsonl` — threshold 0.67

## Tools and help used

Claude Code (Claude Opus) in the terminal, used interactively: it pulled the built-in
scenario configs, ran the baseline and modified runs, and wrote the sweep script when I
asked it to test whether the 12/18 rounds were sitting on a boundary. I chose the
scenario and the setting, and I read the traces myself to check the claims. The
Buchanan–Tullock framing is from prior coursework (data science for politics /
auction economics), not from the tool. NANDA Town quickstart and `docs/` for CLI usage.
No other human help.
