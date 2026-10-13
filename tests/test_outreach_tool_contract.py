#!/usr/bin/env python3
"""Fail when either Outreach plugin names a tool absent from the application registry."""

from __future__ import annotations

import argparse
import os
import re
from pathlib import Path


TOOL_REFERENCE = re.compile(r"`(outreach_[a-z0-9_]+)`")
REGISTERED_TOOL = re.compile(
    r"(?:name|toolName):\s*'(?P<name>outreach_[a-z0-9_]+)'"
    r"|OUTREACH_EVIDENCE_TOOL\s*=\s*'(?P<evidence>outreach_[a-z0-9_]+)'"
    # A tool whose registry name is an exported shared constant (0.9.16: the follow-up queue read).
    r"|export const OUTREACH_[A-Z_]+_TOOL\s*=\s*'(?P<constant>outreach_[a-z0-9_]+)'"
)
REGISTRY_FILES = (
    "features/outreach/server/outreach-mcp-registry.ts",
    "features/outreach/server/outreach-transfer-tool.ts",
    "features/outreach/server/outreach-transfer-batch-tool.ts",
    # The connection-evidence tool's name is a shared constant, not a literal in the registry.
    "features/outreach/shared/outreach-connection-evidence.ts",
    # The follow-up queue read's name is the exported constant OUTREACH_FOLLOW_UP_QUEUE_TOOL (0.9.16).
    "features/outreach/shared/outreach-follow-up-queue.ts",
)
REQUIRED_TOOLS = {"outreach_start_run"}


