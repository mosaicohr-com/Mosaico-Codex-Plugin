#!/usr/bin/env python3
"""Connector acting (0.9.21, reworked for server release 20261017a), the subscription rule, the people tools and, from 0.9.23, install_methodology_component.

Mosaico owns the acting session (it has no timer), who the calls run as and every refusal (ADR-0005). The skills only say how to read
Mosaico's answers in plain language. These checks pin that both packages name the tools, quote Mosaico's sentences word for word, stop
an Outreach run on the acting refusal (no retry, no way round), stop the task and tell the person after the "session ended" refusal
(no repeat, no carrying on as the operator), say the session copies the member exactly, say that installing
a Methodology component needs a subscription (no approve, no publish, no catalogue: server release 20261019d), and add no Mosaico server, address or token to the plugin (Do-not item 1).

Pass --app-repo (or set MOSAICO_APP_REPO) to also check the application at the live server commit: every tool is registered, every
sentence and argument is the one the application uses, and install_methodology_component is registered while the 13 retired catalogue and approval tools are not.
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
VERSION = "0.9.23"  # the README entry these checks read (install_methodology_component)
CURRENT = "0.11.3"  # the manifests
PREVIOUS = "0.9.22"

OPERATOR_ONLY = "Outreach and incident tools are not available while your connector is acting as a member of another organisation. End the session first."
ENDED_START = "Your session as"
ENDED_TAIL = "so the task stopped and this call did not run: tell the person, and do not carry on as yourself."
IDENTITY_LINE = "Working as <member> (<role>) in <customer> since <time> UTC; signed in as <operator>."
RESELLER_REFUSED = "Reseller tools are not available while your connector is working as a member of a customer, because the member is not a reseller. End the session first."
NO_SUBSCRIPTION = "This organization needs an active Mosaico subscription before the MCP connector can run this tool."
NO_ALLOWANCE = "This organization has no remaining AI allowance for this period."
ALLOWANCE_BUSY = "Another tool call is settling this organization’s AI allowance. Retry this call shortly."

ACTING_TOOLS = ("get_acting_status", "stop_acting")
PEOPLE_TOOLS = ("list_teams", "create_team", "batch_assign_positions", "assign_person_to_flow", "set_person_task_due_date")
RESELLER_TOOLS: tuple[str, ...] = ()  # none left: the install tool is allowed while acting, for the member's own organisation only
INSTALL_TOOLS = ("install_methodology_component",)
# Retired by server release 20261019d (mosaicohr-com/mosaico#2013): no skill, test or current README section may name them.
REMOVED_TOOLS = (
    "approve_methodology_conversion", "publish_approved_component_example", "publish_private_reseller_example", "get_private_reseller_catalogue",
    "get_private_reseller_example_delivery", "advance_private_reseller_example_delivery", "get_approved_components_for_customer",
    "set_approved_component_availability", "install_approved_domain_example", "list_example_catalogue", "install_flow_example",
    "install_domain_example", "install_capability_example",
)
REMOVED_ACTIONS = ("approve_conversion", "publish_component_example")
NEW_TOOLS = ACTING_TOOLS + PEOPLE_TOOLS + RESELLER_TOOLS + INSTALL_TOOLS

# Each tool the general skill teaches, with the arguments it names: the application file that declares them.
ARGUMENTS = {
    "install_methodology_component": ("features/methodology/server/methodology-mcp-install-tool.ts", ("projectId", "componentKind", "componentKey", "targetOrganizationId")),
    "create_team": ("features/core-integration-mcp-claude/server/mcp-team-tools.ts", ("name", "description")),
    "batch_assign_positions": ("features/core-integration-mcp-claude/server/mcp-position-assignment-tool.ts", ("assignments", "personId", "positionId")),
    "assign_person_to_flow": ("features/core-integration-mcp-claude/server/mcp-flow-person-tools.ts", ("processId", "personId", "assigned")),
    "set_person_task_due_date": ("features/core-integration-mcp-claude/server/mcp-flow-person-tools.ts", ("processId", "personId", "taskId", "dueDate")),
}

# The skills that make Outreach calls. Each states the thin acting rule in both packages (0.10.0: Mosaico owns the sentences, the skill says stop, report them word for word, never end the session).
OUTREACH_SKILLS = (
    "mosaico-outreach",
    "mosaico-outreach-invite-run",
    "mosaico-outreach-follow-up-run",
    "mosaico-outreach-schedule-install",
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
        check(json.loads(read(manifest))["version"] == CURRENT, f"{manifest.name} is not at {CURRENT}")
        check("mcpServers" not in read(manifest), f"{manifest.name} bundles a Mosaico server")
    check(not list(ROOT.rglob(".mcp.json")), "the plugin ships a .mcp.json: it must bundle no Mosaico server")
    readme = read(ROOT / "README.md")
    check(readme.index(f"### {CURRENT}") < readme.index(f"### {VERSION}") < readme.index(f"### {PREVIOUS}") < readme.index("### 0.9.21") < readme.index("### 0.9.20"), f"README changelog lacks {CURRENT} above {VERSION} above {PREVIOUS} above 0.9.21 above 0.9.20")
    unreleased = flat(readme[readme.index(f"### {VERSION}"):readme.index(f"### {PREVIOUS}")])
    for needle in (
        "20261019d", "build 349", "#2011", "#2013", "install_methodology_component", "projectId", "componentKind", "componentKey", "targetOrganizationId",
        "confirmationToken", "no Approve", "no Publish", "Private or Public", "Examples tab", "get_methodology_project_status", "install_component",
        "Removed tools", "tests/test_connector_acting_skill.py",
    ) + REMOVED_TOOLS + REMOVED_ACTIONS:
        check(needle in unreleased, f"README {VERSION} entry lacks: {needle}")
    entry = flat(readme[readme.index(f"### {PREVIOUS}"):readme.index("### 0.9.21")])  # history: 0.9.22 as released
    for needle in ("20261017a", "4285416fd", "production build 340", "#1965", "#1966", "#1967", "#1968", "#1969", "get_acting_status", "tell_the_person_the_task_stopped"):
        check(needle in entry, f"README {PREVIOUS} entry lacks: {needle}")
    older = flat(readme[readme.index("### 0.9.21"):readme.index("### 0.9.20")])
    for needle in ("20261015a", "bebbbbe06", "production build 334", "#1942", "get_acting_status", "stop_acting", "superseded by the 0.9.22 entry", "superseded by 0.9.23"):
        check(needle in older, f"README 0.9.21 entry lacks: {needle}")
    for package, root in (("Claude", CLAUDE), ("Codex", CODEX)):
        for path in sorted(root.rglob("*")):
            if path.is_file() and path.suffix in (".md", ".json", ".js", ".py"):
                text = read(path)
                for tool in REMOVED_TOOLS + REMOVED_ACTIONS:
                    check(tool not in text, f"{package} package file {path.relative_to(ROOT)} still names the retired {tool}")

    # The general skill, both packages: the same teaching, and the reconnect note in the right words for each.
    general = {package: read(root / "skills" / "mosaico" / "SKILL.md") for package, root in (("Claude", CLAUDE), ("Codex", CODEX))}
    for package, text in general.items():
        for tool in NEW_TOOLS + ("batch_assign_teams", "assign_team_to_process"):
            check(f"`{tool}`" in text, f"{package} mosaico skill does not name {tool}")
        words = flat(text)
        for needle in (
            NO_SUBSCRIPTION, NO_ALLOWANCE, ALLOWANCE_BUSY, OPERATOR_ONLY, ENDED_START, ENDED_TAIL, IDENTITY_LINE, RESELLER_REFUSED,
            "There is no timer: the session ends only when the person ends it or signs out", "copies that member's permissions exactly and adds nothing",
            "billing is reachable only when working as the Owner", "Progress in the member's name is allowed as the member could do it, and Mosaico logs it under both names",
            "Do not repeat the call and do not carry on the task", "then wait for their new instruction", "Do not continue as the operator until they give one",
            "tell_the_person_the_task_stopped", "Only the operator's own click in the Mosaico web console starts it", "No tool starts it",
            "connector.reference", "recommendedAction", "phase (not-acting, acting or ended)", "needs no confirmation and always works",
            "Without a subscription I cannot change anything",
            "no approve step, no publish step, no Private or Public setting", "no Examples tab or example library",
            "projectId, componentKind (flow or domain), componentKey and targetOrganizationId", "mode: \"execute\" and the confirmationToken",
            "replaces the earlier copy in place when nobody has progress on it", "Mosaico makes a new copy and keeps the old one",
            "component_not_published", "analysis_not_complete", "not_compilable", "tenant_access_denied", "subscription_required",
            "only target allowed is that member's organisation", "state (draft or published)", "installs (organizationId, organizationName, installedAt, by, changedSinceInstall)",
            "fix_warnings", "install_component",
            "Removing a person deletes the work they have recorded on the flow",
        ):
            check(needle in words, f"{package} mosaico skill lacks: {needle}")
        for gone in ("30 minutes", "endsAt", "secondsRemaining", "Repeat that same call once", "Repeat it; it will run as you", "until <time> UTC", "Acting as <member>"):
            check(gone not in words, f"{package} mosaico skill still says: {gone}")
        check("http" not in text and ".mcp.json" not in text, f"{package} mosaico skill names a server address")
    body = lambda text: text[text.index("## Changes need a subscription"): text.index("## When a tool is missing")]  # noqa: E731
    check(body(general["Claude"]) == body(general["Codex"]), "the Claude and Codex mosaico skills teach different things")
    claude_missing = flat(section(general["Claude"], "## When a tool is missing"))
    codex_missing = flat(section(general["Codex"], "## When a tool is missing"))
    for package, missing in (("Claude", claude_missing), ("Codex", codex_missing)):
        for needle in ("lists only the tools this person may use", "their role", "no active Mosaico subscription", "get_tier_status", "active subscription", "out of date", "reconnect" if package == "Claude" else "connected again"):
            check(needle in missing, f"{package} mosaico skill's missing-tool note lacks: {needle}")
        check("a tool named in this skill is missing" not in missing and "tell the person to do that" not in missing, f"{package} mosaico skill still tells the person to reconnect for one missing tool")
    check("tell the person to disconnect and reconnect" in claude_missing and "If it shows an active subscription and the person's role allows the change" in claude_missing, "Claude mosaico skill lacks the active-subscription, list-out-of-date, reconnect case")
    check("If it shows an active subscription and the person's role allows the change" in codex_missing, "Codex mosaico skill lacks the active-subscription, list-out-of-date case")
    for name in ("mosaico-outreach", "mosaico-outreach-follow-up-run", "mosaico-outreach-invite-run", "mosaico-outreach-schedule-install"):
        stale = flat(read(CLAUDE / "skills" / name / "SKILL.md"))
        check(stale.count("If a tool named here is missing: role or no subscription") == 1 and "Claude kept an old tool list" not in stale and "with an active subscription, the list is out of date: reconnect" in stale, f"Claude {name} skill lacks the role-or-subscription note for a missing tool")

    # Outreach: stop on the acting refusal (Mosaico's own sentence, reported word for word) and never end the session. The thin skills hold no copy of
    # Mosaico's sentences; the application's wording is still checked below with --app-repo.
    for package, root in (("Claude", CLAUDE), ("Codex", CODEX)):
        for name in OUTREACH_SKILLS:
            raw = read(root / "skills" / name / "SKILL.md")
            words = flat(raw)
            for needle in (
                "If a call is refused because the connector is acting as a member of another organisation, or its acting session ended, stop and report Mosaico's sentence word for word",
                "Never end the acting session yourself",
            ):
                check(needle in words, f"{package} {name} lacks the acting rule: {needle}")
            check("Repeat that same call once" not in words and "carry on as yourself" not in words, f"{package} {name} tells the model to repeat the call or carry on")

    # Installing a component: only on the person's ask, and it needs a subscription. There is no approve step. The run loop still never installs.
    for package, root in (("Claude", CLAUDE), ("Codex", CODEX)):
        convert = flat(read(root / "skills" / "mosaico-methodology-convert" / "SKILL.md"))
        for needle in (
            "install_methodology_component", "install_component", "Call it only when the person asks you to install it", "There is no approve step and no publish step",
            "projectId, componentKind (flow or domain), componentKey and targetOrganizationId", 'mode: "execute" and the confirmationToken', "component_not_published",
            "Without a subscription nothing can be changed through the connector", "Install button in the Mosaico web app",
            "Never install a component the person did not ask you to install.",
        ):
            check(needle in convert, f"{package} convert skill lacks: {needle}")
        run = flat(read(root / "skills" / "mosaico-methodology-conversion-run" / "SKILL.md"))
        check("Never approve or install anything." in run and "install_methodology_component" not in run, f"{package} conversion-run skill no longer leaves installing to the person")

    if args.app_repo is not None:
        app = args.app_repo.resolve()
        source = lambda relative: read(app / relative)  # noqa: E731
        acting = source("features/core-impersonation/shared/connector-acting.ts")
        check(OPERATOR_ONLY in acting, "the application's operator-only sentence differs from the skills'")
        check("`Your session as ${input.names.memberName} in ${input.names.customerName} ended at" in acting and ENDED_TAIL in acting, "the application's session-ended sentence differs from the skills'")
        check("Repeat it" not in acting.split("export function connectorEndedSentence")[1].split("}")[0], "the application's session-ended sentence still says to repeat the call")
        check("`Working as ${names.memberName} (${names.memberRole}) in ${names.customerName} since ${connectorClock(input.startedAt)}; signed in as ${names.operatorName}.`" in acting, "the application's identity line differs from the skills'")
        check(RESELLER_REFUSED in acting, "the application's reseller-tools refusal differs from the skills'")
        check("action: 'tell_the_person_the_task_stopped'" in acting and "kind: 'human'" in acting, "the application's ended status no longer recommends telling the person")
        check("CONNECTOR_OPERATOR_ONLY_PREFIXES = ['outreach_', 'incident_']" in acting and "CONNECTOR_CONTROL_TOOLS = ['get_acting_status', 'stop_acting']" in acting, "the application's acting tool classes changed")
        check("CONNECTOR_NOTICE_CLEARING_TOOLS = ['ping']" in acting, "the application no longer lets ping clear the ended notice")
        for needle in ("phase: 'not-acting'", "phase: 'acting'", "phase: 'ended'", "reference: string", "recommendedAction", "blockers", "allowedActions", "kind: 'tool' | 'human' | 'none'", "Customers → <customer> → Members → <member> → my connected Claude"):
            check(needle in acting, f"the application's acting status lacks: {needle}")
        check("secondsRemaining" not in acting and "endsAt" not in acting, "the application's acting status still has a timer field")
        check("IMPERSONATION_TTL_MS" not in source("features/core-impersonation/shared/impersonation.ts"), "the application's acting session has a timer again")

        invocation = source("features/core-integration-mcp-claude/server/mcp-tool-invocation.ts")
        for sentence in (NO_SUBSCRIPTION, NO_ALLOWANCE, ALLOWANCE_BUSY):
            check(sentence in invocation, f"the application's allowance refusal differs: {sentence}")
        exempt = re.search(r"MCP_ALLOWANCE_EXEMPT_TOOLS = new Set\(\[(.*?)\]\)", invocation, re.S)
        check(exempt is not None, "cannot read MCP_ALLOWANCE_EXEMPT_TOOLS")
        check("install_methodology_component" not in exempt.group(1), "install_methodology_component is allowance-exempt: the skills say it needs a subscription")
        check("get_acting_status" in exempt.group(1) and "stop_acting" in exempt.group(1), "the acting tools are no longer exempt from the allowance")
        check("install_component: 'install_methodology_component'" in source("features/methodology/shared/methodology-action-tools.ts"), "the application's install_component action no longer names install_methodology_component")
        check("approve_conversion" not in source("features/methodology/shared/methodology-action-tools.ts"), "the application still has the approve_conversion action")

        member_list = re.search(r"CONNECTOR_ACTING_MEMBER_TOOLS = \[(.*?)\] as const", source("features/core-integration-mcp-claude/server/mcp-connector-acting-tools.ts"), re.S)
        check(member_list is not None, "cannot read CONNECTOR_ACTING_MEMBER_TOOLS")
        member_tools = set(re.findall(r"'([a-z_]+)'", member_list.group(1)))
        reseller_list = re.search(r"CONNECTOR_ACTING_RESELLER_TOOLS = \[(.*?)\] as const", source("features/core-integration-mcp-claude/server/mcp-connector-acting-tools.ts"), re.S)
        check(reseller_list is not None, "cannot read CONNECTOR_ACTING_RESELLER_TOOLS")
        reseller_only = set(re.findall(r"'([a-z_]+)'", reseller_list.group(1)))
        registered: set[str] = set()
        for path in sorted((app / "features").rglob("*.ts")):
            if "__tests__" in path.parts or path.name.endswith(".test.ts"):
                continue
            text = path.read_text(encoding="utf-8")
            registered |= {m.group(1) for m in re.finditer(r"(?:\bname|\btoolName):\s*'([a-z_]+)'", text)}
            registered |= {m.group(1) for m in re.finditer(r"_TOOL\s*=\s*'([a-z_]+)'", text)}
        for tool in NEW_TOOLS + ("batch_assign_teams", "assign_team_to_process", "list_conversion_components"):
            check(tool in registered, f"the application does not register {tool}")
        for tool in REMOVED_TOOLS:
            check(tool not in registered, f"the application still registers the retired {tool}")
        for tool in NEW_TOOLS:
            if tool in RESELLER_TOOLS:
                check(tool in reseller_only and tool not in member_tools, f"the application no longer refuses {tool} while the connector works as a member")
            elif tool not in ACTING_TOOLS:
                check(tool in member_tools, f"the application does not let an acting connector call {tool}")
        for tool, (relative, names) in ARGUMENTS.items():
            declared = source(relative)
            for name in names:
                check(name in declared, f"the application's {tool} has no argument {name} in {relative}")
        check("component_not_published" in source("features/methodology/shared/methodology-component-install.ts") or "component_not_published" in source("features/methodology/server/methodology-mcp-install-tool.ts"), "the application has no refusal component_not_published")
        suffix = "against the application at " + str(app)
    else:
        suffix = "(pass --app-repo to check the application contract too)"
    print(
        f"PASS: both packages teach connector acting (tools, no timer, an exact replica of the member, started only in the web console), stop an Outreach run on the acting refusal, "
        f"stop the task after the session-ended refusal, say installing a component needs a subscription, teach install_methodology_component, "
        f"the people tools, carry the reconnect note, bundle no Mosaico server, and are at {CURRENT} {suffix}."
    )


if __name__ == "__main__":
    main()
