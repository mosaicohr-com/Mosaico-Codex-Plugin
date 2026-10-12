#!/usr/bin/env python3
"""The follow-up-run skills read threads from LinkedIn's data in Claude and say plainly that Codex cannot."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLAUDE = ROOT / "plugins" / "mosaico-claude"
CODEX = ROOT / "plugins" / "mosaico-codex"
SKILL = "skills/mosaico-outreach-follow-up-run/SKILL.md"


def check(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL: {message}")


def section(text: str, heading: str) -> str:
    match = re.search(rf"^## {re.escape(heading)}\n(.*?)(?=^## |\Z)", text, re.S | re.M)
    check(match is not None, f"missing section {heading}")
    return match.group(1)


def flat(text: str) -> str:
    return re.sub(r"\s+", " ", text)


def main() -> None:
    claude = (CLAUDE / SKILL).read_text(encoding="utf-8")
    codex = (CODEX / SKILL).read_text(encoding="utf-8")

    thread = flat(section(claude, "Capture the thread"))
    for needle in (
        "browser/linkedin-thread-messages.js",
        "`threadEvidence`",
        "`identityEvidence`",
        "`outreach_deposit_conversation`",
        "exactly as returned",
        "built-in browser pane",
        "Never pass `messages` with it",
        "by-eye deposit is the fallback",
        "say in the final report which Leads were read by eye",
        "changing only the value on its first line to the same identifier",
        "// mosaico run linkedin-thread-messages.js PUBLIC_IDENTIFIER=<public identifier> LEAD_NAME=<the Lead's name>",
        "the value on its second line to the Lead's name",
        "`matchBasis`",
        "`requestedName`",
        "`displayName`",
        "`no-conversation`",
        "`thread-not-found-in-window`",
        "Never call it \"no conversation\"",
        "`coverage`",
        "`pagesRead`",
        "up to 8 pages",
        "`outcome`",
        "`outcome-required`",
        "`draftsDiscarded`",
        "`evidence-altered`",
        "### Judge the Lead's latest message",
        "A no ends the Lead. Never draft a follow-up for a Lead who said no, never ask twice, never try to change the Lead's mind.",
        "choose `declined`",
        "Judge only the Lead's latest message, never an older one, never our own words and never the Lead's silence",
        "Mosaico moves the Lead to Drop",
        "Mosaico marks the Lead Warm",
        "do not use the by-eye fallback for it unless the person asks",
    ):
        check(needle in thread, f"Claude thread section lacks: {needle}")
    check_follow = section(claude, "Check for new follow-ups")
    check("**Capture the thread**" in check_follow and "`threadEvidence`" in check_follow and "fresh `identityEvidence`" in check_follow,
          "Check for new follow-ups does not pass threadEvidence with fresh identityEvidence")
    check("say so in the report" in flat(check_follow), "Check for new follow-ups does not require the report to say so")
    one_pass = flat(section(claude, "One pass per thread"))
    check("**Capture the thread**" in one_pass and "`threadEvidence`" in one_pass and "fresh `identityEvidence`" in one_pass,
          "One pass per thread does not pass threadEvidence with fresh identityEvidence")
    check("only when the script cannot run" in one_pass, "One pass per thread does not limit the by-eye deposit to a script that cannot run")
    check("say so in the report" in one_pass, "One pass per thread does not require the report to say so")
    check("Do not search LinkedIn lists" in claude, "lost the no-list-search rule")

    # Rules Mosaico enforces, repair, and script output passed exactly as returned.
    whole_claude = flat(claude)
    for needle in (
        "`follow-up-declined`", "`follow-up-awaiting-reply`", "`follow-up-thread-unread`", "`awaiting-reply`", "`connection-accepted-no-reply`",
        "`repair_drafts`", "`repairSuggestions`", "`draftsDiscarded: [{ messageId, reason }]`", "Before drafting anything new",
        "never work around it", "`recapture`", "exactly as returned", "`integrity` included", "never retyped, trimmed, reformatted, translated or \"fixed\"",
        "`evidence-altered`", "(`status`, `signedIn`, `capturedAt`, `state`, `errorStep`, `profileIdentifier`, `requestedIdentifier`, `resolvedIdentifier`, `memberUrn`, `entries` and `integrity`; none of them changed)", "`{elements, entries, integrity}`",
        "how many drafts Mosaico discarded",
    ):
        check(needle in whole_claude, f"Claude follow-up-run skill lacks: {needle}")
    check("thread not found in window" in whole_claude, "Claude follow-up-run skill does not name the thread not found in window report")
    check("run **Capture the thread** for it and deposit with `outcome`" in whole_claude, "repair does not run the thread capture with an outcome")
    check("**Repair drafts first**" in check_follow and "**Repair drafts first**" in one_pass, "check and one-pass scopes do not do the repair first")
    check("`outcome`" in flat(check_follow) and "`outcome`" in one_pass, "check and one-pass scopes do not pass the outcome")
    for name in ("mosaico-outreach-invite-run", "mosaico-outreach"):
        text = flat((CLAUDE / f"skills/{name}/SKILL.md").read_text(encoding="utf-8"))
        check("exactly as returned" in text and "`integrity`" in text and "`evidence-altered`" in text, f"Claude {name} skill does not say to pass script output exactly as returned")
    invite = flat((CLAUDE / "skills/mosaico-outreach-invite-run/SKILL.md").read_text(encoding="utf-8"))
    check("(`status`, `signedIn`, `capturedAt`, `state`, `errorStep`, `profileIdentifier`, `requestedIdentifier`, `resolvedIdentifier`, `memberUrn`, `entries` and `integrity`; none of them changed)" in invite and "`recapture`" in invite, "Claude invite-run does not pass the whole connection evidence")

    # 0.8.6: the first-line value is whatever follows /in/ (a name or an ACoAA... id), and the new identifier fields travel unchanged.
    for name in ("mosaico-outreach-follow-up-run", "mosaico-outreach-invite-run"):
        text = flat((CLAUDE / f"skills/{name}/SKILL.md").read_text(encoding="utf-8"))
        check("whatever stands there: a name such as `jane-doe`, or an id that starts with `ACoAA`" in text, f"Claude {name} does not say the identifier may be a name or an ACoAA id")
        check("`requestedIdentifier`" in text and "`resolvedIdentifier`" in text and "`memberUrn`" in text, f"Claude {name} does not pass the identifier fields on")
        check("`errorStep`" in text, f"Claude {name} does not name errorStep")
        check("`scriptIdentifier` from the Mosaico read when it is present" in text and "otherwise the part of the Lead's `linkedInProfileUrl` after `/in/`" in text,
              f"Claude {name} does not take the first-line value from scriptIdentifier, else the part after /in/")
    for path in ("mosaico-outreach",):
        text = flat((CLAUDE / f"skills/{path}/SKILL.md").read_text(encoding="utf-8"))
        check("scriptIdentifier" in text and "after `/in/`" in text.replace("after /in/", "after `/in/`"), f"Claude {path} does not name scriptIdentifier")

    # 0.9.16: the follow-up queue, the send-after-deposit, record-and-continue answers and the evidence script's redirect retry.
    queue = flat(section(claude, "The follow-up queue (intent `follow_up_pass`)"))
    for needle in (
        "`outreach_get_follow_up_queue`", "intent `follow_up_pass`", "never read `outreach_get_follow_ups` in a `follow_up_pass` run", "`recommendedCall`",
        "`delivery.state` is `deliverable`", "`delivery.body`", "`delivery.messageUrl`", "Do not reread the queue first",
        "full messaging page", "close any open message window before you navigate to the next profile and again after each send",
        "proved by the post-send thread capture, not by sight", "`completion.stopReason`", "`queue-empty`", "`needs-a-person`", "`needs-another-intent`", "`blocked`",
        "`run-intent-not-allowed`", "Never approve a draft, and never send a draft written in this run",
    ):
        check(needle in queue, f"Claude follow-up queue section lacks: {needle}")
    check("`follow_up_pass`" in flat(section(claude, "Start the run")), "Start the run does not name the follow_up_pass intent")
    deposit_blockers = flat(section(claude, "Capture the thread"))
    check("`thread-person-held-by-other-lead`" in deposit_blockers and "never capture again" in deposit_blockers and "`continue_with_next_lead`" in deposit_blockers,
          "Capture the thread does not say to record thread-person-held-by-other-lead and continue")
    evidence = flat(section(claude, "Capture connection evidence"))
    for needle in ("Redirects (0.9.16)", "never more than once", "never swaps identifiers silently", "`requestedIdentifier` stays the value you gave it", "`resolvedIdentifier` is the identifier LinkedIn's answer names",
                   "`profile-capture-failed`", "`profileCaptureFailures`", "`givenUp`", "`inToSort`", "never capture the same Lead again in the same run"):
        check(needle in evidence, f"Capture connection evidence lacks: {needle}")
    check("Redirects (0.9.16)" in flat(section((CLAUDE / "skills/mosaico-outreach-invite-run/SKILL.md").read_text(encoding="utf-8"), "Capture connection evidence")), "invite-run does not describe the redirect retry")
    # 0.9.17: a gone profile is reported by the script as 404 or 410; a deposit can link two Leads itself.
    for label, text in (("follow-up-run", evidence), ("invite-run", flat(section((CLAUDE / "skills/mosaico-outreach-invite-run/SKILL.md").read_text(encoding="utf-8"), "Capture connection evidence")))):
        for needle in ("Gone profiles (0.9.17)", "reports `status` 404 (410 when LinkedIn says 410)", "LinkedIn's own not-found page", "never replaces a first 404 or 410", "never correct `status`", "never retry the script"):
            check(needle in text, f"{label} Capture connection evidence lacks: {needle}")
    check("Mosaico gives up on a Lead at once on a 404 or 410, and counts a 200 with no profile only as a first failure" in evidence, "follow-up-run does not say how Mosaico counts a 404 against a 200")
    for needle in ("stored with `linkedDuplicate` and the note `duplicate-linked`", "`keptLeadId`, `aliasLeadId`, `basis` `member-id`, `draftsMoved`", "`draftsDiscarded`, `declineCarriedOver`",
                   "carry on with the kept Lead", "Never call `outreach_link_duplicate_leads` yourself", "could prove it only by a public identifier", "`heldBy`", "a person or the Repair routine links the two"):
        check(needle in deposit_blockers, f"Capture the thread lacks: {needle}")
    codex_queue = flat(section(codex, "The follow-up queue"))
    for needle in ("20261013a", "`fix-address`", "`drop-declined`", "`repairGroup`", "`skippedThisRun`", "The Repair routine now works only the backlog outside this queue"):
        check(needle in codex_queue, f"Codex follow-up-run queue section lacks: {needle}")
    check("the Repair routine works only the backlog outside that queue" in flat(section(claude, "Repair is a separate routine")), "Claude follow-up-run 'Repair is a separate routine' does not say Repair works only the rest")
    check("`outreach_get_follow_up_queue`" in flat(section(codex, "The follow-up queue")) and "does not run it" in flat(section(codex, "The follow-up queue")),
          "Codex follow-up-run does not state the queue read and that it does not run the routine")

    codex_thread = flat(section(codex, "Capture the thread"))
    for needle in (
        "linkedin-thread-messages.js",
        "Claude's built-in browser pane",
        "sandboxed",
        "cannot run it",
        "Do not pass `threadEvidence`",
        "by eye",
    ):
        check(needle in codex_thread, f"Codex thread section lacks: {needle}")
    check("read by eye" in flat(section(codex, "Check for new follow-ups")), "Codex check scope does not report threads as read by eye")
    check("by-eye form" in flat(section(codex, "One pass per thread")), "Codex one-pass scope does not name the by-eye form")
    whole_codex = flat(codex)
    for needle in (
        "`outcome`", "`outcome-required`", "### Judge the Lead's latest message", "A no ends the Lead. Never draft a follow-up for a Lead who said no, never ask twice, never try to change the Lead's mind.",
        "`follow-up-declined`", "`follow-up-awaiting-reply`", "`follow-up-thread-unread`", "`awaiting-reply`", "`repair_drafts`", "`repairSuggestions`", "`draftsDiscarded`",
        "never work around it", "how many drafts Mosaico discarded",
    ):
        check(needle in whole_codex, f"Codex follow-up-run skill lacks: {needle}")
    # The outcome checklist reads the same in both packages.
    def checklist(text: str) -> str:
        match = re.search(r"^### Judge the Lead's latest message\n(.*?)(?=^## |\Z)", text, re.S | re.M)
        check(match is not None, "missing the outcome checklist")
        return flat(match.group(1))
    check(checklist(claude) == checklist(codex), "the outcome checklist differs between the Claude and Codex skills")
    check("`threadEvidence`" not in checklist(codex), "Codex outcome checklist mentions script evidence")

    for manifest in (CLAUDE / ".claude-plugin" / "plugin.json", CODEX / ".codex-plugin" / "plugin.json"):
        check(json.loads(manifest.read_text(encoding="utf-8"))["version"] == "0.9.17", f"{manifest.name} is not at 0.9.17")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    check("### 0.7.0" in readme and readme.index("### 0.9.0") < readme.index("### 0.8.7") < readme.index("### 0.8.6") < readme.index("### 0.8.5") < readme.index("### 0.8.4") < readme.index("### 0.8.3") < readme.index("### 0.8.2") < readme.index("### 0.8.1") < readme.index("### 0.8.0") < readme.index("### 0.7.1") < readme.index("### 0.7.0") < readme.index("### 0.6.1"), "README changelog lacks 0.8.6 above 0.8.5 above 0.8.4 above 0.8.3 above 0.8.2 above 0.8.1 above 0.8.0, 0.7.1, 0.7.0 and 0.6.1")
    check("linkedin-thread-messages.js" in readme, "README does not describe the thread script")
    entry = flat(readme[readme.index("### 0.8.1") : readme.index("### 0.8.0")])
    for needle in ("up to 8 pages", "`coverage`", "`outcome`", "no-pressure", "awaiting", "`draftsDiscarded`", "`repair_drafts`", "`integrity`", "`evidence-altered`"):
        check(needle in entry, f"README 0.8.1 entry lacks: {needle}")
    entry2 = flat(readme[readme.index("### 0.8.2") : readme.index("### 0.8.1")])
    for needle in ("messengerConversations.9501074288a12f3ae9e3c7ea243bccbf", "`lastUpdatedBefore`", "primary inbox", "6 Oct 2026"):
        check(needle in entry2, f"README 0.8.2 entry lacks: {needle}")
    entry3 = flat(readme[readme.index("### 0.8.3") : readme.index("### 0.8.2")])
    for needle in ("`complete`", "`page-limit`", "new elements", "fewer than 20", "Sync data schedule text is unchanged"):
        check(needle in entry3, f"README 0.8.3 entry lacks: {needle}")
    skill = flat(claude)
    check("messaging search by the Lead's name" in skill and "primary-inbox conversation list" in skill and "Other tab are not paged" in skill and "`lookup`" in skill,
          "the Claude follow-up skill does not describe the name search and the paged primary-inbox fallback")
    print("PASS: both follow-up-run skills handle thread evidence as designed (Claude reads it from data, Codex cannot) outcome, no-pressure, repair and integrity rules are stated, the follow-up queue is the working read of the scheduled routine, and the version is 0.9.17.")


if __name__ == "__main__":
    main()