def referenced_tools(skill_root: Path) -> set[str]:
    return {
        tool
        for skill in skill_root.glob("*/SKILL.md")
        for tool in TOOL_REFERENCE.findall(skill.read_text(encoding="utf-8"))
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--app-repo",
        type=Path,
        default=Path(os.environ.get("MOSAICO_APP_REPO") or Path(__file__).resolve().parents[2] / "mosaico-app"),
        help="Path to the mosaico-app checkout that owns the MCP registry (default: $MOSAICO_APP_REPO, else ../mosaico-app).",
    )
    args = parser.parse_args()
    plugin_root = Path(__file__).resolve().parents[1] / "plugins"
    codex = referenced_tools(plugin_root / "mosaico-codex" / "skills")
    claude = referenced_tools(plugin_root / "mosaico-claude" / "skills")
    if codex != claude:
        raise SystemExit(
            "Provider Outreach tool references differ: "
            f"Codex-only={sorted(codex - claude)}, Claude-only={sorted(claude - codex)}"
        )

    registered: set[str] = set()
    for relative in REGISTRY_FILES:
        registry_path = args.app_repo.resolve() / relative
        if not registry_path.is_file():
            raise SystemExit(f"Application Outreach registry not found: {registry_path}")
        registered |= {
            match.group("name") or match.group("evidence") or match.group("constant")
            for match in REGISTERED_TOOL.finditer(registry_path.read_text(encoding="utf-8"))
        }
    unused = REQUIRED_TOOLS - codex
    if unused:
        raise SystemExit(f"Skills never start a run: missing {sorted(unused)}")
    for skill in plugin_root.glob("*/skills/*/SKILL.md"):
        for number, line in enumerate(skill.read_text(encoding="utf-8").splitlines(), 1):
            # Only a prohibition, or (0.9.11) the read of a colleague's day and the draft call that carries no ownerUserId.
            if "ownerUserId" in line and not re.search(r"(Never|Do not) pass|no `ownerUserId`|as `ownerUserId`|as ownerUserId", line):
                raise SystemExit(f"{skill}:{number} tells the model about ownerUserId")
    # 0.9.17: the fields the Follow-up routine relies on (server release 20261013a) exist in the application.
    app = args.app_repo.resolve()
    registry_text = (app / "features/outreach/server/outreach-mcp-registry.ts").read_text(encoding="utf-8")
    queue_text = (app / "features/outreach/shared/outreach-follow-up-queue.ts").read_text(encoding="utf-8")
    for stage in ("'fix-address'", "'drop-declined'", "fix_address", "drop_lead", "skippedThisRun", "repairGroup"):
        if stage not in queue_text:
            raise SystemExit(f"The application's follow-up queue lacks {stage} (the 0.9.17 Follow-up routine needs server release 20261013a)")
    for needle in ("skippedThisRun", "linkedDuplicate", "duplicate-linked", "heldBy", "excludedAsFollowUpWork"):
        if needle not in registry_text:
            raise SystemExit(f"The application's MCP registry lacks {needle} (the 0.9.17 Follow-up routine needs server release 20261013a)")
    # 0.9.18: the dated follow-ups the Follow-up routine books (server release 20261013c) exist in the application, and the skill names them.
    dates_text = (app / "features/outreach/shared/outreach-follow-up-dates.ts").read_text(encoding="utf-8")
    for needle in ("sendNotBefore", "nextTouchOn", "scheduledReason", "retry_with_valid_date", "next-touch-scheduled", "follow-up-scheduled", "wait_for_scheduled_day", "returnedToDraft", "followUpRuleViolations"):
        if needle not in registry_text and needle not in dates_text:
            raise SystemExit(f"The application's MCP registry lacks {needle} (the 0.9.18 Follow-up routine needs server release 20261013c)")
    for needle in ("wait_for_scheduled_day", "scheduledReason", "notBefore", "scheduled:"):
        if needle not in queue_text:
            raise SystemExit(f"The application's follow-up queue lacks {needle} (the 0.9.18 Follow-up routine needs server release 20261013c)")
    date_codes = ("date-invalid", "date-not-future", "date-too-far", "date-not-applicable")
    for needle in (*date_codes, "next-touch-scheduled", "next-touch-due", "follow-up-scheduled", "'scheduled-due'", "OUTREACH_FOLLOW_UP_DATE_MAX_DAYS_AHEAD = 365"):
        if needle not in dates_text:
            raise SystemExit(f"The application's follow-up date module lacks {needle} (the 0.9.18 Follow-up routine needs server release 20261013c)")
    for package in ("mosaico-claude", "mosaico-codex"):
        skill_text = (plugin_root / package / "skills" / "mosaico-outreach-follow-up-run" / "SKILL.md").read_text(encoding="utf-8")
        for needle in ("`sendNotBefore`", "`nextTouchOn`", "`notBefore`", "`scheduledReason`", "`wait_for_scheduled_day`", "`retry_with_valid_date`", "`earliestAllowed`", "`latestAllowed`",
                       "`next-touch-scheduled`", "`follow-up-scheduled`", "`next-touch-due`", "`counts.scheduled`", *(f"`{code}`" for code in date_codes)):
            if needle not in skill_text:
                raise SystemExit(f"The {package} follow-up-run skill does not name {needle}, which the application's dated follow-ups use")
    # 0.9.19: the Send invitations run's ordered work list (server release 20261013d) exists in the application, and the skills name it.
    work_text = (app / "features/outreach/server/outreach-send-run-work.ts").read_text(encoding="utf-8")
    run_end_text = (app / "features/outreach/server/outreach-run-end.ts").read_text(encoding="utf-8")
    for needle in (
        "OUTREACH_SEND_RUN_CHECK_CAP = 20", "OUTREACH_SEND_RUN_REFUSED_LIMIT = 2", "OUTREACH_SEND_RUN_OPEN_CODE = 'send-run-open'",
        "['send', 'check', 'draft', 'done']", "recommendedAction", "allowedActions", "remaining", "checksThisRun", "checkCap", "checksLeft", "waitingCount",
        "skippedThisRun", "skippedCount", "verifyBeforeSend", "'end_run'", "work-list-empty", "scriptIdentifier", "verifyAction", "messageId",
        *(f"'{reason}'" for reason in ("in-to-sort", "no-agent", "agent-missing", "no-profile-address", "profile-capture-failed", "check-cap-reached", "refused-twice-this-run")),
    ):
        if needle not in work_text:
            raise SystemExit(f"The application's send-run work list lacks {needle} (the 0.9.19 Send invitations routine needs server release 20261013d)")
    for needle in ("readSendRunWork", "sendRunSummary(work)", "OUTREACH_SEND_RUN_OPEN_CODE", "workflowStatus.sendRun", "sendRun: sendRunWork.work", "sendRun.skippedThisRun", "sendRun.waiting"):
        if needle not in registry_text:
            raise SystemExit(f"The application's MCP registry lacks {needle} (the 0.9.19 Send invitations routine needs server release 20261013d)")
    for needle in ("work-open", "readSendRunWork", "endSendInvitationsRun"):
        if needle not in run_end_text:
            raise SystemExit(f"The application's run-end module lacks {needle} (the 0.9.19 Send invitations routine needs server release 20261013d)")
    for package in ("mosaico-claude", "mosaico-codex"):
        skill_text = (plugin_root / package / "skills" / "mosaico-outreach-invite-run" / "SKILL.md").read_text(encoding="utf-8").replace("`", "")
        for needle in ("sendRun.recommendedAction", "sendRun.next", "sendRun.skippedThisRun", "sendRun.waiting", "send-run-open", "sendRun.phase", "end_run",
                       "verify_connection", "draft_invitation_messages", "send_approved_invitations"):
            if needle not in skill_text:
                raise SystemExit(f"The {package} invite-run skill does not name {needle}, which the application's send-run work list uses")
    claude_routine = (plugin_root / "mosaico-claude" / "skills" / "mosaico-outreach-invite-run" / "SKILL.md").read_text(encoding="utf-8").replace("`", "")
    for needle in ("sendRun.remaining", "sendRun.checksThisRun", "sendRun.checkCap", "next.verifyAction"):
        if needle not in claude_routine:
            raise SystemExit(f"The mosaico-claude invite-run skill does not name {needle}, which the application's send-run work list uses")
    missing = codex - registered
    if missing:
        raise SystemExit(
            "Plugin references unavailable Outreach MCP tools: "
            + ", ".join(sorted(missing))
        )
    print(
        f"PASS: {len(codex)} Outreach tools referenced identically by Codex and Claude "
        "are registered by mosaico-app."
    )


if __name__ == "__main__":
    main()
