#!/usr/bin/env python3
"""The invite-run skills carry the Sales Navigator colleague check as Mosaico defines it, and nothing more.

Claude runs the approved script before saving a candidate for a colleague and passes its output unchanged as
colleagueConnectionEvidence; Mosaico decides (skip, save as unknown, or ask again). Codex ships no browser scripts, so it only
states that it cannot run the check. The skills never make the model the judge: no connection state is set from the check, a
"not found" is never "not connected", and a skip is never a failure. The wording is Mosaico's own codes, checked against the
contract of the application's colleague-check module.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLAUDE = ROOT / "plugins" / "mosaico-claude"
CODEX = ROOT / "plugins" / "mosaico-codex"
SCRIPT = "linkedin-salesnav-colleague-connection.js"
REASONS = ("evidence-missing", "evidence-altered", "colleague-evidence-malformed", "colleague-evidence-inconsistent", "observation-stale",
           "observation-time-invalid", "colleague-mismatch", "candidate-mismatch", "candidate-is-colleague")
NOTES = ("colleague-check-negative-unproven", "colleague-check-unavailable", "colleague-check-cap-reached")


def check(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL: {message}")


def flat(text: str) -> str:
    return re.sub(r"\s+", " ", text)


def section(text: str, heading: str) -> str:
    match = re.search(rf"^## {re.escape(heading)}\n(.*?)(?=^## |\Z)", text, re.S | re.M)
    check(match is not None, f"missing section {heading}")
    return match.group(1)


def check_0911(claude_text: str, codex_text: str) -> None:
    """0.9.11: the colleague check carries proof fields and a send waits for the owner's own evidence. 0.9.13: a proven negative is drafted by her own Sync data run, never by the sourcing run."""
    colleague = flat(section(claude_text, "Check a candidate against the colleague"))
    for needle in (
        "`complete`, `controlTotal`, `visibility` and `unreadableRows`", "send a `null` as `null`", "`colleague-check-negative-proven`", "verified not connected by the colleague check",
        "`awaitingOwnerCheck` true", "This run writes no draft", "her own Sync data run writes her invitation from its `draftsToWrite` list", "`colleague-check-negative-unproven`",
        "stays unverified and undrafted", "Continue sourcing", "`evidence-owner-mismatch`", "never recommends `verify_connection`", "never passed to `outreach_record_connection_evidence`",
    ):
        check(needle in colleague, f"Claude colleague check lacks the 0.9.11 sentence: {needle}")
    check("goes through **Capture connection evidence** as before" not in claude_text, "the colleague check still sends a colleague's Lead through Capture connection evidence")
    check("then run **Capture connection evidence** for it. Do not write any invitation draft" not in flat(claude_text), "Source Leads only still captures evidence for a colleague's Lead")
    check("## Draft a colleague's invitation" not in claude_text and "`lead-awaiting-owner-check`" not in claude_text and "`colleague-draft-invite-only`" not in claude_text, "the skill still has a sourcing-time colleague draft or its refusals")
    for scope in ("Source Leads",):
        text = flat(section(claude_text, scope))
        check("never run **Capture connection evidence**" in text or "never run **Capture connection evidence** for her Lead" in text.replace("and never run", "never run"), f"{scope} does not forbid connection evidence for a colleague's Lead")
        check("Do not write any invitation draft, for your Lead or hers" in text and "`sourcing-writes-no-drafts`" in text, f"{scope} may write a colleague's draft")
    check("`own-evidence-required`" in flat(section(claude_text, "Send approved invitations")) and "`colleague-verified-needs-own-check`" in flat(section(claude_text, "Send approved invitations")), "Send approved invitations lacks the own-evidence rule")
    report = flat(section(claude_text, "Report a sourcing run"))
    for needle in ('"verified not connected by colleague check (proven)"', '"unproven, awaiting her Sync"', "no drafts: a Source leads run writes none"):
        check(needle in report, f"Claude sourcing report lacks: {needle}")
    routine = flat(section(claude_text, "Source leads routine"))
    for needle in (
        "complete, controlTotal, visibility and unreadableRows", "colleague-check-negative-proven", "colleague-check-negative-unproven", "stays undrafted, so continue sourcing", "evidence-owner-mismatch",
        "her own Sync data run drafts her invitation",
        'as "verified not connected by colleague check (proven)"', 'as "unproven, awaiting her Sync"',
    ):
        check(needle in routine, f"Claude Source leads routine lacks: {needle}")
    check("Never run the connection-evidence script for a colleague's Lead" in routine, "the routine does not forbid connection evidence for a colleague's Lead")
    # Sync data (follow-up-run): colleague-verified Leads are verified from the run's own pane; a send that needs the owner's own evidence gets it.
    follow = (CLAUDE / "skills" / "mosaico-outreach-follow-up-run" / "SKILL.md").read_text(encoding="utf-8")
    sync = flat(section(follow, "Sync data routine"))
    for needle in ("colleague-verified-needs-own-check", "verify them from your own pane like any other unverified Lead", "outreach_mark_message_sent answers own-evidence-required", "reread the day"):
        check(needle in sync, f"Sync data routine lacks: {needle}")
    check("`colleague-verified-needs-own-check`" in flat(section(follow, "Check for new follow-ups")), "Check for new follow-ups lacks the colleague-verified reason")
    # Codex: the same rules in words, no script.
    codex = flat(section(codex_text, "The colleague check (Claude only)"))
    for needle in ("`colleague-check-negative-proven`", "`colleague-check-negative-unproven`", "`own-evidence-required`", "never records connection evidence for a colleague's Lead"):
        check(needle in codex, f"Codex colleague note lacks: {needle}")
    codex_follow = (CODEX / "skills" / "mosaico-outreach-follow-up-run" / "SKILL.md").read_text(encoding="utf-8")
    check("`colleague-verified-needs-own-check`" in flat(section(codex_follow, "Check for new follow-ups")), "Codex follow-up-run lacks the colleague-verified reason")
    check("browser/" not in codex, "the Codex colleague note names a browser script")
    # Overview (Claude): the proven negative, the send guard and the accepted risk.
    overview = flat((CLAUDE / "skills" / "mosaico-outreach" / "SKILL.md").read_text(encoding="utf-8"))
    for needle in ("`complete`, `controlTotal`, `visibility` and `unreadableRows`", "a proven negative", "The send guard", "`own-evidence-required`", "`evidence-owner-mismatch`", "The risk accepted", "nothing goes out before her own check"):
        check(needle in overview, f"Claude overview skill lacks: {needle}")
    # Thin schedule texts keep their minimum version: no new routine section, the procedure lives in the installed plugin.
    for package in (CLAUDE, CODEX):
        installer = flat((package / "skills" / "mosaico-outreach-schedule-install" / "SKILL.md").read_text(encoding="utf-8"))
        # 0.9.13: the Sync data text, both Claude lane texts and the Codex Source leads text move to 0.9.13 (drafts move from Source leads to Sync data).
        check("0.9.13 or later" in installer and "0.9.9 or later" not in installer and "0.9.12 or later" not in installer and "0.9.11 or later" not in installer, f"{package.name} schedule-install lacks the 0.9.13 stamp")
    # README: the changelog entry, the script description and the colleague-check paragraph.
    readme_raw = (ROOT / "README.md").read_text(encoding="utf-8")
    check(readme_raw.index("### 0.9.11") < readme_raw.index("### 0.9.10"), "README changelog lacks 0.9.11 above 0.9.10")
    entry = flat(readme_raw[readme_raw.index("### 0.9.11"):readme_raw.index("### 0.9.10")])
    for needle in (
        "`complete`", "`controlTotal`", "`visibility`", "`unreadableRows`", "`paging.total`", "`visibility` is never `hidden`", "no hidden-list marker is known", "`colleague-check-negative-proven`", "`colleague-check-negative-unproven`",
        "`colleague-verified-needs-own-check`", "`own-evidence-required`", "pull request 1822", "still say \"0.9.9 or later\"", "update the plugin to 0.9.11 or later",
    ):
        check(needle in entry, f"README 0.9.11 entry lacks: {needle}")
    readme = flat(readme_raw)
    check("The colleague check." in readme and "The risk accepted" in readme and "the send guard" in readme and "complete, controlTotal, visibility, unreadableRows }` (0.9.11 added the last four" in readme, "README lacks the colleague-check paragraph or the script's new fields")


