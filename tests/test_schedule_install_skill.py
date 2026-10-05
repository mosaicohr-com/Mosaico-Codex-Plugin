#!/usr/bin/env python3
"""The schedule-install skills describe the two Outreach schedules and refuse unsafe installs."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLAUDE = ROOT / "plugins" / "mosaico-claude"
CODEX = ROOT / "plugins" / "mosaico-codex"
SKILLS = {
    "Claude": (CLAUDE / "skills" / "mosaico-outreach-schedule-install" / "SKILL.md").read_text(encoding="utf-8"),
    "Codex": (CODEX / "skills" / "mosaico-outreach-schedule-install" / "SKILL.md").read_text(encoding="utf-8"),
}

TITLES = (
    "Mosaico Outreach — Sync data (connections and messaging)",
    "Mosaico Outreach — Source leads",
)
OUTREACH_SKILLS = (
    "mosaico-outreach-invite-run",
    "mosaico-outreach-follow-up-run",
    "mosaico-outreach-lead-management",
    "mosaico-outreach-agent-management",
)
FORBIDDEN = ("Connect means", "Message means", "Pending means", "already-connected", "invite-pending")
ALLOW_RULES = (
    "mcp__Claude_Browser__javascript_tool",
    "mcp__Claude_Browser__computer",
    "mcp__Claude_Browser__browser_batch",
)
OLD_AUTOMATIONS = (
    "~/.codex/automations/daily-approved-outreach-sends",
    "~/.codex/automations/mosaico-lead-preparation",
)
SCRIPTS = ("browser/linkedin-whoami.js", "browser/linkedin-connection-evidence.js", "browser/linkedin-recent-connections.js", "browser/linkedin-sent-invitations.js")
STALE_DIRS = ("~/.codex/skills/", "~/.claude/skills/")


def check(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL: {message}")


def main() -> None:
    for package, text in SKILLS.items():
        for title in TITLES:
            check(title in text, f"{package} skill is missing the schedule title: {title}")
        for name in OUTREACH_SKILLS:
            for match in re.finditer(re.escape(name), text):
                check(text[: match.start()].endswith("mosaico:"), f"{package} skill names {name} without the mosaico: prefix")
        check(any(f"mosaico:{name}" in text for name in OUTREACH_SKILLS[:2]), f"{package} skill never names a qualified skill")
        for phrase in FORBIDDEN:
            check(phrase not in text, f"{package} skill contains forbidden phrase: {phrase}")
        reasons = re.findall(r"outreach_record_delivery_block with reason (\S+)", text)
        check(all(reason == "cannot-message" for reason in reasons), f"{package} skill records a delivery block for another reason")
        for directory in STALE_DIRS:
            check(directory in text, f"{package} skill does not check {directory} for stale copies")
        for path in OLD_AUTOMATIONS:
            check(path in text, f"{package} skill does not name the old Codex automation {path}")
        check("_archived" in text and "mv " in text, f"{package} skill does not give the archive command")

    claude = SKILLS["Claude"]
    for rule in ALLOW_RULES:
        check(rule in claude, f"Claude skill does not name the allow rule {rule}")
    snippet = claude[claude.index("```json") :]
    snippet = snippet[: snippet.index("```", 7)]
    for rule in ALLOW_RULES:
        check(rule in snippet, f"Claude skill's printed JSON snippet does not include {rule}")
    check("three" in claude and "blocked" in claude, "Claude skill does not explain why browser_batch is required")
    check("permissions.allow" in claude and "~/.claude/settings.json" in claude, "Claude skill does not name the settings file")
    check("cannot write that file" in claude, "Claude skill does not say the plugin cannot write the settings file")
    for script in SCRIPTS:
        check(script in claude, f"Claude skill does not name the approved script {script}")
    check("## Set up a second person" in claude, "Claude skill is missing the Set up a second person section")
    second = claude[claude.index("## Set up a second person") :]
    second = second[: second.index("\n## ", 5)]
    check("outreach_start_run" in second and "inspect_day" in second, "Second-person section does not name the identity check")
    check("linkedin_identity_not_registered" in second, "Second-person section does not handle linkedin_identity_not_registered")
    for rule in ALLOW_RULES:
        check(rule in second, f"Second-person section does not name the allow rule {rule}")
    check("0.6.1" in second and "own Mac" in second, "Second-person section does not name 0.6.1 or her own Mac")
    check("Nobody's run touches another owner's Leads" in second, "Second-person section does not state the isolation rule")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    check("## Set up a second person" in readme, "README is missing the Set up a second person section")
    for rule in ALLOW_RULES:
        check(rule in readme, f"README does not name the allow rule {rule}")
    check("60 minutes" in claude, "Claude skill does not keep the schedules 60 minutes apart")
    sync = claude[claude.index("Mosaico Outreach — Sync data") : claude.index("Mosaico Outreach — Source leads")]
    check("one call per page" in sync and "outreach_record_connections_snapshot" in sync, "Sync data schedule text does not describe paged snapshot submission")
    check("0.8.1 or later" in sync and "0.8.0 or later" not in sync, "Sync data schedule text does not require plugin 0.8.1")
    flat_sync = " ".join(sync.split())
    for needle in (
        "outcome of the Lead's latest message (declined, interested or neutral)",
        "a no ends the Lead",
        "exactly as returned, every field including integrity",
        "evidence-altered",
        "thread-not-found-in-window",
        "repair_drafts",
        "drafts Mosaico discarded (draftsDiscarded)",
        "Leads whose thread was not found in the window",
    ):
        check(needle in flat_sync, f"Sync data schedule text lacks: {needle}")
    check("browser/linkedin-thread-messages.js" in sync, "Sync data schedule text does not name the thread script")
    check("pass its output unchanged as threadEvidence to outreach_deposit_conversation" in sync, "Sync data schedule text does not deposit through the thread script")
    check("Only if the script cannot run, open navigation.messageUrl and deposit the visible conversation by eye" in sync, "Sync data schedule text does not keep the by-eye deposit as the fallback only")
    check("Deposit the complete visible conversation" not in sync, "Sync data schedule text still deposits by eye as the normal path")
    check("threads read from data versus by eye" in sync, "Sync data schedule report does not count threads read from data versus by eye")
    step2 = sync[sync.index("Step 2.") : sync.index("Step 3.")]
    step3 = sync[sync.index("Step 3.") : sync.index("Step 4.")]
    step4 = sync[sync.index("Step 4.") :]
    check("run the approved thread script again" in step2 and "threadEvidence to outreach_mark_message_sent" in step2 and "fresh identityEvidence" in step2, "Sync data Step 2 does not confirm a follow-up send from the thread script")
    check("send-not-confirmed" in step2 and "retry the send once" in step2 and "outreach_record_delivery_block with reason cannot-message" in step2, "Sync data Step 2 does not say what to do on send-not-confirmed")
    check("verify delivery on LinkedIn" not in step2, "Sync data Step 2 still marks a follow-up from a screen check")
    check("browser/linkedin-sent-invitations.js" in sync.split("Step 1.")[0], "Sync data approved-scripts sentence does not name the sent-invitations script")
    check("run the approved sent-invitations script with the Lead's public identifier" in step3 and "sentInvitationEvidence to outreach_mark_message_sent" in step3 and "fresh identityEvidence" in step3, "Sync data Step 3 does not confirm an invitation send from the sent-invitations script")
    check("run the approved connection-evidence script again" not in step3 and "sendEvidence" not in step3.replace("sentInvitationEvidence", ""), "Sync data Step 3 still passes the connection-evidence script as send evidence")
    check("cannot show a pending invitation" in step3, "Sync data Step 3 does not say why the Sent invitations list is used")
    check("send-not-confirmed" in step3 and "retry the send once" in step3 and "do not retype" in step3, "Sync data Step 3 does not say what to do on send-not-confirmed")
    check("Verify each sent invitation on LinkedIn" not in step3, "Sync data Step 3 still marks an invitation from a screen check")
    check("from the screen alone" in step2 and "from the screen alone" in step3, "Sync data Steps 2 and 3 do not forbid marking from the screen alone")
    check("sends confirmed from data versus by screen" in step4, "Sync data Step 4 does not report sends confirmed from data versus by screen")

    for provider, root in (("Claude", CLAUDE), ("Codex", CODEX)):
        follow = " ".join((root / "skills" / "mosaico-outreach-follow-up-run" / "SKILL.md").read_text(encoding="utf-8").split())
        check("one page per call" in follow, f"{provider} follow-up-run skill does not describe one page per call")
    follow = " ".join((CLAUDE / "skills" / "mosaico-outreach-follow-up-run" / "SKILL.md").read_text(encoding="utf-8").split())
    for word in ("snapshotId", "pageIndex", "pageCount", "page_recorded", "connections_recorded", "connectionsCapture.pending", "8 minutes", "one-call form"):
        check(word in follow, f"Claude follow-up-run skill does not mention {word}")

    codex = SKILLS["Codex"]
    check("cannot capture connection evidence" in codex, "Codex skill does not say it cannot capture connection evidence")
    check("must not send" in codex, "Codex skill does not forbid a Codex-installed Sync data schedule from sending")
    check("mcp__Claude_Browser__" not in codex, "Codex skill mentions the Claude browser permissions")

    for package, root in (("Claude", CLAUDE), ("Codex", CODEX)):
        overview = (root / "skills" / "mosaico-outreach" / "SKILL.md").read_text(encoding="utf-8")
        for old in ("8:00 AM", "8:00 PM"):
            check(old not in overview, f"{package} overview skill still mentions {old}")
        check("mosaico:mosaico-outreach-schedule-install" in overview, f"{package} overview does not name the qualified schedule-install skill")
        check("Sync data" in overview and "Source leads" in overview, f"{package} overview does not describe the two schedules")
    codex_overview = (CODEX / "skills" / "mosaico-outreach" / "SKILL.md").read_text(encoding="utf-8")
    check("installed from Claude" in codex_overview, "Codex overview does not say Sync data is installed from Claude")

    for manifest in (CLAUDE / ".claude-plugin" / "plugin.json", CODEX / ".codex-plugin" / "plugin.json"):
        check(json.loads(manifest.read_text(encoding="utf-8"))["version"] == "0.8.3", f"{manifest.name} is not at 0.8.3")
    print("PASS: both schedule-install skills describe the two schedules, qualified skill names, the post-send check and the stale-copy checks.")


if __name__ == "__main__":
    main()
