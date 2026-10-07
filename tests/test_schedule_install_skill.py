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
    "Mosaico Outreach — Sync data (connections and messaging)",
    "Mosaico Outreach — Source leads",
    "Mosaico Outreach — Repair",
)
OUTREACH_SKILLS = (
    "mosaico-outreach-invite-run",
    "mosaico-outreach-follow-up-run",
    "mosaico-outreach-lead-management",
    "mosaico-outreach-agent-management",
    "mosaico-outreach-repair-run",
)
FIX_SENTENCE = "Fix: run /mosaico:mosaico-outreach-schedule-install (Codex: the mosaico-outreach-schedule-install skill), answer who receives the Leads and how many each, and it will put the quota map into this schedule."
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
    check(len(claude_texts) == 3, f"Claude skill must hold exactly three schedule texts, found {len(claude_texts)}")
    check(len(codex_texts) == 1, f"Codex skill must hold exactly one schedule text, found {len(codex_texts)}")
    sync_text, source_text, repair_text = claude_texts
    codex_text = codex_texts[0]
    THIN = (
        ("Claude Sync data", sync_text, "mosaico:mosaico-outreach-follow-up-run", "Sync data routine", ("<timezone>", "<public identifier>"), "built-in browser pane"),
        ("Claude Source leads", source_text, "mosaico:mosaico-outreach-invite-run", "Source leads routine", ("<timezone>", "<public identifier>", "<quota map>"), "built-in browser pane"),
        ("Claude Repair", repair_text, "mosaico:mosaico-outreach-repair-run", "Repair routine", ("<timezone>", "<public identifier>"), "built-in browser pane"),
        ("Codex Source leads", codex_text, "$mosaico:mosaico-outreach-invite-run", "Source leads routine", ("<timezone>", "<quota map>"), "authenticated LinkedIn browser"),
    )
    for label, text, skill_name, section_name, placeholders, browser in THIN:
        words = len(text.split())
        check(words <= THIN_CAP, f"{label} schedule text is {words} words, over the {THIN_CAP}-word cap: it must be thin")
        check(f"Use the installed {skill_name} skill from the mosaico plugin ({MIN_VERSION} or later)" in text, f"{label} text does not name the installed skill and the minimum version")
        check(f"Follow that skill's \"{section_name}\" section exactly" in text, f"{label} text does not name the routine section it follows")
        check("Standing answers for this recurring automation, supplied once by the person:" in text, f"{label} text lacks the standing answers")
        for placeholder in placeholders:
            check(placeholder in text, f"{label} text lacks the placeholder {placeholder}")
        check(f"is older than {MIN_VERSION} or has no \"{section_name}\" section, stop and report that the plugin needs updating" in text, f"{label} text lacks the version stamp stop")
        check("Report as the skill says." in text, f"{label} text does not hand the report to the skill")
        check(browser in text, f"{label} text lacks the browser line ({browser})")
        check("A LinkedIn warning or captcha stops the run, which then reports." in text, f"{label} text lacks the LinkedIn warning guard")
        for procedure in ("Step 1", "Step 2", "Step 3", "outreach_start_run", "outreach_get_", "outreach_record", "identityEvidence", "// mosaico run", "browser/linkedin-", "file-reading tool"):
            check(procedure not in text, f"{label} text holds procedure ({procedure}); it belongs in the skill's routine section")
    check("Proceed without asking which days or which scope" in sync_text and "Proceed without asking which days or which scope" in source_text and "Proceed without asking which scope" in repair_text, "A thin text does not say to proceed without asking")
    check('"one pass per thread"' in sync_text and '"send approved invitations"' in sync_text, "Sync data text lacks its scope answers")
    check('"source Leads only"' in source_text and "next business day" in source_text, "Source leads text lacks its scope answers")
    check("whole repair queue" in repair_text, "Repair text lacks its scope answer")
    check("the Source leads schedule" not in sync_text and "Sync data schedule" not in source_text, "A thin text describes another schedule's procedure")
    # The installer states the version stamp once and the update-in-place rule for a long-form text.
    for package, text in SKILLS.items():
        flat_installer = " ".join(text.split())
        check("**Version stamp.**" in text and f"({MIN_VERSION}, the first release with the routine sections)" in flat_installer and "stops and reports that the plugin needs updating" in flat_installer, f"{package} skill lacks the version stamp rule")
        check("Never copy any step of the procedure into" in flat_installer, f"{package} skill does not forbid copying procedure into a schedule text")
        update = flat_installer[flat_installer.index("### Update the standing answers in place") :] if "### Update the standing answers in place" in flat_installer else ""
        check(update != "", f"{package} schedule-install skill lacks the named sub-section: Update the standing answers in place")
        for needle in ("older long form", "has to become the thin text", "Ask nothing else", "Replace the whole text with the", "Change nothing else", "enabled state", "read its answers from it", "carry them over unchanged", "Read the saved", "A write without readback is not completion"):
            check(needle in update, f"{package} 'Update the standing answers in place' lacks: {needle}")
        check("**Update the standing answers in place** below" in flat_installer and "Update the Source leads quota in place" not in flat_installer, f"{package} installer points at the old sub-section name")
        check("a text in the older long form is replaced by the thin text" in flat_installer, f"{package} Install step 4 does not replace a long-form text with the thin text")
        check("saved text is the thin text" in flat_installer, f"{package} Install readback does not confirm the thin text")
    check(MIN_VERSION == "0.9.6", "the version stamp changed: update it in the installer, here and in the README together")

    # The procedure that used to live in the schedule texts now lives in the run skills' named routine sections.
    follow_claude = (CLAUDE / "skills" / "mosaico-outreach-follow-up-run" / "SKILL.md").read_text(encoding="utf-8")
    repair_claude = (CLAUDE / "skills" / "mosaico-outreach-repair-run" / "SKILL.md").read_text(encoding="utf-8")
    invite_claude = (CLAUDE / "skills" / "mosaico-outreach-invite-run" / "SKILL.md").read_text(encoding="utf-8")
    invite_codex = (CODEX / "skills" / "mosaico-outreach-invite-run" / "SKILL.md").read_text(encoding="utf-8")
    sync = routine(follow_claude, "Sync data routine")
    source = routine(invite_claude, "Source leads routine")
    repair = routine(repair_claude, "Repair routine")
    codex_source = routine(invite_codex, "Source leads routine")
    for label, text in (("Sync data", sync), ("Source leads", source), ("Repair", repair), ("Codex Source leads", codex_source)):
        for placeholder in ("<timezone>", "<public identifier>", "<quota map>"):
            check(placeholder not in text, f"{label} routine section holds the schedule placeholder {placeholder}; it must refer to the standing answers")
        check("standing answers" in text and "do not ask" in text, f"{label} routine section does not say the schedule supplies the answers")
        check("the timezone from the schedule's standing answers" in text, f"{label} routine section does not take the timezone from the standing answers")
    check("A scheduled run does not ask these questions: the **Sync data routine** section" in follow_claude, "follow-up-run intro does not point at the Sync data routine")
    check("A scheduled run does not ask these questions: the **Source leads routine** section" in invite_claude and "the **Source leads routine** section" in invite_codex, "invite-run intro does not point at the Source leads routine")
    check("the public identifier from the schedule's standing answers" in sync and "the public identifier from the schedule's standing answers" in source and "the public identifier from the schedule's standing answers" in repair, "A Claude routine section does not take the LinkedIn identifier from the standing answers")

    # Sync data routine (follow-up-run).
    for script in SCRIPTS:
        check(script in sync, f"Sync data routine does not name the approved script {script}")
    check("one call per page" in sync and "outreach_record_connections_snapshot" in sync, "Sync data routine does not describe paged snapshot submission")
    check("mosaico:mosaico-outreach-invite-run" in sync and "mosaico:mosaico-outreach-invite-run skill with the selected day today and the selected action \"send approved invitations\"" in sync, "Sync data routine does not chain the invite-run skill by name for the approved invitations")
    flat_sync = " ".join(sync.split())
    for name, text in (("Sync data", sync), ("Repair", repair)):
        check("LEAD_NAME=<" in text and "PUBLIC_IDENTIFIER=<scriptIdentifier>" in text, f"{name} routine does not give the thread directive with the Lead's name")
    check("scriptIdentifier" in sync and "after /in/" in sync, "Sync data routine does not name scriptIdentifier and the part after /in/")
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
        check(needle in flat_sync, f"Sync data routine lacks: {needle}")
    check("browser/linkedin-thread-messages.js" in sync, "Sync data routine does not name the thread script")
    check("pass its output unchanged as threadEvidence to outreach_deposit_conversation" in sync, "Sync data routine does not deposit through the thread script")
    check("Only if the script cannot run, open navigation.messageUrl and deposit the visible conversation by eye" in sync, "Sync data routine does not keep the by-eye deposit as the fallback only")
    check("Deposit the complete visible conversation" not in sync, "Sync data routine still deposits by eye as the normal path")
    check("threads read from data versus by eye" in sync, "Sync data routine report does not count threads read from data versus by eye")
    step2 = sync[sync.index("Step 2.") : sync.index("Step 3.")]
    step3 = sync[sync.index("Step 3.") : sync.index("Step 4.")]
    step4 = sync[sync.index("Step 4.") :]
    check("run the approved thread script again" in step2 and "threadEvidence to outreach_mark_message_sent" in step2 and "fresh identityEvidence" in step2, "Sync data Step 2 does not confirm a follow-up send from the thread script")
    check("send-not-confirmed" in step2 and "retry the send once" in step2 and "outreach_record_delivery_block with reason cannot-message" in step2, "Sync data Step 2 does not say what to do on send-not-confirmed")
    check("verify delivery on LinkedIn" not in step2, "Sync data Step 2 still marks a follow-up from a screen check")
    check("browser/linkedin-sent-invitations.js" in sync.split("Step 1.")[0], "Sync data approved-scripts sentence does not name the sent-invitations script")
    check("run the approved sent-invitations script with the Lead's script identifier" in step3 and "sentInvitationEvidence to outreach_mark_message_sent" in step3 and "fresh identityEvidence" in step3, "Sync data Step 3 does not confirm an invitation send from the sent-invitations script")
    check("run the approved connection-evidence script again" not in step3 and "sendEvidence" not in step3.replace("sentInvitationEvidence", ""), "Sync data Step 3 still passes the connection-evidence script as send evidence")
    check("cannot show a pending invitation" in step3, "Sync data Step 3 does not say why the Sent invitations list is used")
    check("send-not-confirmed" in step3 and "retry the send once" in step3 and "do not retype" in step3, "Sync data Step 3 does not say what to do on send-not-confirmed")
    check("Verify each sent invitation on LinkedIn" not in step3, "Sync data Step 3 still marks an invitation from a screen check")
    check("from the screen alone" in step2 and "from the screen alone" in step3, "Sync data Steps 2 and 3 do not forbid marking from the screen alone")
    check("sends confirmed from data versus by screen" in step4, "Sync data Step 4 does not report sends confirmed from data versus by screen")
    check(
        "When Mosaico notes repair-recommended on the follow-ups read, do not work the backlog in this run" in step4
        and "Repair needed: n items, run the Repair routine" in step4,
        "Sync data Step 4 does not recommend Repair instead of working the backlog",
    )

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
    for name, text in (("Sync data", sync), ("Source leads", source), ("Repair", repair)):
        check(" ".join(text.split()).count(READ_SENTENCE) == 1, f"{name} routine does not tell the run to read the approved scripts with the file-reading tool")
        check("If the installed plugin has no browser folder, stop and report that the plugin needs updating." in text, f"{name} routine lacks the no-browser-folder stop")
    check(READ_SENTENCE not in SKILLS["Codex"] and READ_SENTENCE not in codex_source, "Codex has the browser-script reading sentence, but the Codex package ships no browser scripts")
    check("Repair never sends" in claude, "Claude skill does not say Repair never sends")
    check("60 minutes from the Repair time" in claude, "Claude skill does not keep Repair apart from Sync data and Source leads")
    check("0 10 * * 0" in claude.split("## Install")[1], "Install readback does not confirm the Repair cron")
    check("Her Repair schedule works only her own backlog and never sends" in second_person(claude), "Second-person section does not install her Repair schedule")
    check("Source leads and Repair are not installed" in claude, "Single-task fallback does not mention Repair")
    # Each routine is its own section: none borrows another's steps.
    check("outreach_get_repair_queue" not in source and "outreach_get_repair_queue" not in sync, "Sync data or Source leads routine reads the repair queue")

    for provider, root in (("Claude", CLAUDE), ("Codex", CODEX)):
        follow = " ".join((root / "skills" / "mosaico-outreach-follow-up-run" / "SKILL.md").read_text(encoding="utf-8").split())
        check("one page per call" in follow, f"{provider} follow-up-run skill does not describe one page per call")
    follow = " ".join(follow_claude.split())
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

    # Source leads routine: the sourcing start carries the quota Mosaico requires, in both packages' routine section and invite-run skill.
    for package, text in (("Claude", source), ("Codex", codex_source)):
        flat_text = " ".join(text.split())
        check("the quota map from the schedule's standing answers as quota" in flat_text and "each with the same quota map" in flat_text, f"{package} Source leads Step 1 does not send the quota map from the standing answers at the start")
        check("using the quota sent at the start" in text and "using the quota Mosaico reports" not in text, f"{package} Source leads Step 2 still relies on a quota Mosaico reports")
        check("quota remaining for each owner" in flat_text and "A run that saved nothing is a failed run" in flat_text and "never as successful" in flat_text, f"{package} Source leads Step 5 lacks the per-owner report or the failed-run rule")
        for needle in ("sourcing_participant_required", "sourcing_quota_invalid", "never start a run without the quota", "never name a colleague that is not in the quota map from the schedule's standing answers"):
            check(needle in flat_text, f"{package} Source leads routine lacks: {needle}")
        check(FIX_SENTENCE in flat_text, f"{package} Source leads routine lacks the exact Fix sentence for a run that stopped without a quota")
        check("quote Mosaico's code and message verbatim" in flat_text, f"{package} Source leads routine does not quote Mosaico's code and message before the Fix sentence")
    for script in SCRIPTS[:2]:
        check(script in source, f"Claude Source leads routine does not name the approved script {script}")
    check("browser/linkedin-salesnav-colleague-connection.js" in source and "the colleague-connection check" in source, "Claude Source leads routine lacks the colleague check hand-off")
    check("cannot run the colleague-connection check" in codex_source and "colleague-check-required" in codex_source, "Codex Source leads routine lacks the colleague check refusal")
    check("her own member id in its quota map" in " ".join(second_person(claude).split()), "Second-person section does not say her schedule needs her own id in the quota map")
    for needle in ("get_team_profiles", "Person ID", '{"<run owner member id>": 3, "<colleague member id>": 3}'):
        for package, text in SKILLS.items():
            check(needle in " ".join(text.split()), f"{package} Source leads installer text lacks: {needle}")
    for package, root in (("Claude", CLAUDE), ("Codex", CODEX)):
        invite = " ".join((root / "skills" / "mosaico-outreach-invite-run" / "SKILL.md").read_text(encoding="utf-8").split())
        for needle in ("`quota`", "`colleagueOwnerUserId`", "get_team_profiles", "sourcing_participant_required", "sourcing_quota_invalid", "never guesses a colleague", "A run that saved nothing is a failed run", "never report such a run as successful", "Report a sourcing run"):
            check(needle in invite or needle.lower() in invite.lower(), f"{package} invite-run skill lacks: {needle}")
        check(FIX_SENTENCE in invite, f"{package} invite-run skill lacks the exact Fix sentence for a scheduled run without a quota")
        check("quotes Mosaico's code and message verbatim" in invite, f"{package} invite-run skill does not quote Mosaico's code and message before the Fix sentence")
        check("## Offer to save the quota into the Source leads schedule" in (root / "skills" / "mosaico-outreach-invite-run" / "SKILL.md").read_text(encoding="utf-8"), f"{package} invite-run skill lacks the save-to-schedule offer section")
        for needle in ("ask once", "Do you want me to save this into your Source leads schedule, so the scheduled runs use it too?", '"Update the standing answers in place"', "Ask nothing else, change nothing else in", "keep its times", "tell the person what it now holds", "used for this run only", "If no Source leads", "Do not skip the offer silently"):
            check(needle in invite, f"{package} invite-run save-to-schedule offer lacks: {needle}")
        check("mosaico:mosaico-outreach-schedule-install" in invite, f"{package} invite-run offer does not name the qualified installer skill")
        check("`/mosaico:mosaico-outreach-schedule-install`" in invite if package == "Claude" else "`$mosaico:mosaico-outreach-schedule-install`" in invite and "Codex Source leads automation" in invite, f"{package} invite-run offer does not point at the right installer")
        check("shared with a colleague" not in invite and "the number of ready Leads the person named" not in invite, f"{package} invite-run skill still assumes a colleague")

    for manifest in (CLAUDE / ".claude-plugin" / "plugin.json", CODEX / ".codex-plugin" / "plugin.json"):
        check(json.loads(manifest.read_text(encoding="utf-8"))["version"] == "0.9.6", f"{manifest.name} is not at 0.9.6")
    print("PASS: both schedule-install skills install thin routines (standing answers only, under 200 words, naming the skill, the routine section and the version stamp); the run skills hold each routine section; qualified skill names and the stale-copy checks hold.")


if __name__ == "__main__":
    main()
