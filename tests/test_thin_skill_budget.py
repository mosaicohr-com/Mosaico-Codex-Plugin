#!/usr/bin/env python3
"""0.10.0: the Claude package's Outreach skills stay thin, and say no limit, 24-hour rule or Repair beyond the one settled rule.

The only Outreach limit is 20 invitation sends per owner per day, which Mosaico enforces. No skill may state a cap, a ceiling, a
count per run or per day, or a 24-hour rule, and Repair is retired. The budget is about 3,500 words across the six Claude Outreach
skills (it was about 38,700); the check allows 3,600 so a sentence may move without a fight, and every skill has its own ceiling.
"""

from __future__ import annotations

import re

from skill_text import LIMIT_SENTENCE, OUTREACH_SKILLS, PACKAGES, HUB, check, flat, skill, words

TOTAL_BUDGET = 3_600
SKILL_BUDGET = {
    "mosaico-outreach": 800,
    "mosaico-outreach-invite-run": 850,
    "mosaico-outreach-follow-up-run": 850,
    "mosaico-outreach-schedule-install": 900,
    "mosaico-outreach-agent-management": 300,
    "mosaico-outreach-lead-management": 500,
}
# Words that state a limit. The one allowed sentence is removed before this runs.
LIMIT_WORDS = re.compile(
    r"\b(?:limit|limits|limited|cap|caps|capped|ceiling|at most|no more than|up to|maximum|max|quota|quotas|throttle|rate)\b"
    r"|\b\d+\s+(?:per|a|every)\s+(?:run|day|week|hour|owner)\b|\b\d+\s+(?:business\s+)?days?\b|\bonce a (?:day|week)\b|\bweekly\b",
    re.I,
)
TWENTY_FOUR = re.compile(r"\b24[- ]?(?:hours?|h)\b|\btwenty[- ]four\b|\blast day\b|\bwithin a day\b|\bevery 24\b", re.I)
REPAIR = re.compile(r"\bRepair\b|[Rr]epair[- ](?:run|queue|routine|skill)|outreach_get_repair_queue|intent:?\s*repair\b")


def main() -> None:
    counts = {name: words(skill("Claude", name)) for name in OUTREACH_SKILLS}
    total = sum(counts.values())
    check(total <= TOTAL_BUDGET, f"the Claude Outreach skills hold {total} words, over the {TOTAL_BUDGET} budget: {counts}")
    for name, count in counts.items():
        check(count <= SKILL_BUDGET[name], f"Claude {name} holds {count} words, over its {SKILL_BUDGET[name]} budget")
    codex_total = sum(words(skill("Codex", name)) for name in OUTREACH_SKILLS)
    check(codex_total <= total, f"the Codex Outreach skills ({codex_total} words) are longer than Claude's ({total})")

    for package in PACKAGES:
        for name in OUTREACH_SKILLS:
            text = flat(skill(package, name))
            if name == HUB:
                check(LIMIT_SENTENCE in text, f"{package} {name} does not state the one limit: {LIMIT_SENTENCE}")
            text = text.replace(LIMIT_SENTENCE, "")
            for match in LIMIT_WORDS.finditer(text):
                raise SystemExit(f"FAIL: {package} {name} states a limit other than 20 sends a day: ...{text[max(0, match.start() - 60):match.end() + 60]}...")
            for match in TWENTY_FOUR.finditer(text):
                raise SystemExit(f"FAIL: {package} {name} states a 24-hour rule: ...{text[max(0, match.start() - 60):match.end() + 60]}...")
            for match in REPAIR.finditer(text):
                raise SystemExit(f"FAIL: {package} {name} still mentions Repair: ...{text[max(0, match.start() - 60):match.end() + 60]}...")
            check("20 invitation sends" not in text, f"{package} {name} repeats the limit outside its one sentence")

    print(f"PASS: the Claude Outreach skills hold {total} words ({', '.join(f'{n.removeprefix('mosaico-')} {c}' for n, c in counts.items())}), "
          "state no limit but 20 invitation sends per owner per day, no 24-hour rule and no Repair, in both packages.")


if __name__ == "__main__":
    main()
