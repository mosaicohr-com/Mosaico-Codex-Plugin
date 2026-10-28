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
    "get_daily_brief", "reseller_list_customers", "reseller_list_customer_components", "reseller_list_customer_members", "install_methodology_component",
    "get_methodology_components_view", "discard_conversion_components", "get_teams_view", "get_domains_view", "delete_domain_record", "get_flows_view",
    "get_flow_people_view", "assign_person_to_flow", "delete_process", "get_account_view", "get_security_view", "get_notifications_view",
    "get_permissions_view", "get_usage_audit_view",
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
    check(re.fullmatch(r"[0-9a-f]{40}", source["commit"]) is not None and source["release"] == "20261029a" and source["date"] == "2026-10-29", "the source record lacks commit, release or date")
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
    check(len(tools) == 19 and len(set(tools)) == 19, f"the page should declare 19 distinct tools, not {len(tools)}")
    check(set(caps) == {"mcp", "assets"} and caps["assets"] == {}, "the capabilities hold more than mcp and empty assets")
    check(sorted(tools) == sorted(EXPECTED_TOOLS), f"the declared tools differ from the 19 the page was released with: {sorted(set(tools) ^ set(EXPECTED_TOOLS))}")
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
    print("PASS: the Mosaico page equals its recorded source, declares exactly its 19 tools, carries no server-only text or keys, and its Claude-only skill installs one copy per person at one link.")


if __name__ == "__main__":
    main()