def main() -> None:
    claude_text = (CLAUDE / "skills" / "mosaico-outreach-invite-run" / "SKILL.md").read_text(encoding="utf-8")
    codex_text = (CODEX / "skills" / "mosaico-outreach-invite-run" / "SKILL.md").read_text(encoding="utf-8")
    colleague = flat(section(claude_text, "Check a candidate against the colleague"))
    for needle in (
        "`workflowStatus.colleagueChecks`", "`allowed: true`", "right before `outreach_save_lead`", "`<candidate>`", "leave the colleague's identifier exactly as Mosaico wrote it",
        f"// mosaico run {SCRIPT} PUBLIC_IDENTIFIER=<candidate> COLLEAGUE_IDENTIFIER=", "never print, retype, paraphrase, reorder, shorten or extend it", "Sales Navigator page",
        "`colleagueConnectionEvidence`", "exactly as returned (every field, `integrity` included)", "Mosaico's answer is final",
        "`skipped` with code `already-connected-to-colleague`", "`continue_sourcing`", "not a failure and does not count toward the target",
        "`blocked` with code `colleague-check-required`", "`run_colleague_check`", "never retype or edit the old one", "Do this once per candidate",
        "**not** proof that they are not connected", "never write \"not connected\"", "Never decide it from the screen", "it sets none",
        "never passed to `outreach_record_connection_evidence`", "A Lead for the run owner never needs it",
    ):
        check(needle in colleague, f"Claude invite-run colleague check lacks: {needle}")
    for code in (*REASONS, *NOTES):
        check(f"`{code}`" in colleague, f"Claude invite-run colleague check does not name {code}")
    check("ownerUserId" not in colleague, "the colleague check tells the model about ownerUserId")
    # Where the check applies, and that the evidence goes to Mosaico unchanged like every other script's.
    for scope in ("Source Leads",):
        check("**Check a candidate against the colleague**" in flat(section(claude_text, scope)), f"{scope} does not point at the colleague check")
    check("`colleagueConnectionEvidence`" in flat(section(claude_text, "Script output goes to Mosaico exactly as returned")), "the exact-as-returned section does not list colleagueConnectionEvidence")
    # The report counts the skips per owner from Mosaico's data, and never calls them failures.
    for text, label in ((claude_text, "Claude"), (codex_text, "Codex")):
        report = flat(section(text, "Report a sourcing run"))
        check('"skipped as already connected to <owner>: N"' in report and "workflowStatus.colleagueSkips" in report, f"{label} sourcing report does not count the colleague skips from Mosaico")
    check("never failures" in flat(section(claude_text, "Report a sourcing run")) and "not \"not connected\"" in flat(section(claude_text, "Report a sourcing run")), "the Claude report does not say skips are not failures and unknown is not not-connected")
    # Codex cannot run it and never works around the block.
    codex = flat(section(codex_text, "The colleague check (Claude only)"))
    for needle in ("Codex cannot run that check", "Never make up evidence", "`colleague-check-required`", "do not retry it", "need a Claude run", "`already-connected-to-colleague`"):
        check(needle in codex, f"Codex invite-run colleague note lacks: {needle}")
    check("browser/" not in codex and SCRIPT not in codex_text, "the Codex package refers to a browser script it does not ship")

    # The Source leads routine section (the schedule text is thin and names it): the Claude section names the script and the directive and
    # reports the skips; the Codex section says it cannot run the check. The schedule text itself is checked in test_schedule_install_skill.py.
    for package, root in (("Claude", CLAUDE), ("Codex", CODEX)):
        source = flat(section((root / "skills" / "mosaico-outreach-invite-run" / "SKILL.md").read_text(encoding="utf-8"), "Source leads routine"))
        check("colleagueSkips" in source and "skipped as already connected to each owner" in source, f"{package} Source leads routine lacks the skip count")
        if package == "Claude":
            check("browser/linkedin-salesnav-colleague-connection.js" in source and f"// mosaico run {SCRIPT} PUBLIC_IDENTIFIER=<the candidate's identifier> COLLEAGUE_IDENTIFIER=" in source
                  and "colleagueConnectionEvidence" in source and "https://www.linkedin.com/sales/home" in source and "workflowStatus.colleagueChecks" in source,
                  "Claude Source leads routine does not describe the colleague check")
        else:
            check("cannot run the colleague-connection check" in source and "colleague-check-required" in source and "Claude run" in source, "Codex Source leads routine does not say it cannot run the check")
    # The overview skill lists the new script's output among those passed unchanged.
    check("the Sales Navigator colleague check" in flat((CLAUDE / "skills" / "mosaico-outreach" / "SKILL.md").read_text(encoding="utf-8")), "the Claude overview skill does not list the colleague check output")
    check_0911(claude_text, codex_text)
    # Manifests and the README.
    for manifest in (CLAUDE / ".claude-plugin" / "plugin.json", CODEX / ".codex-plugin" / "plugin.json"):
        check(json.loads(manifest.read_text(encoding="utf-8"))["version"] == "0.9.13", f"{manifest.name} is not at 0.9.13")
    readme = flat((ROOT / "README.md").read_text(encoding="utf-8"))
    check("### 0.9.5" in readme and "### 0.9.4" in readme and SCRIPT in readme and "holds the six approved capture scripts" in readme and "already connected to the colleague" in readme, "the README lacks the 0.9.4 entry or the script's description")
    print("PASS: the invite-run skills run the colleague check before a colleague save, pass its output unchanged, handle every Mosaico answer, and never treat 'not found' as 'not connected'; Codex says it cannot run it.")


if __name__ == "__main__":
    main()
