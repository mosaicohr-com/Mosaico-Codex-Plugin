#!/usr/bin/env python3
"""Fail when either Outreach plugin names a tool, step field or routine section that the application does not have.

Plugin side (always checked): both packages name the same Outreach tools, none tells the model to pass ownerUserId, and every skill that
starts a run says so. Application side (pass --app-repo, or set MOSAICO_APP_REPO, to a checkout or export of mosaico stage-v2): every tool
the skills name is registered, Repair's tool is not, the step block carries the fields the skills follow, the end answer carries the report
the skills give unchanged, the routine setup carries the fields the installer reads, the plugin and catalogue versions match the ones the
skills and manifests name, and every routine section the server's routine texts point at is a heading in the named skill.

Without --app-repo the application side is skipped and says so. Export what is needed without checking anything out:
  git -C <mosaico-app> archive origin/stage-v2 features/outreach | tar -x -C <dir>
"""

from __future__ import annotations

import argparse
import os
import re
from pathlib import Path

from skill_text import CATALOGUE_VERSION, CLAUDE, INVITE, FOLLOW_UP, PACKAGES, ROOT, VERSION, check, read, skill

TOOL_REFERENCE = re.compile(r"`(outreach_[a-z0-9_]+)`")
REGISTERED_TOOL = re.compile(
    r"(?:name|toolName):\s*'(?P<name>outreach_[a-z0-9_]+)'"
    r"|OUTREACH_EVIDENCE_TOOL\s*=\s*'(?P<evidence>outreach_[a-z0-9_]+)'"
    r"|export const OUTREACH_[A-Z_]+_TOOL\s*=\s*'(?P<constant>outreach_[a-z0-9_]+)'"
)
REGISTRY_FILES = (
    "features/outreach/server/outreach-mcp-registry.ts",
    "features/outreach/server/outreach-transfer-tool.ts",
    "features/outreach/server/outreach-transfer-batch-tool.ts",
    "features/outreach/server/outreach-lead-load.ts",
    "features/outreach/shared/outreach-connection-evidence.ts",
    "features/outreach/shared/outreach-follow-up-queue.ts",
)
REQUIRED_TOOLS = {"outreach_start_run", "outreach_end_run", "outreach_get_routine_setup", "outreach_record_routine_schedule"}
RETIRED_TOOLS = {"outreach_get_repair_queue"}
STEP_FIELDS = ("stepId", "action", "target", "call", "evidence", "agentInstructions", "then", "guidance", "guidanceVersion", "supplyAlso", "directive", "blocker")
SETUP_FIELDS = ("routinesToInstall", "routinesToUpdate", "retiredRoutines", "catalogueVersion", "minimumPluginVersion", "routineText", "defaultSchedule", "recommendedAction",
                "remove_retired_routines", "register_linkedin_identity", "complete")


