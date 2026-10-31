#!/usr/bin/env python3
"""The Mosaico page (Claude package only): the asset is the recorded source, shows screens only, and its skill installs one copy per person."""

from __future__ import annotations

import hashlib
import json
import re

from skill_text import CLAUDE, CODEX, ROOT, check, flat, read, skill, words

ASSETS = CLAUDE / "assets"
NAME = "mosaico-page-install"
# Server-only know-how and secrets: none of it may be in the page (phrases from the run guidance, the moved tokens, key shapes).
EXPECTED_TOOLS = (
    "get_daily_brief", "reseller_list_customers", "reseller_list_customer_components", "reseller_list_customer_members",
    "install_methodology_component", "get_methodology_view", "create_methodology_project", "add_methodology_source",
    "update_methodology_source", "delete_methodology_project", "save_methodology_guidance", "set_reseller_terminology",
    "edit_methodology_component", "start_methodology_analysis", "cancel_methodology_analysis", "retry_methodology_analysis_unit",
    "retry_methodology_failed_units", "get_teams_view", "get_team_member_view", "get_teams_analytics_view",
    "create_organization_users", "resend_invitation", "delete_user", "set_self_assessment",
    "set_personal_target", "set_member_career_view", "set_member_role", "remove_person_position",
    "set_person_compliance_record", "batch_assign_teams", "batch_assign_positions", "batch_update_profile_fields",
    "set_person_capability_levels", "get_domains_view", "get_domain_view", "get_domain_position_view",
    "get_domain_record_view", "get_domains_analytics_view", "delete_domain_record", "update_domain_record_description",
    "set_position_capability_requirements", "set_position_ladder_level", "get_flows_view", "get_flow_view",
    "get_flow_step_answers", "get_flow_answers", "save_step_answer", "add_step_file",
    "get_step_file", "remove_step_file", "assign_person_to_flow", "set_step_people",
    "set_step_delegates", "set_task_due_date", "approve_task_completion", "send_task_back",
    "delete_process", "get_account_view", "get_security_view", "get_notifications_view",
    "get_permissions_view", "get_usage_audit_view", "get_integrations_view", "revoke_integration_grant",
)
FORBIDDEN = (
    "system message", "pattern list", "agentInstructions", "step.guidance", "draftsToWrite", "sendRun.", "sourcing_plan_empty", "completion.mustContinue",
    "history-mismatch", "Standing answers for this recurring", "checklistReview", "Judge only the Lead", "A no ends the Lead", "Thin results call for a wider search",
    "A draft is only a draft: never approve", "Never reword to get past a refusal", "workNow", "outreach_start_run", "outreach_record_message",
)
SECRET_SHAPES = (r"sk-ant-[A-Za-z0-9_-]{10,}", r"AKIA[0-9A-Z]{16}", r"Bearer\s+[A-Za-z0-9._-]{20,}", r"-----BEGIN [A-Z ]*PRIVATE KEY", r"eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}", r"ghp_[A-Za-z0-9]{30,}")


def main() -> None:
    page = ASSETS / "mosaico-page.html"
    caps_file = ASSETS / "mosaico-page.capabilities.json"
    source = json.loads(read(ASSETS / "mosaico-page.source.json"))
    check(re.fullmatch(r"[0-9a-f]{40}", source["commit"]) is not None and source["release"] == "20261101a" and source["date"] == "2026-11-01", "the source record lacks commit, release or date")
    for name, path in (("mosaico-page.html", page), ("mosaico-page.capabilities.json", caps_file)):
        data = path.read_bytes()
        record = source["files"][name]
        check(hashlib.sha256(data).hexdigest() == record["sha256"], f"{name} is not the recorded source (checksum)")
        check(len(data) == record["bytes"], f"{name} size differs from the record")
    text = read(page)
    check("<title>Mosaico</title>" in text, "the page title is not Mosaico")

    caps = json.loads(read(caps_file))
    servers = caps["mcp"]["servers"]
    check(len(servers) == 1 and servers[0]["server"] == "mosaico", "the capabilities do not name the one connector 'mosaico'")
    tools = servers[0]["tools"]
    check(len(tools) == 64 and len(set(tools)) == 64, f"the page should declare 64 distinct tools, not {len(tools)}")
    check(set(caps) == {"mcp", "assets", "downloads"} and caps["assets"] == {} and caps["downloads"] is True, "the capabilities hold more than mcp, empty assets and downloads")
    check(sorted(tools) == sorted(EXPECTED_TOOLS), f"the declared tools differ from the 64 the page was released with: {sorted(set(tools) ^ set(EXPECTED_TOOLS))}")
    # The page names its read tools in code; the write tools are named by the views it reads, so only the read ones are looked for.
    named = {tool for tool in tools if f'"{tool}"' in text or tool in text}
    check(len(named) >= 14, f"the page names only {len(named)} of its declared tools")
    undeclared = set(re.findall(r"\b((?:get|reseller_list)_[a-z_]+_(?:view|brief|customers|components|members))\b", text)) - set(tools)
    check(not undeclared, f"the page names tools its capabilities do not declare: {sorted(undeclared)}")

    for needle in FORBIDDEN:
        check(needle not in text, f"the page carries server-only text: {needle}")
    for shape in SECRET_SHAPES:
        check(re.search(shape, text) is None, f"the page looks to carry a key or token: {shape}")

    check(not (CODEX / "assets").exists() and not (CODEX / "skills" / NAME).exists(), "the Codex package carries the page or its skill")
    body = skill("Claude", NAME)
    text_flat = flat(body)
    check(words(body) <= 400, "the page skill is not short")
    for needle in ("assets/mosaico-page.html", "unchanged", 'title "Mosaico"', 'icon "dashboard"', "assets/mosaico-page.capabilities.json", "~/.claude/mosaico-page-url",
                   "same link", "Never publish without the link when one exists", "Artifact tool", "named `mosaico`".replace("`", ""), "reconnect"):
        check(needle in text_flat, f"the page skill lacks: {needle}")
    check(text_flat.count("without the link") == 1 and "second copy" in text_flat, "the page skill does not keep to one link per person")
    for rule in ("outreach_", "routine", "Lead", "step.", "checklist"):
        check(rule not in body, f"the page skill carries Mosaico method text: {rule}")
    readme = read(ROOT / "README.md")
    check("## The Mosaico page (Claude only)" in readme and "### 0.11.0" in readme and "does not get the page or the skill" in flat(readme), "the README lacks the page section or note")
    print("PASS: the Mosaico page equals its recorded source, declares exactly its 64 tools, carries no server-only text or keys, and its Claude-only skill installs one copy per person at one link.")


if __name__ == "__main__":
    main()
