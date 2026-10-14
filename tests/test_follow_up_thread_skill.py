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

    # 0.9.18: dated follow-ups. The model proposes a day from the Lead's words; the application owns the rules, the clock and the hold.
    dated_needles = (
        "Needs the Mosaico server release 20261013c or later",
        "\"talk in January\", \"after the holidays\", \"next month\", a named day",
        "the follow-up is booked for a day instead of being written for now",
        "You propose the day from the Lead's words; Mosaico owns everything after that",
        "It checks the day against its own today in the owner's time zone",
        "If Mosaico refuses `sendNotBefore` or `nextTouchOn` as an unknown argument",
        "only when that outcome is `interested` or `neutral`",
        "A bare \"not now\" with no time is a no, a Lead who said no is never booked, and if you doubt whether the message is a no, it is one",
        "If the words give no time you can name, book nothing and report the Lead with the words",
        "written YYYY-MM-DD", "counted from the day the Lead wrote them",
        "Never work out today from a clock: not the machine's, not the page's, and do not run `date`",
        "it returns it as `today` when it refuses a date",
        "no more than 365 days ahead",
        "Mosaico's answer to the thread deposit decides which call to make, not your own reading of the Lead's state",
        "This is the one case in which a `draft` item's `recommendedCall` is not made exactly as given: it gets `sendNotBefore` added, or it is replaced by the `outreach_update_lead` call below",
        "lists `draft_follow_up` among its allowed actions (a follow-up is due now)",
        "add `sendNotBefore` with the day to that `outreach_record_message` call",
        "once approved, Mosaico holds it until the day (reason `follow-up-scheduled`)",
        "`followUpRuleViolations` holds nothing but `follow-up-awaiting-reply`", "`delivery.state` is `none`", "`returnedToDraft`", "write no draft",
        "`outreach_update_lead` with the `leadId`, `changes` set to `nextTouchOn` with the day, and the `runId`",
        "reason `next-touch-due`", "also when our own message is the latest",
        "An approved follow-up Mosaico offers (`delivery.state` `deliverable`) is sent as approved: booking never holds back or changes a message a person approved",
        "`date-invalid`", "`date-not-future`", "`date-too-far`", "`date-not-applicable`", "`field`, `today`, `earliestAllowed` and `latestAllowed`",
        "`retry_with_valid_date` and `continue_with_next_lead`", "Follow `recommendedAction`: retry once", "between `earliestAllowed` and `latestAllowed`, worked out from the returned `today`",
        "take `continue_with_next_lead`: write nothing more for this Lead and report the refusal",
        "Never choose a day only to get past a refusal, never leave the date out to write the draft anyway, and never try a third time",
        "`wait_for_scheduled_day`", "`notBefore`", "`scheduledReason`", "`counts.scheduled`", "never open, read, draft or send for it",
        "skipped with `next-touch-scheduled` (with `notBefore`)", "`draft-already-exists` with the recommended action `continue_with_next_lead` and `existingMessage.sendNotBefore`",
        "`scheduled-due` or `next-touch-due`", "worked like any other, with no date", "Do not book it again from the same message",
        "A reply before the booked day does not clear the booking", "the note `next-touch-scheduled` with `notBefore`",
        "move the booking: `outreach_update_lead` with the new `nextTouchOn`", "clear it: `nextTouchOn` `null`", "leave the booking as it is",
        "when a follow-up is recorded as sent on or after the booked day, which Mosaico clears in the same write; never clear it yourself after a send",
        "a person's to move (Outreach, the Follow Up card, \"Follow up on or after\")",
        "The report", "the bookings made", "the bookings changed or cleared", "the booked items waiting (`counts.scheduled`)", "the date refusals",
    )
    claude_book = flat(section(claude, "Book a later touch"))
    codex_book = flat(section(codex, "Book a later touch"))
    for needle in dated_needles:
        check(needle in claude_book, f"Claude 'Book a later touch' lacks: {needle}")
        check(needle in codex_book, f"Codex 'Book a later touch' lacks: {needle}")
    # The two sections say the same thing: they differ only where Codex has no queue stages and reads a thread by eye.
    def book_norm(text: str) -> str:
        return text.replace("as stage `draft` describes", "<<draft step>>").replace("as this scope's draft step describes", "<<draft step>>").replace("in the stored conversation", "in the conversation")
    check(book_norm(claude_book) == book_norm(codex_book), "the 'Book a later touch' sections differ between the Claude and Codex skills")
    check(claude.index("## Book a later touch") < claude.index("## Capture connection evidence") and codex.index("## Book a later touch") < codex.index("## Capture connection evidence"),
          "'Book a later touch' is not placed after the outcome checklist and before the connection evidence")
    queue_flat = flat(section(claude, "The follow-up queue (intent `follow_up_pass`)"))
    for needle in ("`notBefore` and `scheduledReason` are on every item", "`scheduled`, `scheduled-due`, `next-touch-scheduled`, `next-touch-due` or null", "never work it out yourself",
                   "last in stage `held` with `nextStep` `wait_for_scheduled_day` (reasons `follow-up-scheduled` or `next-touch-scheduled`)", "is not due, needs no person and is never `next`",
                   "`counts.scheduled` counts those Leads for the report", "A queue with only them left stops with `queue-empty`", "On its day a dated item is first in its stage",
                   "add `sendNotBefore` to the draft or book the Lead instead", "a booked touch whose day has come: write its draft as above, without a date",
                   "Work booked for a later day is in this stage too, last, with `nextStep` `wait_for_scheduled_day`: it needs no person and nothing is done for it in this run",
                   "also when only work booked for a later day, or skipped Leads, is left", "`needs-a-person` (only held items that need a person are left)", "20261013c"):
        check(needle in queue_flat, f"Claude follow-up queue section lacks: {needle}")
    for scope in ("Check for new follow-ups", "One pass per thread"):
        for label, text in (("Claude", claude), ("Codex", codex)):
            check("**Book a later touch**" in flat(section(text, scope)), f"{label} '{scope}' does not point at Book a later touch")
    codex_dated = flat(section(codex, "The follow-up queue"))
    for needle in ("20261013c", "`notBefore`", "`scheduledReason`", "`wait_for_scheduled_day`", "`counts.scheduled`", "stops with `queue-empty`", "**Book a later touch**"):
        check(needle in codex_dated, f"Codex follow-up queue section lacks the dated follow-ups: {needle}")

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
    # 0.9.18: a named later time is not a refusal even after "not now" (otherwise "not now, talk in January" drops the Lead before it can be booked).
    for needle in ("A message that asks to be contacted at a later time it names (\"talk in January\", \"after the holidays\", \"next month\", a named day) is not a refusal, even when it begins with \"not now\": judge it `interested` or `neutral`, and book the day (see **Book a later touch**)",
                   "A \"not now\" with no time, or a \"maybe someday\", stays `declined`"):
        check(needle in checklist(claude) and needle in checklist(codex), f"the outcome checklist lacks: {needle}")

    for manifest in (CLAUDE / ".claude-plugin" / "plugin.json", CODEX / ".codex-plugin" / "plugin.json"):
        check(json.loads(manifest.read_text(encoding="utf-8"))["version"] == "0.9.21", f"{manifest.name} is not at 0.9.21")
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
    print("PASS: both follow-up-run skills handle thread evidence as designed (Claude reads it from data, Codex cannot) outcome, no-pressure, repair and integrity rules are stated, the follow-up queue is the working read of the scheduled routine, a conversation that asks for contact later is booked with a day Mosaico validates (never today from a clock), booked work waits, and the version is 0.9.18.")


if __name__ == "__main__":
    main()