def referenced_tools(skill_root: Path) -> set[str]:
    return {tool for path in skill_root.glob("*/SKILL.md") for tool in TOOL_REFERENCE.findall(read(path))}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--app-repo", type=Path, default=Path(os.environ["MOSAICO_APP_REPO"]) if os.environ.get("MOSAICO_APP_REPO") else None,
                        help="A mosaico stage-v2 checkout or export (default: $MOSAICO_APP_REPO; without one the application side is skipped).")
    args = parser.parse_args()

    codex = referenced_tools(PACKAGES["Codex"] / "skills")
    claude = referenced_tools(PACKAGES["Claude"] / "skills")
    check(codex == claude or codex <= claude, f"Codex names Outreach tools that Claude does not: {sorted(codex - claude)}")
    check(REQUIRED_TOOLS & {"outreach_start_run", "outreach_end_run"} <= codex, "the skills never start or end a run")
    check({"outreach_get_routine_setup", "outreach_record_routine_schedule"} <= claude, "the Claude installer does not name the routine setup and schedule tools")
    check(not (RETIRED_TOOLS & (codex | claude)), f"a skill names a retired tool: {sorted(RETIRED_TOOLS & (codex | claude))}")
    for skill_file in ROOT.glob("plugins/*/skills/*/SKILL.md"):
        text = " ".join(read(skill_file).replace("`", "").split())
        for match in re.finditer("ownerUserId", text):
            before = text[max(0, match.start() - 70):match.start()]
            if not re.search(r"(?:Never|never|Do not) pass |Owner or Admin (?:adds|may [^.]*with) |for your own", before):
                raise SystemExit(f"FAIL: {skill_file} tells the model about ownerUserId: ...{before}ownerUserId")

    if args.app_repo is None:
        print(f"PASS: {len(claude)} Outreach tools named by Claude and {len(codex)} by Codex, none retired, none told to pass ownerUserId "
              "(pass --app-repo to check the application contract too).")
        return

    app = args.app_repo.resolve()
    registered: set[str] = set()
    for relative in REGISTRY_FILES:
        path = app / relative
        check(path.is_file(), f"Application Outreach file not found: {path}")
        registered |= {m.group("name") or m.group("evidence") or m.group("constant") for m in REGISTERED_TOOL.finditer(read(path))}
    missing = (codex | claude | REQUIRED_TOOLS) - registered
    check(not missing, f"Plugin references unavailable Outreach MCP tools: {sorted(missing)}")
    check(not (RETIRED_TOOLS & registered), f"the application still registers a retired tool: {sorted(RETIRED_TOOLS & registered)}")

    registry = read(app / "features/outreach/server/outreach-mcp-registry.ts")
    for field in ("clientCapabilities", "browserEvidence", "identityEvidence", "observedLinkedInProfile", "onBehalfOfMemberId", "sourcingScope", "inspect_day",
                  "follow_up_pass", "manage_leads", "send_approved_invitations", "source_invitation_leads", "linkedInIssue", "nextAction", "alreadyWaiting"):
        sources = (registry, read(app / "features/outreach/server/outreach-lead-load.ts"), read(app / "features/outreach/server/outreach-service.ts"))
        check(any(field in source for source in sources), f"the application's Outreach tools lack {field}")
    step = read(app / "features/outreach/server/outreach-workflow-step.ts")
    for field in STEP_FIELDS:
        check(field in step, f"the application's step block lacks {field}")
    report = read(app / "features/outreach/server/outreach-run-report.ts")
    check("lines" in report and "sections" in report, "the application's run report has no lines and sections")
    setup = read(app / "features/outreach/server/outreach-routine-setup.ts")
    for field in SETUP_FIELDS:
        check(field in setup, f"the application's routine setup lacks {field}")

    # Versions: the plugin version the server names, the catalogue version this plugin expects, and the routine sections the texts point at.
    requirements = read(app / "features/outreach/shared/outreach-setup-requirements.ts")
    check(f"OUTREACH_PLUGIN_VERSION = '{VERSION}'" in requirements, f"the application does not name plugin version {VERSION}")
    catalogue = read(app / "features/outreach/server/outreach-routine-catalogue.ts")
    check(f"OUTREACH_ROUTINE_CATALOGUE_VERSION = '{CATALOGUE_VERSION}'" in catalogue, f"the application's routine catalogue is not at {CATALOGUE_VERSION}, which the installer expects")
    pointed = set(re.findall(r"skill: '([^']+)',\s*section: '([^']+)'", catalogue))
    check(len(pointed) >= 5, f"cannot read the routine sections from the catalogue: {sorted(pointed)}")
    for skill_name, section_name in sorted(pointed):
        check(skill_name.startswith("mosaico:"), f"the catalogue names a skill without the plugin prefix: {skill_name}")
        text = skill("Claude", skill_name.removeprefix("mosaico:"))
        check(re.search(rf"^## {re.escape(section_name)}$", text, re.M) is not None, f"the {skill_name} skill has no '{section_name}' section, which the server's routine text points at")
    print(f"PASS: {len(claude)} Outreach tools named by Claude and {len(codex)} by Codex are registered by the application at {app}, the step block, report and routine setup "
          f"carry the fields the skills follow, the versions ({VERSION}, catalogue {CATALOGUE_VERSION}) match, and every routine section the server points at is a heading in its skill.")


if __name__ == "__main__":
    main()
