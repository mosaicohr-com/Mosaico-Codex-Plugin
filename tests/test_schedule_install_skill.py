#!/usr/bin/env python3
"""The schedule-install skills describe the three Outreach schedules and refuse unsafe installs."""

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
    "Mosaico Outreach — Send invitations",
    "Mosaico Outreach — Follow-up",
    "Mosaico Outreach — Withdraw stale invitations",
    "Mosaico Outreach — Source leads",
    "Mosaico Outreach — Repair",
)
LANE_TITLES = (
    "Mosaico Outreach — Source leads (own)",
    "Mosaico Outreach — Source leads (colleagues)",
)
OUTREACH_SKILLS = (
    "mosaico-outreach-invite-run",
    "mosaico-outreach-follow-up-run",
    "mosaico-outreach-lead-management",
    "mosaico-outreach-agent-management",
    "mosaico-outreach-repair-run",
)
SET_SENTENCE = "Set Leads per day and Leads per run on an Agent in Outreach (Agent tab), then rerun."
FULL_SENTENCE = "Every Agent is full for the next 10 business days; nothing to source"
PLAN_SENTENCE = "Leads per day and Leads per run are set on each Agent in Outreach, Agent tab; an Agent is sourced only when it is on and both are set."
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


MIN_VERSION = "0.9.6"
SOURCE_MIN_VERSION = "0.9.13"  # Codex's single Source leads text: 0.9.13 writes no drafts (0.9.9 added Leads per run)
LANE_MIN_VERSION = "0.9.13"  # Claude's two Source leads lane texts (0.9.12 added the `sourcing scope` line; 0.9.13 writes no drafts)
SYNC_MIN_VERSION = "0.9.15"  # Claude's Send invitations and Withdraw stale invitations texts: 0.9.15 splits the old Sync data routine into them
FOLLOW_MIN_VERSION = "0.9.18"  # Claude's Follow-up text: 0.9.16 started a follow_up_pass run and works outreach_get_follow_up_queue; 0.9.17 works its repair stages, skippedThisRun and linkedDuplicate; 0.9.18 books a later touch and leaves booked work alone
CONNECTOR_RULE = (
    "Use the Mosaico connector that serves production (https://app.mosaico.one), the one the person connected in Claude. "
    "The plugin ships no Mosaico server of its own. "
    "If no Mosaico connector is connected, stop and tell the person to connect it in Claude's connectors (not /mcp), then rerun. "
    "Never use a server whose address contains amplifyapp.com, stage, staging, test or localhost; if that is the only Mosaico server available, stop and report it. "
    "Do not choose a server because its organisation id matches; stage and production share ids."
)


def routine(text: str, name: str) -> str:
    """The body of the '## <name>' section of a run skill."""
    match = re.search(rf"^## {re.escape(name)}\n(.*?)(?=^## |\Z)", text, re.S | re.M)
    if match is None:
        raise SystemExit(f"FAIL: the skill has no '## {name}' section")
    return match.group(1)


