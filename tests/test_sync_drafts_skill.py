#!/usr/bin/env python3
"""0.9.13: Source leads writes no invitation drafts; Sync data writes the missing ones from `draftsToWrite`.

The application owns the list, its recommended action and the refusal (ADR-0005): a draft write inside any sourcing run is refused
with `sourcing-writes-no-drafts`, and `outreach_get_day` (in `workflowStatus`) and `outreach_get_follow_ups` return `draftsToWrite`.
These checks pin that the skills only follow that list: Source leads never attempts a draft and treats the refusal as expected, the
Sync data routine writes drafts for the owner's own Leads from the list, never approves or sends one, and the installer stamps the
Sync data and Source leads texts 0.9.13 while Repair is untouched.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLAUDE = ROOT / "plugins" / "mosaico-claude"
CODEX = ROOT / "plugins" / "mosaico-codex"

LIST_FIELDS = ("count", "entries", "leadId", "name", "agentId", "day", "action", "writtenBy", "writableInThisRun", "allowedActions", "recommendedAction", "note")
OPTIONAL_APP_NEEDLES = (
    "SOURCING_WRITES_NO_DRAFTS_CODE = 'sourcing-writes-no-drafts'",
    "DRAFT_INVITATION_ACTION = 'draft_invitation_messages'",
    "readonly writableInThisRun: boolean",
    "readonly recommendedAction: typeof DRAFT_INVITATION_ACTION | 'none'",
    "readonly leadId: string",
    "readonly agentId: string | null",
)


def check(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL: {message}")


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def flat(text: str) -> str:
    return " ".join(text.replace("`", "").split())


def section(text: str, heading: str) -> str:
    match = re.search(rf"^## {re.escape(heading)}\n(.*?)(?=^## |\Z)", text, re.S | re.M)
    check(match is not None, f"missing section {heading}")
    return match.group(1)


def main() -> None:
    for package, root in (("Claude", CLAUDE), ("Codex", CODEX)):
        raw = read(root / "skills" / "mosaico-outreach-invite-run" / "SKILL.md")
        text = flat(raw)

        # 1. Source leads: finds, saves, places, ends. It never writes a draft and takes the refusal as expected.
        sourcing = flat(section(raw, "Source Leads"))
        for needle in (
            "never writes an invitation draft, for its own Leads or a colleague's",
            "Mosaico refuses a draft write inside any sourcing run with sourcing-writes-no-drafts",
            "Do not write any invitation draft, for your Lead or hers",
            "sourcing-writes-no-drafts (state blocked, recommended action continue_with_next_lead), that is expected and not a failure",
            "nothing was saved, the Lead stays saved and placed; continue with the next Lead",
            "its writableInThisRun is false and its recommendedAction is none",
            "recommends end_run or end_run_days_full",
            "nothing is left to verify or sort",
        ):
            check(needle in sourcing, f"{package} Source Leads section lacks: {needle}")
        for gone in ("Source Leads and prepare drafts", "Source Leads only", "source Leads and prepare invitation drafts", "prepare invitation drafts", "Draft a colleague's invitation", "lead-awaiting-owner-check", "colleague-draft-invite-only", "verify or draft"):
            check(gone not in text, f"{package} invite-run skill still holds: {gone}")
        check("Write the missing outbound Invite draft" not in text and "write a missing invitation draft" not in text.lower(), f"{package} invite-run skill still tells a sourcing run to write a draft")

        # 2. The Source leads routine: one action, no drafts, the refusal is expected.
        routine = flat(raw[raw.index("## Source leads routine"):])
        check('the action is "source Leads only"' in routine, f'{package} Source leads routine does not name the one action "source Leads only"')
        check("It never writes invitation drafts, approves, sends or messages; the Sync data schedule" in routine, f"{package} Source leads routine intro still allows drafts")
        step3 = routine[routine.index("Step 3."):routine.index("Step 4.")]
        for needle in ("writes no invitation draft, for your Leads or a colleague's", "draftsToWrite list", "do not attempt one", "sourcing-writes-no-drafts", "expected and not a failure", "continue_with_next_lead", "Never approve or send an invitation"):
            check(needle in step3, f"{package} Source leads Step 3 lacks: {needle}")
        step4 = routine[routine.index("Step 4."):routine.index("Step 5.")]
        check("nothing is left to verify or sort, or when Mosaico recommends end_run or end_run_days_full" in step4, f"{package} Source leads Step 4 does not stop at end_run")
        step5 = routine[routine.index("Step 5."):]
        check("drafts written" not in step5 and "sourcing-writes-no-drafts is not reported as a failure" in step5, f"{package} Source leads Step 5 still reports drafts or fails on the refusal")
        report = flat(section(raw, "Report a sourcing run"))
        check("no drafts: a Source leads run writes none" in report and "never reported as a failure or a blocker" in report, f"{package} sourcing report does not treat the refusal as expected")

        # 3. The drafting procedure follows the application's list and recommended action; it never rebuilds either.
        drafts_raw = section(raw, "Write missing invitation drafts")
        drafts = flat(drafts_raw)
        for field in LIST_FIELDS:
            check(field in drafts, f"{package} 'Write missing invitation drafts' lacks the field name: {field}")
        for needle in (
            "the Lead owner's work, done in the Sync data routine for the person's own Leads only",
            "A Source leads run never does it",
            "outreach_get_day for today with intent: send_approved_invitations",
            "outreach_get_follow_ups carries the same list as a top-level draftsToWrite",
            "never rebuild it from other reads or from memory",
            "Work the list only when it is draft_invitation_messages. When it is none, write nothing",
            "outreach_get_agents with no arguments",
            "messageInstructions", "messagingChecklist", "checklistReview",
            "outreach_record_message", "kind invite", "direction outbound", "sentAt null", "Pass no ownerUserId",
            "for no other Lead",
            "Never approve, send or mark sent a draft you wrote",
            "do not try it again in this run",
        ):
            check(needle in drafts, f"{package} 'Write missing invitation drafts' lacks: {needle}")
        check(not re.search(r"ownerUserId", drafts_raw.replace("Pass no `ownerUserId`", "")), f"{package} 'Write missing invitation drafts' tells the model about ownerUserId")
        both = flat(section(raw, "Both"))
        check("Complete **Write missing invitation drafts** first" in both and "Never approve a newly created draft automatically" in both and "Sourcing is never part of this" in both, f"{package} Both section does not draft first, send approved only, and keep sourcing out")
        send = flat(section(raw, "Send approved invitations"))
        check("outreach_record_message" not in send, f"{package} Send approved invitations may write a draft")
        start = flat(raw[raw.index("## Start the run"):raw.index("## Source Leads\n")])
        check("Sourcing is always its own run; writing drafts and sending share one send_approved_invitations run" in start, f"{package} Start the run does not keep sourcing apart from drafting and sending")
        check("missing invitation drafts" in flat(raw.split("---", 2)[1]), f"{package} invite-run description does not name drafting")

    # 4. Sync data routine (Claude): drafts first in the invitation step, from the application's list, own Leads only, never approved or sent.
    follow = read(CLAUDE / "skills" / "mosaico-outreach-follow-up-run" / "SKILL.md")
    sync = flat(section(follow, "Sync data routine"))
    for needle in (
        "It does not source or transfer",
        "It writes the missing invitation drafts for the person's own Leads, from the draftsToWrite list Mosaico gives it, and never approves or sends them",
        'then invitations for today with the actions "write missing invitation drafts" and "send approved invitations"',
        'the selected actions "write missing invitation drafts", then "send approved invitations"',
        "Write missing invitation drafts\" section says",
        "draftsToWrite on the day read (outreach_get_follow_ups carries the same list) and follow its recommendedAction",
        "write a draft with sentAt null only for an entry on that list (always one of your own Leads), never approve or send a draft, and never write one for any other Lead",
        "invitation drafts written and Leads skipped for drafting, each with its reason",
    ):
        check(needle in sync, f"Sync data routine lacks: {needle}")
    check("draft invitations; the Source leads schedule" not in sync and "does not source, transfer or draft" not in sync, "Sync data routine still says it does not draft invitations")
    note = flat(section(follow, "Missing invitation drafts are not follow-up work"))
    check("draftsToWrite" in note and "do not act on it" in note and "a Source leads run never does" in note, "follow-up-run lacks the note that draftsToWrite is not follow-up work")
    codex_follow = read(CODEX / "skills" / "mosaico-outreach-follow-up-run" / "SKILL.md")
    check("Sync data routine" not in codex_follow, "Codex follow-up-run holds a Sync data routine")

    # 5. The installer: the Sync data and Source leads texts carry the 0.9.13 stamp, Repair keeps 0.9.6, nothing says 0.9.12 any more.
    installer_raw = read(CLAUDE / "skills" / "mosaico-outreach-schedule-install" / "SKILL.md")
    texts = re.findall(r"```text\n(.*?)\n```", installer_raw, re.S)
    check(len(texts) == 4, f"Claude installer must hold four schedule texts, found {len(texts)}")
    sync_text, own_text, colleagues_text, repair_text = texts
    for label, text, section_name in (("Sync data", sync_text, "Sync data routine"), ("Source leads (own)", own_text, "Source leads routine"), ("Source leads (colleagues)", colleagues_text, "Source leads routine")):
        check("(0.9.13 or later)" in text and f'is older than 0.9.13 or has no "{section_name}" section' in text, f"the {label} text is not stamped 0.9.13")
        check("0.9.12" not in text, f"the {label} text still names 0.9.12")
        check(len(text.split()) <= 200, f"the {label} text is not thin")
        for procedure in ("outreach_", "draftsToWrite", "Step 1", "checklistReview"):
            check(procedure not in text, f"the {label} text holds procedure: {procedure}")
    check('"write missing invitation drafts"' in sync_text and '"send approved invitations"' in sync_text and '"one pass per thread"' in sync_text, "the Sync data text lacks its three actions")
    check('action: "source Leads only"' in own_text and 'action: "source Leads only"' in colleagues_text, 'a Source leads text does not name the one action "source Leads only"')
    check("(0.9.6 or later)" in repair_text, "the Repair stamp changed")
    codex_installer_raw = read(CODEX / "skills" / "mosaico-outreach-schedule-install" / "SKILL.md")
    codex_texts = re.findall(r"```text\n(.*?)\n```", codex_installer_raw, re.S)
    check(len(codex_texts) == 1 and "(0.9.13 or later)" in codex_texts[0] and 'action: "source Leads only"' in codex_texts[0], "the Codex Source leads text is not stamped 0.9.13 with the one action")
    check("### Update the standing answers in place" in installer_raw, "the installer lost the update-in-place path")
    flat_installer = " ".join(installer_raw.split())
    check('a Sync data schedule that does not yet name the action "write missing invitation drafts"' in flat_installer and 'still names the action "source Leads and prepare invitation drafts"' in flat_installer, "the installer does not move older Sync data or Source leads texts in place")

    # 6. Overview skills.
    for package, root in (("Claude", CLAUDE), ("Codex", CODEX)):
        overview = flat(read(root / "skills" / "mosaico-outreach" / "SKILL.md"))
        check("A Source run never writes drafts: the Lead owner's Sync data run does" in overview and "Write missing invitation drafts" in overview and "draftsToWrite" in overview, f"{package} overview skill does not describe who writes drafts")
        check("save personalized invitation drafts" not in overview, f"{package} overview skill still says Source saves drafts")

    # 7. Versions and the changelog entry that holds the release gate.
    for manifest in (CLAUDE / ".claude-plugin" / "plugin.json", CODEX / ".codex-plugin" / "plugin.json"):
        check(json.loads(read(manifest))["version"] == "0.9.13", f"{manifest.name} is not at 0.9.13")
    readme = read(ROOT / "README.md")
    check(readme.index("### 0.9.13") < readme.index("### 0.9.12"), "README changelog lacks 0.9.13 above 0.9.12")
    entry = flat(readme[readme.index("### 0.9.13"):readme.index("### 0.9.12")])
    for needle in (
        "mosaicohr-com/mosaico#1834", "Do not publish or install this plugin before that release is live on main-v2",
        "sourcing-writes-no-drafts", "continue_with_next_lead", "end_run", "draftsToWrite", "draft_invitation_messages", "writableInThisRun",
        "Write missing invitation drafts", "outreach_get_agents", "checklistReview", "never approves or sends a draft", "stamped 0.9.13 or later", "Repair is unchanged",
    ):
        check(needle in entry, f"README 0.9.13 entry lacks: {needle}")
    check("tests/test_sync_drafts_skill.py" in readme, "README does not list this test")

    # 8. When the application checkout is at hand, the server still carries what this release relies on.
    app = os.environ.get("MOSAICO_APP_REPO")
    if app:
        server = Path(app) / "features" / "outreach" / "server"
        module, registry = server / "outreach-drafts-to-write.ts", server / "outreach-mcp-registry.ts"
        if module.is_file() and registry.is_file():
            source = read(module)
            for needle in OPTIONAL_APP_NEEDLES:
                check(needle in source, f"the application's drafts module lacks: {needle}")
            registry_text = read(registry)
            check("draftsToWrite: draftsToWrite(" in registry_text and "SOURCING_WRITES_NO_DRAFTS" in registry_text, "the application registry does not return draftsToWrite or refuse sourcing drafts")

    print("PASS: Source leads saves and places Leads only and treats sourcing-writes-no-drafts as expected; Sync data writes the missing invitation drafts from draftsToWrite for its own Leads and never approves or sends; the Sync data and Source leads texts are stamped 0.9.13.")


if __name__ == "__main__":
    main()
