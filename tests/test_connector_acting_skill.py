#!/usr/bin/env python3
"""0.9.21: connector acting, the subscription rule, the reseller catalogue and the people tools in the skills.

Mosaico owns the acting session, its 30 minutes, who the calls run as and every refusal (ADR-0005). The skills only say how to read
Mosaico's answers in plain language. These checks pin that both packages name the tools, quote Mosaico's sentences word for word, stop
an Outreach run on the acting refusal (no retry, no way round), repeat a call once after the "session ended" refusal, say that approving
a conversion needs a subscription, and add no Mosaico server, address or token to the plugin (Do-not item 1).

Pass --app-repo (or set MOSAICO_APP_REPO) to also check the application at the live server commit: every tool is registered, every
sentence and argument is the one the application uses, and approve_methodology_conversion is no longer allowance-exempt.
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
VERSION = "0.9.21"

OPERATOR_ONLY = "Outreach and incident tools are not available while your connector is acting as a member of another organisation. End the session first."
ENDED_START = "Your session acting as"
ENDED_TAIL = "This call did not run. Repeat it; it will run as you in"
NO_SUBSCRIPTION = "This organization needs an active Mosaico subscription before the MCP connector can run this tool."
NO_ALLOWANCE = "This organization has no remaining AI allowance for this period."
ALLOWANCE_BUSY = "Another tool call is settling this organization’s AI allowance. Retry this call shortly."

ACTING_TOOLS = ("get_acting_status", "stop_acting")
PEOPLE_TOOLS = ("list_teams", "create_team", "batch_assign_positions", "assign_person_to_flow", "set_person_task_due_date")
RESELLER_TOOLS = ("publish_approved_component_example", "get_approved_components_for_customer", "set_approved_component_availability")
INSTALL_TOOLS = ("list_example_catalogue", "install_flow_example", "install_domain_example", "install_capability_example", "install_approved_domain_example")
NEW_TOOLS = ACTING_TOOLS + PEOPLE_TOOLS + RESELLER_TOOLS + INSTALL_TOOLS

# Each tool the general skill teaches, with the arguments it names: the application file that declares them.
ARGUMENTS = {
    "publish_approved_component_example": ("features/reseller/shared/approved-component-publication.ts", ("projectId", "componentKind", "componentKey", "visibility")),
    "get_approved_components_for_customer": ("features/reseller/shared/approved-component-availability.ts", ("targetOrganizationId",)),
    "set_approved_component_availability": ("features/reseller/shared/approved-component-availability.ts", ("targetOrganizationId", "projectId", "componentKind", "componentKey", "available")),
    "install_flow_example": ("features/flows/shared/flow-example-install.ts", ("exampleId",)),
    "install_domain_example": ("features/domains/shared/domain-example-install.ts", ("setId", "careerName", "positionIds")),
    "install_capability_example": ("features/domains/shared/domain-example-install.ts", ("exampleId",)),
    "install_approved_domain_example": ("features/domains/shared/domain-example-install.ts", ("componentKey", "projectId")),
    "create_team": ("features/core-integration-mcp-claude/server/mcp-team-tools.ts", ("name", "description")),
    "batch_assign_positions": ("features/core-integration-mcp-claude/server/mcp-position-assignment-tool.ts", ("assignments", "personId", "positionId")),
    "assign_person_to_flow": ("features/core-integration-mcp-claude/server/mcp-flow-person-tools.ts", ("processId", "personId", "assigned")),
    "set_person_task_due_date": ("features/core-integration-mcp-claude/server/mcp-flow-person-tools.ts", ("processId", "personId", "taskId", "dueDate")),
}

# The skills that make Outreach calls. Each carries the acting section in both packages.
OUTREACH_SKILLS = (
    "mosaico-outreach",
    "mosaico-outreach-invite-run",
    "mosaico-outreach-follow-up-run",
    "mosaico-outreach-repair-run",
    "mosaico-outreach-lead-management",
    "mosaico-outreach-agent-management",
)


def check(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL: {message}")


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def flat(text: str) -> str:
    return " ".join(text.replace("`", "").split())


def section(text: str, heading: str) -> str:
    start = text.index(heading)
    end = text.find("\n## ", start + len(heading))
    return text[start:] if end < 0 else text[start:end]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--app-repo", type=Path, default=Path(os.environ["MOSAICO_APP_REPO"]) if os.environ.get("MOSAICO_APP_REPO") else None)
    args = parser.parse_args()

    # Version, changelog and Do-not item 1: the plugin carries skills only.
    for manifest in (CLAUDE / ".claude-plugin" / "plugin.json", CODEX / ".codex-plugin" / "plugin.json"):
        check(json.loads(read(manifest))["version"] == VERSION, f"{manifest.name} is not at {VERSION}")
        check("mcpServers" not in read(manifest), f"{manifest.name} bundles a Mosaico server")
    check(not list(ROOT.rglob(".mcp.json")), "the plugin ships a .mcp.json: it must bundle no Mosaico server")
    readme = read(ROOT / "README.md")
    check(readme.index(f"### {VERSION}") < readme.index("### 0.9.20"), f"README changelog lacks {VERSION} above 0.9.20")
    entry = flat(readme[readme.index(f"### {VERSION}"):readme.index("### 0.9.20")])
    for needle in (
        "20261015a", "mosaicohr-com/mosaico#1947", "bebbbbe06", "production build 334", "#1942", "get_acting_status", "stop_acting",
        "30 minutes", "web console", "CONNECTOR_ACTING", "Repeat that same call once", "subscription", "Install button", "disconnect",
        "tests/test_connector_acting_skill.py", "No schedule text changes",
    ):
        check(needle in entry, f"README {VERSION} entry lacks: {needle}")
    for tool in NEW_TOOLS:
        check(tool in entry, f"README {VERSION} entry does not name {tool}")

    # The general skill, both packages: the same teaching, and the reconnect note in the right words for each.
    general = {package: read(root / "skills" / "mosaico" / "SKILL.md") for package, root in (("Claude", CLAUDE), ("Codex", CODEX))}
    for package, text in general.items():
        for tool in NEW_TOOLS + ("batch_assign_teams", "assign_team_to_process", "advance_private_reseller_example_delivery", "list_conversion_components"):
            check(f"`{tool}`" in text, f"{package} mosaico skill does not name {tool}")
        words = flat(text)
        for needle in (
            NO_SUBSCRIPTION, NO_ALLOWANCE, ALLOWANCE_BUSY, OPERATOR_ONLY, ENDED_START, "This call did not run. Repeat it; it will run as you in",
            "for 30 minutes", "Only the operator's own click in the Mosaico web console starts it", "No tool starts it",
            "connector.reference", "recommendedAction", "phase (not-acting, acting or ended)", "needs no confirmation and always works",
            "Without a subscription I cannot change anything", "flow_not_switchable", "capability_not_switchable",
            "Installing a flow or an approved domain again creates another copy",
            "Removing a person deletes the work they have recorded on the flow",
        ):
            check(needle in words, f"{package} mosaico skill lacks: {needle}")
        check("http" not in text and ".mcp.json" not in text, f"{package} mosaico skill names a server address")
    body = lambda text: text[text.index("## Changes need a subscription"): text.index("## When a tool is missing")]  # noqa: E731
    check(body(general["Claude"]) == body(general["Codex"]), "the Claude and Codex mosaico skills teach different things")
    claude_missing = flat(section(general["Claude"], "## When a tool is missing"))
    check("disconnects and reconnects the Mosaico connector in Claude's connector settings" in claude_missing and "Claude keeps a copy of the connector's tool list" in claude_missing, "Claude mosaico skill lacks the reconnect note")
    check("disconnected and connected again" in flat(section(general["Codex"], "## When a tool is missing")), "Codex mosaico skill lacks the missing-tool note")
    follow = flat(read(CLAUDE / "skills" / "mosaico-outreach-follow-up-run" / "SKILL.md"))
    check(follow.count("in Claude's connector settings (Claude keeps its old tool list until then, so a new tool does not appear before that)") == 1, "Claude follow-up skill lacks the reconnect note where it says the follow-up queue tool is missing")

    # Outreach: stop on the acting refusal, repeat once after the ended refusal.
    for package, root in (("Claude", CLAUDE), ("Codex", CODEX)):
        for name in OUTREACH_SKILLS:
            raw = read(root / "skills" / name / "SKILL.md")
            check(raw.count("## While the connector is acting as a member") == 1, f"{package} {name} lacks the acting section (exactly once)")
            words = flat(section(raw, "## While the connector is acting as a member"))
            for needle in (
                OPERATOR_ONLY, "Stop there.", "Report that sentence word for word", "Do not try the call again", "do not end the session yourself",
                "A scheduled run reports and stops the same way", ENDED_START, "This call did not run. Repeat it", "Repeat that same call once, with the same arguments",
            ):
                check(needle in words, f"{package} {name} acting section lacks: {needle}")
            check("outreach_" not in words, f"{package} {name} acting section names an Outreach tool")

    # Approving a conversion: only on the person's ask, and it needs a subscription. The run loop still never approves.
    for package, root in (("Claude", CLAUDE), ("Codex", CODEX)):
        convert = flat(read(root / "skills" / "mosaico-methodology-convert" / "SKILL.md"))
        for needle in (
            "approve_methodology_conversion", "approve_conversion", "Call it only when the person has reviewed the draft and asks you to install it",
            "Without a subscription nothing can be changed through the connector", "Install button in the Mosaico web app",
            "Never approve a conversion the person did not ask you to install.",
        ):
            check(needle in convert, f"{package} convert skill lacks: {needle}")
        run = flat(read(root / "skills" / "mosaico-methodology-conversion-run" / "SKILL.md"))
        check("Never approve or install anything." in run and "approve_methodology_conversion" not in run, f"{package} conversion-run skill no longer leaves approval to the person")

    if args.app_repo is not None:
        app = args.app_repo.resolve()
        source = lambda relative: read(app / relative)  # noqa: E731
        acting = source("features/core-impersonation/shared/connector-acting.ts")
        check(OPERATOR_ONLY in acting, "the application's operator-only sentence differs from the skills'")
        check("`Your session acting as ${input.names.memberName} in ${input.names.customerName} ended at" in acting and "This call did not run. Repeat it; it will run as you in" in acting, "the application's session-ended sentence differs from the skills'")
        check("CONNECTOR_OPERATOR_ONLY_PREFIXES = ['outreach_', 'incident_']" in acting and "CONNECTOR_CONTROL_TOOLS = ['get_acting_status', 'stop_acting']" in acting, "the application's acting tool classes changed")
        check("CONNECTOR_NOTICE_CLEARING_TOOLS = ['ping']" in acting, "the application no longer lets ping clear the ended notice")
        for needle in ("phase: 'not-acting'", "phase: 'acting'", "phase: 'ended'", "reference: string", "recommendedAction", "secondsRemaining", "blockers", "allowedActions", "kind: 'tool' | 'human' | 'none'", "Customers → <customer> → Members → <member> → my connected Claude"):
            check(needle in acting, f"the application's acting status lacks: {needle}")
        check("IMPERSONATION_TTL_MS = 30 * 60 * 1000" in source("features/core-impersonation/shared/impersonation.ts"), "the application's acting session is no longer 30 minutes")

        invocation = source("features/core-integration-mcp-claude/server/mcp-tool-invocation.ts")
        for sentence in (NO_SUBSCRIPTION, NO_ALLOWANCE, ALLOWANCE_BUSY):
            check(sentence in invocation, f"the application's allowance refusal differs: {sentence}")
        exempt = re.search(r"MCP_ALLOWANCE_EXEMPT_TOOLS = new Set\(\[(.*?)\]\)", invocation, re.S)
        check(exempt is not None, "cannot read MCP_ALLOWANCE_EXEMPT_TOOLS")
        check("approve_methodology_conversion" not in exempt.group(1), "approve_methodology_conversion is allowance-exempt again: the convert skill says it needs a subscription")
        check("get_acting_status" in exempt.group(1) and "stop_acting" in exempt.group(1), "the acting tools are no longer exempt from the allowance")
        check("Like every change made through Claude, it needs an active subscription" in source("features/methodology/server/methodology-mcp-tools.ts"), "the application's approve tool no longer says it needs a subscription")
        check("approve_conversion: 'approve_methodology_conversion'" in source("features/methodology/shared/methodology-action-tools.ts"), "the application's approve_conversion action no longer names approve_methodology_conversion")

        member_list = re.search(r"CONNECTOR_ACTING_MEMBER_TOOLS = \[(.*?)\] as const", source("features/core-integration-mcp-claude/server/mcp-connector-acting-tools.ts"), re.S)
        check(member_list is not None, "cannot read CONNECTOR_ACTING_MEMBER_TOOLS")
        member_tools = set(re.findall(r"'([a-z_]+)'", member_list.group(1)))
        registered: set[str] = set()
        for path in sorted((app / "features").rglob("*.ts")):
            if "__tests__" in path.parts or path.name.endswith(".test.ts"):
                continue
            text = path.read_text(encoding="utf-8")
            registered |= {m.group(1) for m in re.finditer(r"(?:\bname|\btoolName):\s*'([a-z_]+)'", text)}
            registered |= {m.group(1) for m in re.finditer(r"_TOOL\s*=\s*'([a-z_]+)'", text)}
        for tool in NEW_TOOLS + ("batch_assign_teams", "assign_team_to_process", "advance_private_reseller_example_delivery", "list_conversion_components"):
            check(tool in registered, f"the application does not register {tool}")
        for tool in NEW_TOOLS:
            if tool not in ACTING_TOOLS:
                check(tool in member_tools, f"the application does not let an acting connector call {tool}")
        for tool, (relative, names) in ARGUMENTS.items():
            declared = source(relative)
            for name in names:
                check(name in declared, f"the application's {tool} has no argument {name} in {relative}")
        availability = source("features/reseller/shared/approved-component-availability.ts")
        for code in ("flow_not_switchable", "capability_not_switchable"):
            check(f"{code}:" in availability, f"the application has no refusal {code}")
        catalogue = source("features/core-integration-mcp-claude/server/mcp-example-catalogue-tool.ts")
        for name in ("resellerLink", "flowExamples", "domainSets", "capabilityExamples", "approvedExamples", "allowedActions", "recommendedAction"):
            check(name in catalogue, f"the application's example catalogue read has no {name}")
        check("a flow cannot be switched on" in source("features/core-integration-mcp-claude/server/mcp-approved-component-availability-tool.ts"), "the application no longer says a flow cannot be switched")
        suffix = "against the application at " + str(app)
    else:
        suffix = "(pass --app-repo to check the application contract too)"
    print(
        f"PASS: both packages teach connector acting (tools, 30 minutes, started only in the web console), stop an Outreach run on the acting refusal, "
        f"repeat a call once after the session-ended refusal, say approving a conversion needs a subscription, teach the reseller catalogue, "
        f"install and people tools, carry the reconnect note, bundle no Mosaico server, and are at {VERSION} {suffix}."
    )


if __name__ == "__main__":
    main()
