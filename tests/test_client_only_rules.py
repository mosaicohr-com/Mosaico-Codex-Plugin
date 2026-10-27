#!/usr/bin/env python3
"""Every rule the server's rule audit classes as client-only is still stated in a thin skill, or enforced by the browser-script gate hook.

The server's audit (mosaico `features/outreach/documentation/outreach-rule-audit.json`) sorts every rule the old skills carried into
enforced, server-decided, guidance, conflict and client-only. The client-only ones can only happen on the person's machine, so they
stay in the plugin. `fixtures/outreach-client-only-rules.json` is the list of those ids, copied with the server commit it came from.
Each id must have a check below (a new id in the fixture fails until it has one) and the check must hold: the phrases are in the
named skills of the named packages, or the gate hook enforces the rule. R110 is moot: the Repair queue and run are gone.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from skill_text import AGENTS, CLAUDE, FOLLOW_UP, HUB, INVITE, LEADS, OUTREACH_SKILLS, PACKAGES, ROOT, SCHEDULE, check, flat, read, skill

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "outreach-client-only-rules.json"
GATE = CLAUDE / "hooks" / "browser-script-gate.py"
RUN = (HUB, INVITE, FOLLOW_UP)
ALL = OUTREACH_SKILLS

# id -> list of (package, skills, phrases that must all appear in each of those skills). "gate" checks the hook source.
RULES: dict[str, dict] = {
    "R002": {"skills": [("Claude", RUN, ["amplifyapp", "production"]), ("Codex", RUN, ["amplifyapp", "production"]),
                        ("Claude", (HUB,), ["organisation id"]), ("Codex", (HUB,), ["organisation id"])]},
    "R004": {"skills": [("Claude", (HUB,), ["connect it in Claude's connectors (not /mcp)"]), ("Claude", (INVITE, FOLLOW_UP), ["connect it in Claude's connectors (not /mcp)"]),
                        ("Codex", (HUB,), ["stop and tell them to add it"]), ("Codex", (INVITE, FOLLOW_UP), ["None connected: stop"])]},
    "R006": {"skills": [("Claude", ALL, ["Never end the acting session yourself"]), ("Codex", ALL, ["Never end the acting session yourself"])]},
    "R017": {"skills": [("Claude", RUN, ["Never print, retype, paraphrase, reorder, shorten or extend a script", "// mosaico run <script>.js <PLACEHOLDER>=<value>"])],
             "gate": ["// mosaico run", "def expand_directive", "def approved_scripts", "def evaluate"]},
    "R018": {"skills": [("Claude", RUN, ["Never read, copy, export or reconstruct a LinkedIn cookie, token or session"]),
                        ("Codex", RUN, ["Never read, copy, export or reconstruct a LinkedIn cookie, token or session"])],
             "gate": ["RESTRICTED", "cookie", "csrf", "linkedin", "localStorage"]},
    "R019": {"skills": [("Claude", RUN, ["file-reading tool", "browser folder", "needs updating"])]},
    "R020": {"skills": [("Claude", RUN, ["built-in browser pane", "Chrome extension"]), ("Codex", RUN, ["Codex cannot run the approved LinkedIn captures"])]},
    "R043": {"skills": [("Claude", (INVITE, LEADS), ["acknowledgeProfileOnOtherOwner", "only after the person decides"]),
                        ("Codex", (INVITE, LEADS), ["acknowledgeProfileOnOtherOwner", "only after the person decides"])]},
    "R056": {"skills": [("Claude", (INVITE,), ["email-required", "never cannot-message"]), ("Codex", (INVITE,), ["email-required", "never cannot-message"])]},
    "R090": {"skills": [("Claude", (INVITE,), ["only after LinkedIn shows the invitation gone", "never click Connect or Message"]),
                        ("Codex", (INVITE,), ["only after LinkedIn shows the invitation gone", "never click Connect or Message"])]},
    "R093": {"skills": [("Claude", RUN, ["warning, captcha or restriction stops the run at once", "linkedInIssue"]),
                        ("Codex", RUN, ["warning, captcha or restriction stops the run at once", "linkedInIssue"])]},
    "R098": {"skills": [("Claude", (INVITE, FOLLOW_UP), ["Routines Board", "one batch", "never a halt", "ArtifactData"])]},
    "R099": {"skills": [("Claude", RUN, ["incident_log_mcp_report", "memory"]),
                        ("Codex", RUN, ["incident_log_mcp_report", "memory"])]},
    "R101": {"skills": [("Claude", (AGENTS, LEADS), ["immediately before"]), ("Codex", (AGENTS, LEADS), ["immediately before"]),
                        ("Claude", (LEADS,), ["Never infer a bulk target from a partial name"]), ("Codex", (LEADS,), ["Never infer a bulk target from a partial name"])]},
    "R106": {"skills": [("Claude", (SCHEDULE,), ["mcp__Claude_Browser__javascript_tool", "mcp__Claude_Browser__computer", "mcp__Claude_Browser__browser_batch",
                                                "mosaico-outreach-*", "daily-approved-outreach-sends", "amplifyapp.com", "non-production Mosaico address"]),
                        ("Codex", (SCHEDULE,), ["mosaico-outreach-*", "daily-approved-outreach-sends", "mosaico-lead-preparation"])]},
    "R109": {"skills": [("Claude", (SCHEDULE,), ["Never add, shorten or copy a step into a text", "Sync data routine", "never run"]),
                        ("Claude", (INVITE, FOLLOW_UP), ["needs a newer plugin than", "needs updating"]),
                        ("Claude", (FOLLOW_UP,), ["Run nothing from it"])]},
    # Moot since the Repair queue and run left the server: nothing in either package may start or mention a Repair run.
    "R110": {"retired": True},
}


def main() -> None:
    fixture = json.loads(read(FIXTURE))
    source = fixture["source"]
    check(re.fullmatch(r"[0-9a-f]{40}", source["commit"]) is not None, "the fixture does not name the server commit it was copied from")
    check(source["file"].endswith("outreach-rule-audit.json") and source["branch"] == "stage-v2", "the fixture does not name the server audit file and branch")
    ids = [rule["id"] for rule in fixture["rules"]]
    check(len(ids) == len(set(ids)) == 18, f"the fixture should hold the 18 client-only rules, once each: {ids}")
    check(all(rule["clientOnly"] for rule in fixture["rules"]), "a fixture rule has no clientOnly place")
    check(set(ids) == set(RULES), f"the checks and the fixture differ: unchecked={sorted(set(ids) - set(RULES))}, unknown={sorted(set(RULES) - set(ids))}")

    gate = read(GATE)
    for rule in fixture["rules"]:
        spec = RULES[rule["id"]]
        where = rule["clientOnly"]
        if spec.get("retired"):
            for package, root in PACKAGES.items():
                check(not (root / "skills" / "mosaico-outreach-repair-run").exists(), f"{rule['id']}: the {package} package still has a Repair skill")
            continue
        if where.startswith("plugin-gate-hook"):
            check("gate" in spec, f"{rule['id']} is enforced by the gate hook but has no gate check")
        for needle in spec.get("gate", ()):
            check(needle in gate, f"{rule['id']}: the gate hook {GATE.relative_to(ROOT)} lacks {needle}")
        for package, names, phrases in spec.get("skills", ()):
            for name in names:
                text = flat(skill(package, name))
                for phrase in phrases:
                    check(phrase in text, f"{rule['id']}: {package} {name} does not state: {phrase}")
        check(spec.get("skills") or spec.get("gate"), f"{rule['id']} is checked nowhere")

    print(f"PASS: all {len(ids)} client-only rules of the server audit ({source['commit'][:12]} on {source['branch']}) are still stated in a thin skill "
          "or enforced by the browser-script gate hook; R110 is moot because Repair is gone.")


if __name__ == "__main__":
    main()