def second_person(text: str) -> str:
    section = text[text.index("## Set up a second person") :]
    return " ".join(section[: section.index("\n## ", 5)].split())


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

    # Thin routines (0.9.6): each saved schedule text holds only the standing answers and names the installed plugin's skill and routine
    # section; the procedure lives in the run skills. The texts are short, name the skill, the section and the version stamp, carry the
    # standing-answer placeholders and hold no Step 1 / Step 2 procedure.
    THIN_CAP = 200
    claude_texts = re.findall(r"```text\n(.*?)\n```", claude, re.S)
    codex_texts = re.findall(r"```text\n(.*?)\n```", SKILLS["Codex"], re.S)
    check(len(claude_texts) == 6, f"Claude skill must hold exactly six schedule texts (Send invitations, Follow-up, Withdraw stale invitations, Source leads own, Source leads colleagues, Repair), found {len(claude_texts)}")
    for title in LANE_TITLES:
        check(title in claude, f"Claude skill is missing the Source leads lane title: {title}")
    check(len(codex_texts) == 1, f"Codex skill must hold exactly one schedule text, found {len(codex_texts)}")
    sync_text, follow_text, withdraw_text, source_text, colleagues_text, repair_text = claude_texts
    codex_text = codex_texts[0]
    THIN = (
        ("Claude Send invitations", sync_text, "mosaico:mosaico-outreach-invite-run", "Send invitations routine", ("<timezone>", "<public identifier>"), "built-in browser pane"),
        ("Claude Follow-up", follow_text, "mosaico:mosaico-outreach-follow-up-run", "Follow-up routine", ("<timezone>", "<public identifier>"), "built-in browser pane"),
        ("Claude Withdraw stale invitations", withdraw_text, "mosaico:mosaico-outreach-invite-run", "Withdraw stale invitations routine", ("<timezone>", "<public identifier>"), "built-in browser pane"),
        ("Claude Source leads (own)", source_text, "mosaico:mosaico-outreach-invite-run", "Source leads routine", ("<timezone>", "<public identifier>"), "built-in browser pane"),
        ("Claude Source leads (colleagues)", colleagues_text, "mosaico:mosaico-outreach-invite-run", "Source leads routine", ("<timezone>", "<public identifier>"), "built-in browser pane"),
        ("Claude Repair", repair_text, "mosaico:mosaico-outreach-repair-run", "Repair routine", ("<timezone>", "<public identifier>"), "built-in browser pane"),
        ("Codex Source leads", codex_text, "$mosaico:mosaico-outreach-invite-run", "Source leads routine", ("<timezone>",), "authenticated LinkedIn browser"),
    )
    for label, text, skill_name, section_name, placeholders, browser in THIN:
        min_version = (LANE_MIN_VERSION if label.startswith("Claude Source leads") else SOURCE_MIN_VERSION) if "Source leads" in label else (FOLLOW_MIN_VERSION if label == "Claude Follow-up" else SYNC_MIN_VERSION if label in ("Claude Send invitations", "Claude Withdraw stale invitations") else MIN_VERSION)
        words = len(text.split())
        check(words <= THIN_CAP, f"{label} schedule text is {words} words, over the {THIN_CAP}-word cap: it must be thin")
        check(f"Use the installed {skill_name} skill from the mosaico plugin ({min_version} or later)" in text, f"{label} text does not name the installed skill and the minimum version")
        check(f"Follow that skill's \"{section_name}\" section exactly" in text, f"{label} text does not name the routine section it follows")
        check("Standing answers for this recurring automation, supplied once by the person:" in text, f"{label} text lacks the standing answers")
        for placeholder in placeholders:
            check(placeholder in text, f"{label} text lacks the placeholder {placeholder}")
        check(f"is older than {min_version} or has no \"{section_name}\" section, stop and report that the plugin needs updating" in text, f"{label} text lacks the version stamp stop")
        check("Report as the skill says." in text, f"{label} text does not hand the report to the skill")
        check(browser in text, f"{label} text lacks the browser line ({browser})")
        check("A LinkedIn warning or captcha stops the run, which then reports." in text, f"{label} text lacks the LinkedIn warning guard")
        for procedure in ("Step 1", "Step 2", "Step 3", "outreach_start_run", "outreach_get_", "outreach_record", "identityEvidence", "// mosaico run", "browser/linkedin-", "file-reading tool"):
            check(procedure not in text, f"{label} text holds procedure ({procedure}); it belongs in the skill's routine section")
    for label, text in (("Claude Source leads (own)", source_text), ("Claude Source leads (colleagues)", colleagues_text), ("Codex Source leads", codex_text)):
        check("<quota map>" not in text and "quota" not in text.lower() and "who receives" not in text.lower(), f"{label} thin text still carries a quota standing answer")
    check("Proceed without asking which days or which scope" in sync_text and "Proceed without asking which days or which scope" in source_text and "Proceed without asking which scope" in repair_text, "A thin text does not say to proceed without asking")
    check('"write missing invitation drafts"' in sync_text and '"send approved invitations"' in sync_text and '"one pass per thread"' not in sync_text, "Send invitations text lacks its scope answers")
    check('"one pass per thread"' in follow_text and "invitations for today" not in follow_text, "Follow-up text lacks its scope answer")
    check("whole withdraw queue" in withdraw_text and "cap Mosaico sets" in withdraw_text and "Proceed without asking which scope" in withdraw_text, "Withdraw stale invitations text lacks its scope answer")
    for dead in ("Sync data routine", "This is the Sync data"):
        check(not any(dead in text for text in claude_texts), f"a schedule text still names the deprecated {dead}")
    check("prepare invitation drafts" not in source_text and "prepare invitation drafts" not in colleagues_text and "prepare invitation drafts" not in codex_text, "a Source leads text still names the action that prepares drafts")
    check('"source Leads only"' in source_text and '"source Leads only"' in colleagues_text, "Source leads text lacks its scope answers")
    for label, text in (("Claude Source leads (own)", source_text), ("Claude Source leads (colleagues)", colleagues_text), ("Codex Source leads", codex_text)):
        check("next business day" not in text and "day:" not in text and "scheduledDate" not in text, f"{label} thin text still names a day: the application files the days")
    check("whole repair queue" in repair_text, "Repair text lacks its scope answer")
    check("the Source leads schedule" not in sync_text and "Sync data schedule" not in source_text and "Sync data schedule" not in colleagues_text and "Sync data" not in follow_text, "A thin text describes another schedule's procedure")
    # The installer states the version stamp once and the update-in-place rule for a long-form text.
    for package, text in SKILLS.items():
        flat_installer = " ".join(text.split())
        check("**Version stamp.**" in text and f"({MIN_VERSION}, the first release with the routine sections)" in flat_installer and "stops and reports that the plugin needs updating" in flat_installer, f"{package} skill lacks the version stamp rule")
        if package == "Claude":
            check("The Source leads texts need 0.9.13 (0.9.12 added the `sourcing scope` line" in flat_installer and "The Send invitations and Withdraw stale invitations texts need 0.9.15" in flat_installer and "named in the plugin's changelog for 0.9.15" in flat_installer and "A saved Sync data text is retired" in flat_installer, "Claude skill does not state the Source leads 0.9.13 and the 0.9.15 minimum versions")
            check("The Follow-up text needs 0.9.18" in flat_installer and "`follow_up_pass`" in flat_installer and "`outreach_get_follow_up_queue`" in flat_installer and "named in the plugin's changelog for 0.9.18" in flat_installer
                  and "`fix-address`" in flat_installer and "`drop-declined`" in flat_installer and "`skippedThisRun`" in flat_installer and "`linkedDuplicate`" in flat_installer
                  and "`sendNotBefore` on a follow-up draft, `nextTouchOn` on a Lead" in flat_installer and "`wait_for_scheduled_day`" in flat_installer
                  and "a 0.9.17 plugin works the repairs the queue carries" in flat_installer and "knows no dates and would draft at once for a Lead who asked for January" in flat_installer
                  and "The Send invitations and Withdraw stale invitations texts stay at 0.9.15" in flat_installer, "Claude skill does not state the Follow-up 0.9.18 minimum version")
            update_flat = flat_installer[flat_installer.index("### Update the standing answers in place") :]
            check("a Follow-up schedule saved at 0.9.15, 0.9.16 or 0.9.17" in update_flat and "becomes the 0.9.18 Follow-up text" in update_flat and 'A saved Follow-up text that says "0.9.15 or later", "0.9.16 or later" or "0.9.17 or later"' in flat_installer and "replace it in place with the 0.9.18 Follow-up text" in flat_installer
                  and "its stamp moved to 0.9.18" in flat_installer and "to move a saved Follow-up text from the 0.9.15, 0.9.16 or 0.9.17 stamp to the 0.9.18 stamp" in flat_installer,
                  "Claude skill does not move a saved 0.9.15, 0.9.16 or 0.9.17 Follow-up text to the 0.9.18 stamp in place")
            follow_start = flat_installer.index("**Mosaico Outreach — Follow-up**")
            follow_prose = flat_installer[follow_start : flat_installer.index("```text", follow_start)]
            check("From 0.9.18 it books a later touch when a conversation asks to be picked up later" in follow_prose and "leaves work booked for a later day alone until its day" in follow_prose
                  and "reports the bookings it made, changed or cleared" in follow_prose, "Claude installer's Follow-up description does not say what 0.9.18 adds")
        else:
            check("The Source leads text needs 0.9.13, the first release where a Source leads run finds, saves and places Leads only and writes no invitation drafts" in flat_installer, f"{package} skill does not state the Source leads minimum version 0.9.13")
        check(PLAN_SENTENCE in flat_installer and "to drop it follow **Update the standing answers in place** below" in flat_installer, f"{package} skill does not say both numbers are set on each Agent, and an Agent is sourced only with both")
        check("Never copy any step of the procedure into" in flat_installer, f"{package} skill does not forbid copying procedure into a schedule text")
        update = flat_installer[flat_installer.index("### Update the standing answers in place") :] if "### Update the standing answers in place" in flat_installer else ""
        check(update != "", f"{package} schedule-install skill lacks the named sub-section: Update the standing answers in place")
        for needle in ("older long form", "has to become the thin text", "Ask nothing else", "Replace the whole text with the", "Change nothing else", "enabled state", "read its answers from it", "carry them over unchanged", "Read the saved", "A write without readback is not completion"):
            check(needle in update, f"{package} 'Update the standing answers in place' lacks: {needle}")
        check("**Update the standing answers in place** below" in flat_installer and "Update the Source leads quota in place" not in flat_installer, f"{package} installer points at the old sub-section name")
        check("a text in the older long form is replaced by the thin text" in flat_installer, f"{package} Install step 4 does not replace a long-form text with the thin text")
        check("saved text is the thin text" in flat_installer, f"{package} Install readback does not confirm the thin text")
    check(MIN_VERSION == "0.9.6" and SOURCE_MIN_VERSION == "0.9.13" and LANE_MIN_VERSION == "0.9.13" and SYNC_MIN_VERSION == "0.9.15" and FOLLOW_MIN_VERSION == "0.9.18", "a version stamp changed: update it in the installer, here and in the README together")

    # The procedure that used to live in the schedule texts now lives in the run skills' named routine sections.
    follow_claude = (CLAUDE / "skills" / "mosaico-outreach-follow-up-run" / "SKILL.md").read_text(encoding="utf-8")
    repair_claude = (CLAUDE / "skills" / "mosaico-outreach-repair-run" / "SKILL.md").read_text(encoding="utf-8")
    invite_claude = (CLAUDE / "skills" / "mosaico-outreach-invite-run" / "SKILL.md").read_text(encoding="utf-8")
    invite_codex = (CODEX / "skills" / "mosaico-outreach-invite-run" / "SKILL.md").read_text(encoding="utf-8")
    sync = routine(follow_claude, "Follow-up routine")
    send = routine(invite_claude, "Send invitations routine")
    withdraw = routine(invite_claude, "Withdraw stale invitations routine")
    check("## Sync data routine\n" not in follow_claude and "## Sync data routine (superseded)" in follow_claude, "the follow-up-run skill still has a live Sync data routine heading")
    check("Do not run any part of it" in routine(follow_claude, "Sync data routine (superseded)"), "the superseded Sync data note does not stop an old saved schedule")
    source = routine(invite_claude, "Source leads routine")
    repair = routine(repair_claude, "Repair routine")
    codex_source = routine(invite_codex, "Source leads routine")
    for label, text in (("Follow-up", sync), ("Send invitations", send), ("Withdraw stale invitations", withdraw), ("Source leads", source), ("Repair", repair), ("Codex Source leads", codex_source)):
        for placeholder in ("<timezone>", "<public identifier>", "<quota map>"):
            check(placeholder not in text, f"{label} routine section holds the schedule placeholder {placeholder}; it must refer to the standing answers")
        check("standing answers" in text and "do not ask" in text, f"{label} routine section does not say the schedule supplies the answers")
        check("the timezone from the schedule's standing answers" in text, f"{label} routine section does not take the timezone from the standing answers")
    check("A scheduled run does not ask these questions: the **Follow-up routine** section" in follow_claude, "follow-up-run intro does not point at the Sync data routine")
    check("A scheduled run does not ask these questions: the **Source leads**, **Send invitations** and **Withdraw stale invitations** routine sections" in invite_claude and "the **Source leads routine** section" in invite_codex, "invite-run intro does not point at the Source leads routine")
    check("the public identifier from the schedule's standing answers" in sync and "the public identifier from the schedule's standing answers" in source and "the public identifier from the schedule's standing answers" in repair, "A Claude routine section does not take the LinkedIn identifier from the standing answers")

    # Follow-up routine (follow-up-run).
    for script in ("browser/linkedin-whoami.js", "browser/linkedin-connection-evidence.js", "browser/linkedin-recent-connections.js"):
        check(script in sync, f"Follow-up routine does not name the approved script {script}")
    check("one call per page" in sync and "outreach_record_connections_snapshot" in sync, "Follow-up routine does not describe paged snapshot submission")
    check("mosaico:mosaico-outreach-invite-run" not in sync and "write missing invitation drafts" not in sync and "send approved invitations" not in sync, "Follow-up routine still chains the invitation work")
    flat_sync = " ".join(sync.split())
    for name, text in (("Follow-up", sync), ("Repair", repair)):
        check("LEAD_NAME=<" in text and "PUBLIC_IDENTIFIER=<scriptIdentifier>" in text, f"{name} routine does not give the thread directive with the Lead's name")
    check("scriptIdentifier" in sync and "after /in/" in sync, "Follow-up routine does not name scriptIdentifier and the part after /in/")
    for needle in (
        "outcome of the Lead's latest message (declined, interested or neutral)",
        "a no ends the Lead",
        "exactly as returned, every field including integrity",
        "evidence-altered",
        "thread-not-found-in-window",
        "read-thread",
        "drafts Mosaico discarded (draftsDiscarded)",
        "Leads whose thread was not found in the window",
    ):
        check(needle in flat_sync, f"Follow-up routine lacks: {needle}")
    check("browser/linkedin-thread-messages.js" in sync, "Follow-up routine does not name the thread script")
    check("pass its output unchanged as threadEvidence to outreach_deposit_conversation" in sync, "Follow-up routine does not deposit through the thread script")
    check("Only if the script cannot run, open the item's messageUrl and deposit the visible conversation by eye" in sync, "Follow-up routine does not keep the by-eye deposit as the fallback only")
    check("Deposit the complete visible conversation" not in sync, "Follow-up routine still deposits by eye as the normal path")
    check("threads read from data versus by eye" in sync, "Follow-up routine report does not count threads read from data versus by eye")
    step2 = sync[sync.index("Step 2.") : sync.index("Step 3.")]
    step3 = sync[sync.index("Step 3.") :]
    check("run the approved thread script again" in step2 and "threadEvidence to outreach_mark_message_sent" in step2 and "fresh identityEvidence" in step2, "Follow-up Step 2 does not confirm a follow-up send from the thread script")
    check("send-not-confirmed" in step2 and "retry the send once" in step2 and "outreach_record_delivery_block with reason cannot-message" in step2, "Follow-up Step 2 does not say what to do on send-not-confirmed")
    check("verify delivery on LinkedIn" not in step2, "Follow-up Step 2 still marks a follow-up from a screen check")
    check("from the screen alone" in step2, "Follow-up Step 2 does not forbid marking from the screen alone")
    # 0.9.16: the routine starts a follow_up_pass run and works Mosaico's queue instead of the 750 KB follow-ups read. 0.9.17: it also works the repair stages.
    step1 = sync[sync.index("Step 1.") : sync.index("Step 2.")]
    check("Start one run with intent follow_up_pass" in step1, "Follow-up Step 1 does not start the run with intent follow_up_pass")
    for needle in (
        "outreach_get_follow_up_queue", "never read outreach_get_follow_ups as the working read of this run", "Do what next says, once, then read the queue again",
        "completion.mustContinue", "completion.stopReason", "End the run with outreach_end_run: reason complete when completion.stopReason is queue-empty, needs-a-person or needs-another-intent",
        "follow each item's recommendedCall literally", "next.kind is connections-capture", "next.script.stopAtCreatedAt",
        "delivery.state deliverable and recommends send_approved_follow_up", "send that approved follow-up right then", "without rereading the queue",
        "messageUrlBasis is conversation or stored", "close any open message window before you navigate to the next profile and after each send",
        "the typed text is proved by the thread capture after the send, not by sight",
        "thread-person-held-by-other-lead", "never capture that thread again", "profile-capture-failed", "profileCaptureFailures, givenUp and inToSort", "never capture that Lead again in this run",
        "save the missing outbound follow-up draft Mosaico permits with sentAt null",
    ):
        check(needle in " ".join(step1.split()) + " " + " ".join(step2.split()), f"Follow-up routine lacks: {needle}")
    # 0.9.17: the repair stages, skippedThisRun as information, linkedDuplicate, and the report lines.
    for needle in (
        "For a fix-address item, make its recommendedCall (outreach_update_lead with the new linkedInProfileUrl and the runId) without visiting LinkedIn",
        "for a drop-declined item, make its recommendedCall (outreach_update_lead with status dropped and the runId) and do nothing else for that Lead: no thread read, no draft, no send",
        "A Lead named in skippedThisRun is information for the report: never open, capture, deposit or draft for it again in this run (a later run offers it again)",
        "If the deposit answer carries linkedDuplicate", "report the link and continue with the kept Lead (keptLeadId)", "never call outreach_link_duplicate_leads",
        "record it with the Lead named in heldBy, never capture that thread again and continue with the next Lead",
    ):
        check(needle in " ".join(step2.split()), f"Follow-up Step 2 lacks: {needle}")
    for needle in ("Leads skipped this run (skippedThisRun), each with its code and reason", "links a deposit made (linkedDuplicate: kept and alias Lead", "addresses fixed", "Leads dropped as declined"):
        check(needle in " ".join(step3.split()), f"Follow-up Step 3 lacks: {needle}")
    check("never calls the link tool itself" in " ".join(sync.split()) and "The Repair routine works only the backlog outside this queue" in " ".join(sync.split()), "Follow-up routine does not say it never links by itself and that Repair works only the rest")
    check("outreach_get_follow_ups" not in step2.replace("never read outreach_get_follow_ups as the working read of this run", ""), "Follow-up Step 2 still reads outreach_get_follow_ups")
    check("outreach_get_follow_ups" not in step3 or "repair-recommended" in step3, "Follow-up Step 3 reads from the old follow-ups read")
    queue = " ".join(routine(follow_claude, "The follow-up queue (intent `follow_up_pass`)").split())
    for needle in (
        "intent `follow_up_pass`", "It may not save Leads, link duplicate Leads or withdraw invitations", "never read `outreach_get_follow_ups` in a `follow_up_pass` run",
        "20261013a", "`counts`, `unverified`, `items`, `listed`, `skippedThisRun`, `nextCursor`, `next`, `completion`, `cap`, `blockers`, `allowedActions`, `recommendedAction` and `notes`",
        "`pending-connections-capture`", "never `upperBound`", "`connections-capture`", "`verify-connection`", "`read-thread`", "`send-approved`", "`draft`", "`held`",
        "`approvedMessage`", "`heldReason`", "`readConversationCall`", "`coveredByRun`", "`messageUrlBasis`", "`conversation`, `stored` or `profile`", "`messageUrlNote`",
        "`delivery { state, messageId, body, messageUrl, reasons }`", "`delivery.state` is `deliverable`", "Do not reread the queue first",
        "the typed text is proved by the post-send thread capture, not by sight", "A script that reads the compose box is deferred",
        "close any open message window before you navigate to the next profile and again after each send",
        "`queue-empty`", "`needs-a-person`", "`needs-another-intent`", "`blocked`", "One pass per thread still holds",
        # 0.9.17
        "`fix-address` (`nextStep` `fix_address`", "`drop-declined` (`drop_lead`", "`outreach_update_lead` with the new `linkedInProfileUrl`", "`outreach_update_lead` with `status: dropped`",
        "do nothing else for this Lead: no thread read, no draft, no send", "`repairGroup`", "`addresses`, `declinedPending`, `mismatches`, `repairSuggestions` or `unverified`",
        "the Repair routine now works only the backlog outside this queue", "`excludedAsFollowUpWork`", "`skippedThisRun` lists `{ leadId, personName, code, reason }`", "`counts.skippedThisRun`",
        "`thread-person-held-by-other-lead`", "`profile-capture-failed`", "leaves those Leads out of `items` and `next`", "`completion.stopReason` is `queue-empty` when only they are left",
        "never open, capture, deposit or draft for a skipped Lead again in this run", "A later run offers the Lead again when it is still work",
        "`linkedDuplicate { keptLeadId, aliasLeadId, basis, draftsMoved, draftsDiscarded, declineCarriedOver }`", "`duplicate-linked`", "go on with the kept Lead (`keptLeadId`)",
        "Never call `outreach_link_duplicate_leads`; this intent may not", "It may not save Leads, link duplicate Leads or withdraw invitations",
    ):
        check(needle in queue, f"the follow-up queue section lacks: {needle}")
    stage_order = [queue.index(f"{n}. `{stage}`") for n, stage in ((1, "fix-address"), (2, "drop-declined"), (3, "verify-connection"), (4, "read-thread"), (5, "send-approved"), (6, "draft"), (7, "held"))]
    check(stage_order == sorted(stage_order), "the follow-up queue section does not list the stages in Mosaico's order (fix-address, drop-declined, verify-connection, read-thread, send-approved, draft, held)")
    # 0.9.18: the routine books a later touch (a day Mosaico validates), leaves booked work alone and reports it.
    flat_steps = " ".join(step2.split())
    for needle in (
        "When the Lead's latest message asks to be contacted later (\"talk in January\", \"after the holidays\", \"next month\", a named day) and its outcome is interested or neutral, book it instead of drafting for now, exactly as this skill's section \"Book a later touch\" describes",
        "when the deposit answer lists draft_follow_up, write the draft with sendNotBefore set to the day you propose (YYYY-MM-DD)",
        "when it offers no draft and refuses nothing but follow-up-awaiting-reply, call outreach_update_lead with changes nextTouchOn set to that day and write no draft",
        "Never work out today from a clock (the machine's, the page's; never run date): Mosaico judges every day against its own today in the owner's time zone and returns it as today in a date refusal",
        "If Mosaico refuses a date (date-invalid, date-not-future, date-too-far or date-not-applicable), follow its recommendedAction: retry once with a day the Lead's words still name between earliestAllowed and latestAllowed, otherwise take continue_with_next_lead, write nothing more for that Lead and report the refusal",
        "never pick a day only to get past it and never write the draft undated",
        "A queue item with nextStep wait_for_scheduled_day is booked for a later day: it is not due, so never open, read, draft or send for it; report it from counts.scheduled (a queue left with only those ends with queue-empty)",
        "When its day has come (scheduledReason scheduled-due or next-touch-due) work the item like any other, without a date",
        "Booking is the one case in which a draft item's recommendedCall is not made exactly as given (sendNotBefore is added, or the outreach_update_lead call replaces it), and only as the deposit answer says",
        "When a thread deposit shows a new reply for a Lead with a booking (the note next-touch-scheduled), decide whether the booking still stands: if the reply names another time call outreach_update_lead with the new nextTouchOn, if it asks for contact now or takes the request back call it with nextTouchOn null, otherwise leave the booking as it is",
    ):
        check(needle in flat_steps, f"Follow-up routine lacks: {needle}")
    flat_follow_routine = " ".join(sync.split())
    check("That date is for the report only: the day a follow-up may be booked for is counted from the day the Lead wrote and judged by Mosaico against its own today, never against a clock you read" in flat_follow_routine
          and "the timezone from the schedule's standing answers" in flat_follow_routine, "Follow-up routine still lets the model take today from its own clock")
    check("it books that day instead of drafting now (a day on the follow-up draft, or on the Lead when no draft is due yet) and leaves work booked for a later day alone until its day" in flat_follow_routine,
          "Follow-up routine's opening does not say it books a later touch")
    for needle in (
        "bookings made (each Lead, the day and the Lead's words that asked for it)", "bookings changed or cleared (Lead, old and new day, why)", "booked items waiting (the queue's counts.scheduled)",
        "date refusals (Lead, field, code, the day tried and what was done)", "the held items that need a person, not the ones booked for a later day",
    ):
        check(needle in " ".join(step3.split()), f"Follow-up Step 3 lacks: {needle}")
    check("sends confirmed from data versus by screen" in step3, "Follow-up Step 3 does not report sends confirmed from data versus by screen")
    check(
        "When Mosaico notes repair-recommended on the follow-ups read, do not work the backlog in this run" in step3
        and "Repair needed: n items, run the Repair routine" in step3,
        "Follow-up Step 3 does not recommend Repair instead of working the backlog",
    )

    # Send invitations routine (invite-run): the ordered list (0.9.19), with the approved invitations confirmed from LinkedIn's Sent invitations list.
    for script in ("browser/linkedin-whoami.js", "browser/linkedin-connection-evidence.js", "browser/linkedin-sent-invitations.js"):
        check(script in send, f"Send invitations routine does not name the approved script {script}")
    for gone in ("linkedin-thread-messages.js", "linkedin-recent-connections.js", "outreach_deposit_conversation", "one pass per thread", "outreach_get_withdraw_queue"):
        check(gone not in send, f"Send invitations routine holds work that is not its own: {gone}")
    check("scriptIdentifier" in send and "after /in/" in send, "Send invitations routine does not name scriptIdentifier and the part after /in/")
    sstep3 = send[send.index("Step 3.") : send.index("Step 4.")]
    sstep4 = send[send.index("Step 4.") :]
    check("run the approved sent-invitations script with the Lead's script identifier" in sstep3 and "sentInvitationEvidence to outreach_mark_message_sent" in sstep3 and "fresh identityEvidence" in sstep3, "Send invitations Step 3 does not confirm an invitation send from the Sent invitations list")
    check("run the approved connection-evidence script again" not in sstep3 and "sendEvidence" not in sstep3.replace("sentInvitationEvidence", ""), "Send invitations Step 3 still passes the connection-evidence script as send evidence")
    check("cannot show a pending invitation" in sstep3, "Send invitations Step 3 does not say why the Sent invitations list is used")
    check("send-not-confirmed" in sstep3 and "retry the send once" in sstep3 and "do not retype" in sstep3, "Send invitations Step 3 does not say what to do on send-not-confirmed")
    check("Verify each sent invitation on LinkedIn" not in sstep3, "Send invitations Step 3 still marks an invitation from a screen check")
    check("from the screen alone" in sstep3, "Send invitations Step 3 does not forbid marking from the screen alone")
    check("sends confirmed from data versus by screen" in sstep4, "Send invitations Step 4 does not report sends confirmed from data versus by screen")

    # Withdraw stale invitations routine (invite-run): Mosaico owns the 30-day rule; the run withdraws, records, and never sends.
    flat_withdraw = " ".join(withdraw.split())
    for needle in (
        "outreach_get_withdraw_queue", "outreach_record_withdrawal", "Mosaico owns the 30-day rule", "never work it out from dates yourself",
        "with intent manage_leads", "including both withdraw tools", "Never pass ownerUserId", "rule.withdrawAfterDays is 30, cap.perRun is 25",
        "never recomputes either from dates or counts beyond what the read says", "Follow recommendedAction literally",
        "withdraw_next", "nothing_to_do", "write_report", "register_linkedin_identity", "start_outreach_run",
        "linkedin-identity-not-registered", "run-required", "run-intent-not-allowed",
        "completion (mustContinue, stopReason, validStopReasons)", "next (the Lead to work now, or null)",
        "Record a withdrawal only after LinkedIn shows the invitation is gone", "withdrawal_recorded", "already_withdrawn",
        "invitation-accepted", "declined", "lead-not-active", "no-invitation-sent", "invitation-too-recent", "nothing was written: skip that Lead",
        "Stop when next is null or completion.mustContinue is false", "queue-empty, run-cap-reached or blocked",
        "never clicks Connect", "never withdraws an invitation Mosaico did not list", "never sends anything",
        "A LinkedIn warning or captcha also stops the run at once", "outreach_end_run",
        "https://www.linkedin.com/mynetwork/invitation-manager/sent/",
    ):
        check(needle in flat_withdraw, f"Withdraw stale invitations routine lacks: {needle}")
    for gone in ("outreach_mark_message_sent", "outreach_record_message", "outreach_deposit_conversation", "outreach_save_lead", "observedLinkedInProfile) and"):
        check(gone not in withdraw, f"Withdraw stale invitations routine names a tool that is not its own: {gone}")

    # 0.9.16 changelog: the follow-up queue, the intent, the send-after-deposit, the script retry, the stamp and the named server release.
    entry16 = " ".join(readme[readme.index("### 0.9.16") : readme.index("### 0.9.15")].split())
    for needle in (
        "20261012d", "mosaicohr-com/mosaico#1916", "#1908, #1909, #1910, #1911, #1912 and #1915", "`outreach_get_follow_up_queue`", "`outreach_deposit_conversation`",
        "`follow_up_pass`", "no longer the working read", "`delivery.state` `deliverable`", "Typed text is proved by the thread capture after the send, not by sight",
        "`thread-person-held-by-other-lead`", "`profileCaptureFailures`", "redirect retry", "`requestedIdentifier`", "`resolvedIdentifier`", "stamped 0.9.16 or later",
        "saved 0.9.15 Follow-up text to the 0.9.16 text in place", "stay at 0.9.15",
    ):
        check(needle.lower() in entry16.lower(), f"README 0.9.16 entry lacks: {needle}")
    check(readme.index("### 0.9.16") < readme.index("### 0.9.15"), "README changelog lacks 0.9.16 above 0.9.15")
    # 0.9.17 changelog: the gone-profile status, the repair stages, skippedThisRun, linkedDuplicate, the stamp and the named server release.
    entry17 = " ".join(readme[readme.index("### 0.9.17") : readme.index("### 0.9.16")].split())
    for needle in (
        "20261013a", "mosaicohr-com/mosaico#1921", "promotion of stage-v2 to main-v2", "`fix-address`", "`drop-declined`", "`repairGroup`", "`skippedThisRun`", "`counts.skippedThisRun`",
        "`linkedDuplicate`", "`duplicate-linked`", "`heldBy`", "`excludedAsFollowUpWork`", "`outreach_deposit_conversation`", "`thread-person-held-by-other-lead`",
        "`outreach_link_duplicate_leads`", "reports 404", "410 stays 410", "never replaces a first 404 or 410", "`document.title`", "`location.pathname`",
        "stamped 0.9.17 or later", "saved 0.9.15 or 0.9.16 Follow-up text to the 0.9.17 text in place", "stay at 0.9.15", "only the backlog outside the follow-up queue",
    ):
        check(needle.lower() in entry17.lower(), f"README 0.9.17 entry lacks: {needle}")
    check(readme.index("### 0.9.17") < readme.index("### 0.9.16"), "README changelog lacks 0.9.17 above 0.9.16")
    # 0.9.18 changelog: dated follow-ups, the day the model proposes and the application checks, the fields relied on, the stamp and the named server release.
    entry18 = " ".join(readme[readme.index("### 0.9.18") : readme.index("### 0.9.17")].split())
    for needle in (
        "20261013c", "mosaicohr-com/mosaico#1930", "stage-v2 to main-v2", "mosaicohr-com/mosaico#1928", "#1929", "dated follow-ups",
        "`sendNotBefore` on `outreach_record_message`", "`changes.nextTouchOn` on `outreach_update_lead`", "`nextTouchOn` on `outreach_get_leads`",
        "`nextTouchOn`, `notBefore` and `scheduledReason` on the rows of `outreach_get_follow_ups`", "`summary.scheduled`", "`follow-up-scheduled`", "`next-touch-due`",
        "`notBefore` and `scheduledReason` on the items of `outreach_get_follow_up_queue`", "`counts.scheduled`", "`wait_for_scheduled_day`", "`next-touch-scheduled`",
        "`outreach_deposit_conversation`", "`date-invalid`", "`date-not-future`", "`date-too-far`", "`date-not-applicable`", "`earliestAllowed`", "`latestAllowed`", "`retry_with_valid_date`",
        "Book a later touch", "`draft_follow_up`", "`outreach_update_lead` with `nextTouchOn`", "writes no draft", "booking never holds back or changes what a person approved",
        "The outcome checklist", "is not a refusal, even when it begins with \"not now\"", "stays `declined`",
        "Never today from a clock", "returns it as `today`", "Date refusals follow `recommendedAction`", "`continue_with_next_lead`", "never writes the draft undated",
        "Booked work waits", "stops with `queue-empty`", "no longer count as needing a person", "A new reply on a booked Lead", "another time moves `nextTouchOn`", "clears it (`null`)",
        "recorded as sent on or after the day", "Mosaico clears it in the same write", "stamped 0.9.18 or later",
        "saved 0.9.15, 0.9.16 or 0.9.17 Follow-up text to the 0.9.18 text in place", "stay at 0.9.15", "does not run the scheduled routine",
    ):
        check(needle.lower() in entry18.lower(), f"README 0.9.18 entry lacks: {needle}")
    check(readme.index("### 0.9.18") < readme.index("### 0.9.17"), "README changelog lacks 0.9.18 above 0.9.17")
    flat_readme_top = " ".join(readme[: readme.index("## Changelog")].split())
    check("from 0.9.18 it books a later touch when a conversation asks to be picked up later" in flat_readme_top and "leaves work booked for a later day alone until its day" in flat_readme_top,
          "README current state does not describe the 0.9.18 Follow-up routine")
    # 0.9.19 changelog: the send run's ordered work list and the owner's limits, the refused end, the fields relied on, the named server release
    # (20261014a, on top of 20261013d) and no schedule change.
    entry19 = " ".join(readme[readme.index("### 0.9.19") : readme.index("### 0.9.18")].split())
    for needle in (
        "Requires the Mosaico server release 20261014a", "mosaicohr-com/mosaico#1933", "on top of release 20261013d", "mosaicohr-com/mosaico#1932", "mosaicohr-com/mosaico#1931", "stage-v2 to main-v2",
        "which is already live", "Do not publish or install this plugin before that release is live on main-v2", "the plugin is published only after 20261014a is on production main-v2",
        "`workflowStatus.sendRun` on `outreach_get_day`", "`recommendedAction`", "`allowedActions`", "`next`", "`remaining`", "`checksThisRun`", "`checkLimit`", "`checksLeft`",
        "`draftsThisRun`", "`draftLimit`", "`draftsLeft`",
        "`waiting`", "`skippedThisRun`", "`outreach_record_message`", "`outreach_record_connection_evidence`", "`outreach_end_run`", "`send-run-open`", "`end_run`",
        "One run does send, then check, then draft, in the order Mosaico gives", "that check never counts toward a limit",
        "check the connection of every Lead placed on a later day (after today) whose connection is not checked yet, soonest day first, at most 100 checks in the run (`checkLimit`)",
        "write the invitation draft of every Lead placed on a later day whose connection was checked and is not connected, at most 100 drafts in the run (`draftLimit`)",
        "counted by Mosaico from the run's own record and never by the model", "carry no limit of their own", "needs no reread",
        "The opening question", "no longer offers", "Source leads or Send invitations", "runs send, then check, then draft, in one run",
        "A refused end", "does what the answer names, never argues and never asks again", "`blockerCode` Mosaico gave in the run", "three Mosaico errors in a row",
        "The model's own \"never retry\" rule is gone for the send run", "`sendRun.skippedThisRun`",
        "sends, then checks, then drafts", "Leads that need a person never hold the end, and neither do Leads left over at a limit", "`check-limit-reached`", "`draft-limit-reached`",
        "that release 20261013d called `check-cap-reached`", "`refused-twice-this-run`",
        "Mosaico's figures from its answers, not memory", "drafts written (`draftsThisRun`)", "connection checks made (`checksThisRun`)",
        "Codex", "stops there", "No schedule text changes", "stays at 0.9.15", "Update the plugin on every machine that runs the Send invitations schedule",
    ):
        check(needle.lower() in entry19.lower(), f"README 0.9.19 entry lacks: {needle}")
    for gone in ("`checkCap`", "at most 20", "counted by Mosaico from the run's own evidence writes", "placed from today on"):
        check(gone.lower() not in entry19.lower(), f"README 0.9.19 entry still holds the old send-run wording: {gone}")
    check(readme.index("### 0.9.19") < readme.index("### 0.9.18"), "README changelog lacks 0.9.19 above 0.9.18")
    check("from 0.9.19 it works the one ordered list Mosaico keeps: it sends the approved invitations, checks the connections Mosaico hands out, then writes the missing invitation drafts" in flat_readme_top,
          "README current state does not describe the 0.9.19 Send invitations run")
    # 0.9.20 changelog: a stuck send never stops the run (server release 20261014b, app PR 1938), paired with the release, no schedule change.
    entry20 = " ".join(readme[readme.index("### 0.9.20") : readme.index("### 0.9.19")].split())
    for needle in (
        "Requires the Mosaico server release 20261014b", "mosaicohr-com/mosaico#1938", "mosaicohr-com/mosaico#1935 and #1936", "already on stage", "on top of release 20261014a",
        "Do not publish or install this plugin before that release is live on main-v2", "the plugin is published only after 20261014b is on production main-v2",
        "`sendRun` on the answers to `outreach_mark_message_sent` and `outreach_record_delivery_block`", "`sendRun.movedThisRun`", "`sendRun.movedCount`",
        "`send-refused-twice-this-run`", "`no-open-day`", "`lead-skipped-this-run`", "`invite-already-pending`", "`invitationSentAt`", "`email-required`", "`cannot-message`",
        "A send Mosaico refuses twice is skipped by Mosaico", "`sendRun.skippedThisRun` (step `send`)", "follows the answer's recommendation",
        "no longer records `cannot-message` after a second `send-not-confirmed`",
        "An earlier invitation still pending is not an error", "`invite-pending`", "it never records `invite-pending` itself",
        "LinkedIn asks for the person's email", "sends nothing", "Mosaico keeps the Lead", "Outreach To sort", "`cannot-message` still drops the Lead and is never used for an email request",
        "Mosaico moves the Leads of a missed day", "to open days", "`leadId`, `name`, `fromDay`, `toDay`", "The skill does nothing for either",
        "carries `sendRun`", "rereads only when an answer says `sendRun` is unavailable",
        "The report", "from Mosaico's answers and not from memory", "Codex", "Unchanged from 0.9.19", "`checkLimit`, `draftLimit`", "`send-run-open`",
        "No schedule text changes", "stays at 0.9.15", "Update the plugin on every machine that runs the Send invitations schedule",
    ):
        check(needle.lower() in entry20.lower(), f"README 0.9.20 entry lacks: {needle}")
    for gone in ("`checkCap`", "at most 20"):
        check(gone.lower() not in entry20.lower(), f"README 0.9.20 entry holds old send-run wording: {gone}")
    check(readme.index("### 0.9.20") < readme.index("### 0.9.19"), "README changelog lacks 0.9.20 above 0.9.19")
    # 0.9.19: no schedule text and no minimum-version stamp changes; the Send invitations text still names the routine section of the installed plugin.
    check("(0.9.15 or later)" in claude_texts[0] and 'Follow that skill\'s "Send invitations routine" section exactly' in claude_texts[0] and "0.9.19" not in "\n".join(claude_texts) and "0.9.20" not in "\n".join(claude_texts), "a schedule text changed for 0.9.19 or 0.9.20")
    claude_flat = " ".join(claude.split())
    check("it sends the invitations that are already approved, checks the connections of the Leads placed on later days that Mosaico hands out, then writes the missing invitation drafts for those found not connected; Mosaico sets how many checks and drafts one run gets (`checkLimit` and `draftLimit`)" in claude_flat
          and "the text below is unchanged because it names the routine section of the installed plugin" in claude_flat, "Claude installer does not describe the 0.9.19 Send invitations order and limits")
    check("at most 20" not in claude_flat.split("**Mosaico Outreach — Send invitations**")[1].split("```text")[0], "Claude installer still states the old 20-check limit")
    codex_flat = " ".join(SKILLS["Codex"].split())
    check("it sends the approved invitations, checks the connections Mosaico hands out, then writes the missing invitation drafts" in codex_flat, "Codex installer does not describe the Send invitations order")
    check("It never writes invitation drafts, approves or sends: the Lead owner's Send invitations run writes the drafts" in codex_flat and "It finds Leads and writes invitation drafts" not in codex_flat,
          "Codex installer still says that Source leads writes invitation drafts")
    # 0.9.15 changelog: the split, the stamp, the two server tools, the retirement of the old task, and the named server release.
    entry = " ".join(readme[readme.index("### 0.9.15") : readme.index("### 0.9.14")].split())
    for needle in (
        "Send invitations routine", "Follow-up routine", "Withdraw stale invitations routine", "outreach_get_withdraw_queue", "outreach_record_withdrawal",
        "Mosaico owns the 30-day rule", "Sync data routine (superseded)", "retires (disables or deletes) the old Sync data task", "stamped 0.9.15 or later",
        "Requires the Mosaico server release 20261012c", "mosaicohr-com/mosaico#1907", "mosaicohr-com/mosaico#1906",
    ):
        check(needle in entry, f"README 0.9.15 entry lacks: {needle}")
    check(readme.index("### 0.9.15") < readme.index("### 0.9.14"), "README changelog lacks 0.9.15 above 0.9.14")

    # The third routine: Repair, weekly Sunday 10:00 by default, also on demand, never sends.
    repair_prose = claude[claude.index("**Mosaico Outreach — Repair**") : claude.index("```text", claude.index("**Mosaico Outreach — Repair**"))]
    flat_repair = " ".join(repair.split())
    check("`0 10 * * 0`" in repair_prose and "Sunday at 10:00 AM" in repair_prose, "Repair schedule is not weekly Sunday 10:00 (cron 0 10 * * 0)")
    check("also whenever the person asks for it" in " ".join(repair_prose.split()), "Repair schedule is not also available on demand")
    for needle in (
        "intent repair", "outreach_get_repair_queue", "recommendedCall", "in the order Mosaico gives them", "supplyAlso",
        "// mosaico run <script>.js <PLACEHOLDER>=<value>", "scriptIdentifier", "capture_connections", "outreach_record_connections_snapshot",
        "outcome declined", "history-mismatch", "completion.mustContinue", "run-cap-reached", "queue-empty", "end-of-queue",
        "never earlier for volume", "Reread the queue after each group", "outreach_get_run", "draftsDiscarded", "nothing was sent and nothing was approved",
        "never sends a message or an invitation", "never attempt the same item twice", "mosaico:mosaico-outreach-follow-up-run",
    ):
        check(needle in flat_repair, f"Repair routine lacks: {needle}")
    for script in ("browser/linkedin-whoami.js", "browser/linkedin-connection-evidence.js", "browser/linkedin-recent-connections.js", "browser/linkedin-thread-messages.js"):
        check(script in repair, f"Repair routine does not name the approved script {script}")
    check("browser/linkedin-sent-invitations.js" not in repair, "Repair routine names the sent-invitations script, which Repair never needs")
    check("outreach_mark_message_sent" not in repair and "outreach_record_message" not in repair, "Repair routine names a sending or drafting tool")
    READ_SENTENCE = "Read each script file with the file-reading tool, one file at a time, by its path under the installed plugin's browser folder; do not print them with a shell command."
    for name, text in (("Follow-up", sync), ("Send invitations", send), ("Withdraw stale invitations", withdraw), ("Source leads", source), ("Repair", repair)):
        check(" ".join(text.split()).count(READ_SENTENCE) == 1, f"{name} routine does not tell the run to read the approved scripts with the file-reading tool")
        check("If the installed plugin has no browser folder, stop and report that the plugin needs updating." in text, f"{name} routine lacks the no-browser-folder stop")
    check(READ_SENTENCE not in SKILLS["Codex"] and READ_SENTENCE not in codex_source, "Codex has the browser-script reading sentence, but the Codex package ships no browser scripts")
    check("Repair never sends" in claude, "Claude skill does not say Repair never sends")
    check("60 minutes from the Repair time" in claude, "Claude skill does not keep Repair apart from the daily schedules and Source leads")
    check("0 10 * * 0" in claude.split("## Install")[1], "Install readback does not confirm the Repair cron")
    check("Her Repair schedule works only her own backlog and never sends" in second_person(claude), "Second-person section does not install her Repair schedule")
    check("Source leads and Repair are not installed" in claude, "Single-task fallback does not mention Repair")
    # Each routine is its own section: none borrows another's steps.
    check("outreach_get_repair_queue" not in source and "outreach_get_repair_queue" not in sync and "outreach_get_repair_queue" not in send and "outreach_get_repair_queue" not in withdraw, "a Follow-up, Send invitations or Source leads routine reads the repair queue")

    # Production connector only: every scheduled routine and the overview skill name the connector to use and refuse a stage server.
    overview_claude = (CLAUDE / "skills" / "mosaico-outreach" / "SKILL.md").read_text(encoding="utf-8")
    for label, text in (("Follow-up routine", sync), ("Send invitations routine", send), ("Withdraw stale invitations routine", withdraw), ("Source leads routine", source), ("Repair routine", repair), ("mosaico-outreach skill", overview_claude)):
        flat = " ".join(text.split())
        check(CONNECTOR_RULE in flat, f"{label} lacks the production-connector rule")
        check(flat.count("amplifyapp.com") == 1, f"{label} must name the non-production addresses exactly once")
    installer = " ".join(claude.split())
    check("4. **Non-production Mosaico server.**" in installer, "Claude installer lacks the fourth pre-install check")
    for needle in ("`.mcp.json`", "`~/.claude.json`", "amplifyapp.com", "`localhost`", "refuse to install", "remove it before installing", "stage and production share organisation ids", "`mosaico-stage`", "app.mosaico.one"):
        check(needle in installer, f"Claude installer's fourth check lacks: {needle}")
    check("5. **Production Mosaico connector.**" in installer, "Claude installer lacks the fifth pre-install check")
    for needle in ("A Mosaico connector pointing at `https://app.mosaico.one` must be connected and signed in", "Claude's connectors (not `/mcp`)", "ships no Mosaico server of its own"):
        check(needle in installer, f"Claude installer's fifth check lacks: {needle}")
    check("reached through the plugin's own Mosaico server" not in installer, "Claude installer still names the plugin's own Mosaico server")
    check("Non-production Mosaico server" not in SKILLS["Codex"], "Codex installer carries the Claude-only connector check")

    for provider, root in (("Claude", CLAUDE), ("Codex", CODEX)):
        follow = " ".join((root / "skills" / "mosaico-outreach-follow-up-run" / "SKILL.md").read_text(encoding="utf-8").split())
        check("one page per call" in follow, f"{provider} follow-up-run skill does not describe one page per call")
    follow = " ".join(follow_claude.split())
    for word in ("snapshotId", "pageIndex", "pageCount", "page_recorded", "connections_recorded", "connectionsCapture.pending", "8 minutes", "one-call form"):
        check(word in follow, f"Claude follow-up-run skill does not mention {word}")

    codex = SKILLS["Codex"]
    check("cannot capture connection evidence" in codex, "Codex skill does not say it cannot capture connection evidence")
    check("must not send" in codex, "Codex skill does not forbid a Codex-installed daily schedule from sending")
    check("mcp__Claude_Browser__" not in codex, "Codex skill mentions the Claude browser permissions")

    for package, root in (("Claude", CLAUDE), ("Codex", CODEX)):
        overview = (root / "skills" / "mosaico-outreach" / "SKILL.md").read_text(encoding="utf-8")
        for old in ("8:00 AM", "8:00 PM"):
            check(old not in overview, f"{package} overview skill still mentions {old}")
        check("mosaico:mosaico-outreach-schedule-install" in overview, f"{package} overview does not name the qualified schedule-install skill")
        check("Send invitations" in overview and "Follow-up" in overview and "Withdraw stale invitations" in overview and "Source leads" in overview, f"{package} overview does not describe the schedules")
    codex_overview = (CODEX / "skills" / "mosaico-outreach" / "SKILL.md").read_text(encoding="utf-8")
    check("installed from Claude" in codex_overview, "Codex overview does not say the daily schedules are installed from Claude")

    # Source leads routine (0.9.9): Leads per run drives it and the application files the days; the run is started with no quota and no colleague.
    for package, text in (("Claude", source), ("Codex", codex_source)):
        flat_text = " ".join(text.split())
        check("Send no quota and no colleague" in flat_text and "Mosaico derives the quota from the sourcing plan on the Agents" in flat_text, f"{package} Source leads Step 1 does not start the run with no quota and no colleague")
        check("run.quota" in flat_text and "run.sourcingPlan" in flat_text, f"{package} Source leads Step 1 does not read run.quota and run.sourcingPlan")
        check("the quota map" not in flat_text and "the same quota map" not in flat_text and "using the quota sent at the start" not in flat_text, f"{package} Source leads routine still sends a quota map")
        check("sourcing_plan_empty" in flat_text and "set_agent_sourcing_numbers_in_outreach" in flat_text and SET_SENTENCE in flat_text, f"{package} Source leads Step 1 does not handle sourcing_plan_empty with the exact sentence")
        check("set_leads_per_day_in_outreach" not in flat_text, f"{package} Source leads routine still names the old recommended action")
        check("sourcing-days-full" in flat_text and "wait_for_free_days" in flat_text and FULL_SENTENCE in flat_text and "not a failure" in flat_text, f"{package} Source leads Step 1 does not handle the sourcing-days-full start blocker as not a failure")
        check("quote Mosaico's code and message verbatim" in flat_text, f"{package} Source leads routine does not quote Mosaico's code and message before the sentence")
        check("sourcing-plan-already-met" not in flat_text, f"{package} Source leads routine still handles the removed sourcing-plan-already-met note")
        check("Never send targetCount for sourcing" in flat_text and "Never send scheduledDate" in flat_text, f"{package} Source leads Step 2 does not forbid targetCount and scheduledDate")
        check("targetCount:" not in flat_text and "scheduledDate:" not in flat_text and "scheduledDate=" not in flat_text, f"{package} Source leads routine passes targetCount or scheduledDate")
        check("Call outreach_get_day without day" in flat_text and "the next business day" not in flat_text, f"{package} Source leads Step 2 does not omit day on outreach_get_day")
        check("Keep sourcing while any line of workflowStatus.sourcingPlan is open" in flat_text and "Work workflowStatus.workNow" in flat_text and "never your own judgement" in flat_text, f"{package} Source leads Step 2 does not keep sourcing while a line is open")
        step4 = flat_text[flat_text.index("Step 4."):flat_text.index("Step 5.")]
        check("Stop only when Mosaico says the run is complete" in step4 and "sourcing-quota-met, sourcing-days-full or sourcing-agent-unavailable" in step4 and "end_run_days_full" in step4 and "Never stop while any line of workflowStatus.sourcingPlan is open" in step4 and "never because you think enough was found" in step4, f"{package} Source leads Step 4 stops on something other than Mosaico's completion")
        check("across every day in workflowStatus.runDays" in flat_text, f"{package} Source leads Step 3 does not verify and draft across every run day")
        check("sourcing-quota-met and sourcing-days-full save nothing and are not failures" in flat_text, f"{package} Source leads Step 2 does not handle the two save blocks that end sourcing")
        for needle in ("workflowStatus.sourcingPlan", "workflowStatus.workNow", "workNow.agentId", "no ownerUserId", "agent-not-in-sourcing-plan", "planned-agent-quota-met", "agent-required", "planned-agent-unavailable"):
            check(needle in flat_text, f"{package} Source leads Step 2 lacks: {needle}")
        check("Do not ask the person for numbers" in flat_text, f"{package} Source leads routine may ask the person for numbers")
        check("for each owner and each of their Agents in workflowStatus.sourcingPlan, the target (Leads per run), the Leads accepted, the Leads remaining and the status" in flat_text and "for each day in workflowStatus.runDays, how many Leads were filed on it" in flat_text and "the shortfalls in workflowStatus.shortfalls" in flat_text, f"{package} Source leads Step 5 does not report per Agent and per day")
        check("A run that saved nothing because of a blocker other than days-full is a failed run" in flat_text and "never as successful" in flat_text and f"report \"{FULL_SENTENCE}.\"" in flat_text, f"{package} Source leads Step 5 lacks the failed-run rule or the nothing-to-source report")
        for stale in ("sourcing_participant_required", "sourcing_quota_invalid", "never start a run without the quota", "Fix: run /mosaico:mosaico-outreach-schedule-install"):
            check(stale not in flat_text, f"{package} Source leads routine still holds the old quota wording: {stale}")
    for script in SCRIPTS[:2]:
        check(script in source, f"Claude Source leads routine does not name the approved script {script}")
    check("browser/linkedin-salesnav-colleague-connection.js" in source and "the colleague-connection check" in source and "workflowStatus.colleagueChecks" in source, "Claude Source leads routine lacks the colleague check hand-off")
    check("cannot run the colleague-connection check" in codex_source and "colleague-check-required" in codex_source, "Codex Source leads routine lacks the colleague check refusal")
    check("need no quota" in " ".join(second_person(claude).split()), "Second-person section does not say her Source leads schedules need no quota")
    check("Leads per day and Leads per run on her Agent in Outreach (Agent tab)" in " ".join(second_person(claude).split()) and '"Sourced by"' in second_person(claude), "Second-person section does not point at both numbers and Sourced by on her Agent")
    for package, text in SKILLS.items():
        flat_installer = " ".join(text.split())
        for gone in ("get_team_profiles", "Person ID", "<quota map>", "Who receives the Leads this schedule sources", "How many accepted Leads should each of them reach", "who receives the Leads and how many"):
            check(gone not in flat_installer, f"{package} installer still holds the old quota wording: {gone}")
        check("Never ask for a quota" in flat_installer and "drop any quota map" in flat_installer, f"{package} installer does not drop the quota from an older Source leads text")
    for package, root in (("Claude", CLAUDE), ("Codex", CODEX)):
        raw_invite = (root / "skills" / "mosaico-outreach-invite-run" / "SKILL.md").read_text(encoding="utf-8")
        invite = " ".join(raw_invite.split())
        start_block = invite[invite.index("A sourcing start sends no quota"):invite.index("3. Keep the returned `runId`")]
        for needle in ("sends no quota and no colleague", "Never send `quota` or `colleagueOwnerUserId`", "never ask the person for numbers", "`run.quota`", "`run.sourcingPlan`", "`sourcing_plan_empty`", "`set_agent_sourcing_numbers_in_outreach`", SET_SENTENCE, "`sourcing-days-full`", "`wait_for_free_days`", FULL_SENTENCE, "not a failure", "quotes Mosaico's code and message verbatim", "the sum of their Leads per run", "nothing is taken off for earlier runs", "Mosaico, not you, files each Lead on"):
            check(needle in start_block, f"{package} invite-run start does not say: {needle}")
        check("Never send `targetCount` for sourcing" in invite and "`targetCount: 20`" not in invite, f"{package} invite-run skill still sends targetCount for sourcing")
        check("## Which Agent a Lead goes to" in raw_invite, f"{package} invite-run skill lacks the Which Agent section")
        agent_section = invite[invite.index("## Which Agent a Lead goes to"):invite.index("## The colleague check") if "## The colleague check" in invite else invite.index("## Check a candidate against the colleague")]
        for needle in ("`workflowStatus.sourcingPlan`", "the owner", "`agentId`", "`agentName`", "`leadsPerDay`", "`leadsPerRun`", "`acceptedThisRun`", "`remainingThisRun`", "`open`", "`days-full`", "`workflowStatus.agentId`", "`workNow.agentId`", "`planned-agent-unavailable`", "`agent-not-in-sourcing-plan`", "`planned-agent-quota-met`", "`agent-required`", "`sourcing-quota-met`", "`sourcing-days-full`", "never send `targetCount` or `scheduledDate` for sourcing", "Pass `workNow.agentId` as `agentId` on every `outreach_save_lead` and pass no `ownerUserId`"):
            check(needle in agent_section, f"{package} Which Agent section lacks: {needle}")
        report = invite[invite.index("## Report a sourcing run"):invite.index("## Send approved invitations")]
        check("per Agent, from `workflowStatus.sourcingPlan`" in report and "name the owner and the Agent" in report and "the target (Leads per run)" in report and "per day, from `workflowStatus.runDays`" in report and "the shortfalls in `workflowStatus.shortfalls`" in report, f"{package} invite-run report is not per Agent and per day, with the shortfalls")
        check("A run that saved nothing because of a blocker other than `sourcing-days-full` is a failed run" in report and "Never report such a run as successful" in report, f"{package} invite-run report lost the failed-run rule")
        check(f"report \"{FULL_SENTENCE}.\"" in report and "is not a failure" in report and SET_SENTENCE in report, f"{package} invite-run report does not report days-full with nothing saved as nothing to source")
        check("sourcing-plan-already-met" not in invite and "Leads remaining today" not in invite and "acceptedToday" not in invite, f"{package} invite-run skill still holds the removed per-day wording")
        sourcing = invite[invite.index("## Source Leads "):invite.index("## Which Agent a Lead goes to")]
        for needle in ("Leave `day` out", "Never send `targetCount` for sourcing", "Never send `scheduledDate`", "`scheduled-date-ignored`", "Mosaico decides when sourcing ends, never your own judgement", "While any line in `workflowStatus.sourcingPlan` has status `open`, keep sourcing", "Work `workflowStatus.workNow` and read it again at every decision point", "`sourcing-quota-met` (every Agent delivered its Leads per run), `sourcing-days-full`", "across every day in `workflowStatus.runDays`", "`end_run_days_full`"):
            check(needle in sourcing, f"{package} Source Leads section lacks: {needle}")
        check("targetCount:" not in invite and "scheduledDate:" not in invite, f"{package} invite-run skill passes targetCount or scheduledDate")
        check("## Offer to save the quota" not in raw_invite and "Do you want me to save this into your Source leads schedule" not in invite, f"{package} invite-run skill still offers to save a quota into the schedule")
        for stale in ("sourcing_participant_required", "sourcing_quota_invalid", "who receives the Leads and how many", "get_team_profiles", "never guesses a colleague", "Fix: run /mosaico:mosaico-outreach-schedule-install"):
            check(stale not in invite, f"{package} invite-run skill still holds the old quota wording: {stale}")
        check("shared with a colleague" not in invite and "the number of ready Leads the person named" not in invite, f"{package} invite-run skill still assumes a colleague")
        agents = " ".join((root / "skills" / "mosaico-outreach-agent-management" / "SKILL.md").read_text(encoding="utf-8").split())
        for needle in ("`leadsPerDay`", "`leadsPerRun`", "`sourcedByUserId`", "`outreach_update_agent`", "Owner or Admin, or the Agent's owner", "Sourced by must be an active member", "`sourcing`", "`sourced`", "`not-configured`", "`sourcingReason`", "Turning an Agent on needs no numbers", "Source leads sources it only when both numbers are set"):
            check(needle in agents, f"{package} agent-management skill lacks: {needle}")
        overview = " ".join((root / "skills" / "mosaico-outreach" / "SKILL.md").read_text(encoding="utf-8").split())
        check("The sourcing plan lives on each Agent in Outreach (Agent tab)" in overview and "never a `targetCount`" in overview and "no quota and no colleague" in overview and "`targetCount` (20" not in overview, f"{package} overview skill does not describe the sourcing plan")
        check("Leads per run" in overview and "no `day`" in overview and "sourced only when it is on and both numbers are set" in overview and "nothing to source" in overview and "preserved `day`, `intent: source_invitation_leads`" not in overview, f"{package} overview skill does not describe Leads per run and day placement")

    for manifest in (CLAUDE / ".claude-plugin" / "plugin.json", CODEX / ".codex-plugin" / "plugin.json"):
        check(json.loads(manifest.read_text(encoding="utf-8"))["version"] == "0.9.23", f"{manifest.name} is not at 0.9.23")
    # 0.9.7: neither package bundles a Mosaico server; every call goes through the person's own connector.
    for package_root in (CLAUDE, CODEX):
        check(not (package_root / ".mcp.json").exists(), f"{package_root.name} still ships a bundled .mcp.json")
    for manifest in (CLAUDE / ".claude-plugin" / "plugin.json", CODEX / ".codex-plugin" / "plugin.json", ROOT / ".claude-plugin" / "marketplace.json"):
        check("mcpServers" not in manifest.read_text(encoding="utf-8"), f"{manifest.name} declares a bundled MCP server")
    for path in sorted(ROOT.rglob("*")):
        if path.is_file() and ".git" not in path.parts and "tests" not in path.parts and path.suffix in {".md", ".json", ".js", ".py"}:
            body = path.read_text(encoding="utf-8").lower()
            check("claude-code-client-metadata" not in body and "oauth_resource" not in body, f"{path.relative_to(ROOT)} still carries bundled-server OAuth wiring")
    for label, text in (("Claude", SKILLS["Claude"]), *((f"Claude {name}", (CLAUDE / "skills" / name / "SKILL.md").read_text(encoding="utf-8")) for name in OUTREACH_SKILLS)):
        check("plugin's own Mosaico server" not in " ".join(text.split()), f"{label} still sends people to the plugin's own Mosaico server")
    print("PASS: both schedule-install skills install thin routines (standing answers only, under 200 words, naming the skill, the routine section and the version stamp); the run skills hold each routine section; qualified skill names and the stale-copy checks hold.")


if __name__ == "__main__":
    main()
