#!/usr/bin/env python3
"""The repair-run skills follow Mosaico's repair queue as designed (Claude works it, Codex only lists it).

Pass --app-repo (or set MOSAICO_APP_REPO) to also check the skills against the application that owns the
queue: the tools, the run intent and the queue's fields must exist there.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLAUDE = ROOT / "plugins" / "mosaico-claude"
CODEX = ROOT / "plugins" / "mosaico-codex"
SKILL = "mosaico-outreach-repair-run"
claude_text = (CLAUDE / "skills" / SKILL / "SKILL.md").read_text(encoding="utf-8")
codex_text = (CODEX / "skills" / SKILL / "SKILL.md").read_text(encoding="utf-8")
flat_claude = " ".join(claude_text.split())
flat_codex = " ".join(codex_text.split())

TOOL_REFERENCE = re.compile(r"`(outreach_[a-z0-9_]+)`")
REGISTERED_TOOL = re.compile(
    r"(?:name|toolName):\s*'(?P<name>outreach_[a-z0-9_]+)'"
    r"|OUTREACH_EVIDENCE_TOOL\s*=\s*'(?P<evidence>outreach_[a-z0-9_]+)'"
)
REPAIR_TOOLS = {
    "outreach_start_run",
    "outreach_get_repair_queue",
    "outreach_update_lead",
    "outreach_deposit_conversation",
    "outreach_record_connection_evidence",
    "outreach_record_connections_snapshot",
    "outreach_link_duplicate_leads",
    "outreach_get_run",
}
SENDING_TOOLS = {"outreach_mark_message_sent", "outreach_record_message", "outreach_record_delivery_block", "outreach_save_lead"}
GROUPS = ("duplicates", "addresses", "declinedPending", "mismatches", "repairSuggestions", "unverified")
ACTIONS = ("link_duplicate_leads", "fix_address", "drop_lead", "verify_connection", "read_thread", "repair_drafts")


def check(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL: {message}")


def front_matter(text: str) -> dict[str, str]:
    match = re.match(r"---\n(.*?)\n---\n", text, re.S)
    check(match is not None, "skill has no front matter")
    return dict(line.split(": ", 1) for line in match.group(1).splitlines())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--app-repo", type=Path, default=Path(os.environ["MOSAICO_APP_REPO"]) if os.environ.get("MOSAICO_APP_REPO") else None)
    args = parser.parse_args()

    for package, text in (("Claude", claude_text), ("Codex", codex_text)):
        meta = front_matter(text)
        check(meta.get("name") == SKILL, f"{package} skill is not named {SKILL}")
        check(len(meta.get("description", "")) > 40, f"{package} skill has no description")
        for match in re.finditer(re.escape(SKILL), text):
            before = text[: match.start()]
            check(before.endswith("mosaico:") or before.endswith("name: "), f"{package} skill names {SKILL} without the mosaico: prefix")

    # Claude: works the queue, and nothing else.
    referenced = set(TOOL_REFERENCE.findall(claude_text))
    check(referenced == REPAIR_TOOLS, f"Claude repair skill references {sorted(referenced ^ REPAIR_TOOLS)} unexpectedly")
    check(not (referenced & SENDING_TOOLS), "Claude repair skill references a sending or drafting tool")
    for needle in (
        "never sends a message or an invitation",
        "never approves, rewrites or replaces a draft",
        "never sets a connection state",
        "never reads a thread by eye",
        "`intent: repair`",
        "// mosaico run linkedin-whoami.js",
        "`identityEvidence`",
        "Never pass `ownerUserId` on a write",
        "`workOrder`",
        "`recommendedCall`",
        "`supplyAlso`",
        "`scriptIdentifier`",
        "Work the items in the order Mosaico lists them",
        "its `tool` and `arguments` unchanged",
        "attempt the same `itemId` twice",
        "// mosaico run linkedin-connection-evidence.js PUBLIC_IDENTIFIER=<scriptIdentifier>",
        "// mosaico run linkedin-thread-messages.js PUBLIC_IDENTIFIER=<scriptIdentifier> LEAD_NAME=<personName>",
        "A decline found while reading a thread is recorded with `outcome: declined`",
        "flagged `history-mismatch` too",
        "exactly as returned, every field including `integrity`",
        "`evidence-altered`",
        "call `outreach_get_repair_queue` again",
        "`cap.perRun`",
        "the cap is Mosaico's, not yours",
        "`completion.mustContinue` is false",
        "`run-cap-reached`",
        "`queue-empty`",
        "`end-of-queue`",
        "`summary.needsPerson`",
        "Call `outreach_get_run`",
        "`draftsDiscarded`",
        "nothing was sent and nothing was approved",
        "Repair never reads a thread by eye",
        "Capture recent connections",
        "capture_connections",
    ):
        check(needle in flat_claude, f"Claude repair skill lacks: {needle}")
    for group in GROUPS:
        check(f"`{group}`" in claude_text, f"Claude repair skill does not name the group {group}")
    for action in ACTIONS:
        check(f"`{action}`" in claude_text, f"Claude repair skill does not say what to do for {action}")
    check(claude_text.index("## Start the run") < claude_text.index("## Read the queue") < claude_text.index("## Read again after each group") < claude_text.index("## Report"), "Claude repair skill sections are out of order")
    check("mcp__Claude_Browser__" not in claude_text, "Claude repair skill names a browser permission rule")
    check("cookie" in claude_text.lower() and "Never read, copy, export or reconstruct a LinkedIn cookie" in flat_claude, "Claude repair skill does not forbid reading a LinkedIn session")
    for name in re.findall(r"mosaico-outreach-[a-z-]+", claude_text):
        check(name in {"mosaico-outreach-follow-up-run", SKILL}, f"Claude repair skill names an unexpected skill {name}")
    for match in re.finditer(r"mosaico-outreach-follow-up-run", claude_text):
        check(claude_text[: match.start()].endswith("mosaico:"), "Claude repair skill names the follow-up-run skill without the mosaico: prefix")

    # Codex: read-only.
    codex_referenced = set(TOOL_REFERENCE.findall(codex_text))
    check(codex_referenced == REPAIR_TOOLS, f"Codex repair skill references {sorted(codex_referenced ^ REPAIR_TOOLS)} unexpectedly")
    for needle in (
        "read-only",
        "never starts a Repair run, never writes to Mosaico",
        "never sends or approves anything",
        "This package cannot capture connection evidence.",
        "Call `outreach_get_repair_queue` with no `runId`",
        "`summary.needsPerson`",
        "`mosaico:mosaico-outreach-repair-run`",
        "Do not call any write tool, do not start a run, do not open LinkedIn",
        "point them to Claude",
    ):
        check(needle in flat_codex, f"Codex repair skill lacks: {needle}")
    check("javascript_tool" not in codex_text and "mcp__Claude_Browser__" not in codex_text and "// mosaico run" not in codex_text, "Codex repair skill runs or names a browser script")
    for group in GROUPS:
        check(group in codex_text, f"Codex repair skill does not name the group {group}")
    for line_number, line in enumerate(codex_text.splitlines(), 1):
        if "ownerUserId" in line:
            check(bool(re.search(r"(Never|Do not) pass", line)), f"Codex repair skill line {line_number} tells the model about ownerUserId")

    # Both packages: the version, the changelog and the overview routes.
    for manifest in (CLAUDE / ".claude-plugin" / "plugin.json", CODEX / ".codex-plugin" / "plugin.json"):
        check(json.loads(manifest.read_text(encoding="utf-8"))["version"] == "0.9.11", f"{manifest.name} is not at 0.9.11")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    entry = " ".join(readme[readme.index("### 0.9.0") : readme.index("### 0.8.7")].split())
    for needle in (
        "`outreach_get_repair_queue`", "`outreach_link_duplicate_leads`", "`mosaico-outreach-repair-run`", "`recommendedCall`",
        "`scriptIdentifier`", "25 items per Repair run", "`outcome` `declined`", "cron `0 10 * * 0`", "Repair needed: n items, run the Repair routine",
        "The Codex copy is read-only", "`repair-recommended`", "20 Leads per run", "`deferredToRepair`",
    ):
        check(needle in entry, f"README 0.9.0 entry lacks: {needle}")
    for package, root, route in (("Claude", CLAUDE, "/mosaico:mosaico-outreach-repair-run"), ("Codex", CODEX, "$mosaico:mosaico-outreach-repair-run")):
        overview = (root / "skills" / "mosaico-outreach" / "SKILL.md").read_text(encoding="utf-8")
        check(route in overview and "Repair the Outreach backlog" in overview, f"{package} overview does not route to the repair-run skill")
    for package, root in (("Claude", CLAUDE), ("Codex", CODEX)):
        follow = " ".join((root / "skills" / "mosaico-outreach-follow-up-run" / "SKILL.md").read_text(encoding="utf-8").split())
        for needle in ("## Repair is a separate routine", "`verifyCap`", "`summary.deferredToRepair`", "`repair-recommended`", "Repair needed: n items, run the Repair routine"):
            check(needle in follow, f"{package} follow-up-run skill lacks: {needle}")

    # The contract with the application that owns the queue.
    if args.app_repo is not None:
        app = args.app_repo.resolve()
        registry = (app / "features/outreach/server/outreach-mcp-registry.ts").read_text(encoding="utf-8")
        run = (app / "features/outreach/server/outreach-run.ts").read_text(encoding="utf-8")
        queue = (app / "features/outreach/shared/outreach-repair-queue.ts").read_text(encoding="utf-8")
        registered: set[str] = set()
        for relative in (
            "features/outreach/server/outreach-mcp-registry.ts",
            "features/outreach/server/outreach-transfer-tool.ts",
            "features/outreach/server/outreach-transfer-batch-tool.ts",
            # The connection-evidence tool's name is a shared constant, not a literal in the registry.
            "features/outreach/shared/outreach-connection-evidence.ts",
        ):
            registered |= {
                match.group("name") or match.group("evidence")
                for match in REGISTERED_TOOL.finditer((app / relative).read_text(encoding="utf-8"))
            }
        for tool in sorted(REPAIR_TOOLS):
            check(tool in registered, f"the application does not register {tool}")
        check("'repair'" in run.split("OUTREACH_RUN_INTENTS")[1].split("as const")[0], "the application has no repair run intent")
        for group in GROUPS:
            check(f"'{group}'" in queue, f"the application's repair queue has no group {group}")
        for action in ACTIONS:
            check(f"'{action}'" in queue, f"the application's repair queue has no action {action}")
        description = re.search(r"name: 'outreach_get_repair_queue'.*?description: '(.*?)',\n    inputSchema", registry, re.S)
        check(description is not None, "cannot read the repair queue tool description")
        for field in ("workOrder", "recommendedCall", "supplyAlso", "scriptIdentifier", "summary.needsPerson", "processedInThisRun", "cap.perRun", "nextCursor", "completion", "run-cap-reached", "queue-empty", "end-of-queue", "capture_connections", "write_report"):
            check(field in description.group(1), f"the application's repair queue description lacks {field}")
        follow_ups = re.search(r"name: 'outreach_get_follow_ups'.*?description: '(.*?)',\n    inputSchema", registry, re.S)
        check(follow_ups is not None and all(word in follow_ups.group(1) for word in ("verifyCap", "deferredToRepair", "repairNeeded", "repair-recommended", "Repair needed: n items, run the Repair routine")), "the application's follow-ups description lacks the Repair recommendation")
        usage = (app / "features/outreach/shared/outreach-flow-steps.ts").read_text(encoding="utf-8")
        for step in ("read_queue_r_1", "verify_connection_r_2", "read_thread_r_3", "fix_address_r_4", "link_duplicates_r_5", "report_r_6"):
            check(step in usage, f"the application's Usage audit has no repair step {step}")
        suffix = "against the application at " + str(app)
    else:
        suffix = "(pass --app-repo to check the application contract too)"
    print(f"PASS: the Claude repair-run skill works Mosaico's repair queue as designed and never sends; the Codex copy is read-only; the schedule, changelog and routes agree {suffix}.")


if __name__ == "__main__":
    main()
