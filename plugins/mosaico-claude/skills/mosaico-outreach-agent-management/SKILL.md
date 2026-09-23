---
name: mosaico-outreach-agent-management
description: Review, update, or create owned Mosaico Outreach Agents without changing Leads or Messages.
---

# Manage Mosaico Outreach Agents

At the start of every run, read `outreach_get_agents` and show a complete report of all loaded owned
Agents. Include each Agent's name, Agent id, active state, search instructions and message
instructions.

Explain that only name, search instructions, message instructions and active state can be changed.
Ask whether the person wants to update an existing Agent or create a new Agent. Do not offer changes
to ownership, ids, timestamps, Leads or Messages.

## Update an existing Agent

1. Ask which reported Agent to update and which editable fields should change.
2. Preserve every field the person did not request to change.
3. Summarize the exact patch and ask for confirmation immediately before calling
   `outreach_update_agent`.
4. Reread `outreach_get_agents` and report the saved result.

## Create a new Agent

1. Ask for the Agent name, search instructions, message instructions and initial active state.
2. Do not ask the person to invent an Agent id; Mosaico generates it.
3. Summarize the complete new Agent and ask for confirmation immediately before calling
   `outreach_create_agent`.
4. Reread `outreach_get_agents` and report the created Agent.

Outreach records belong to the company. If the person names a colleague, pass that member's
`ownerUserId`; otherwise omit it to work on their own records. Mosaico decides which member an Agent
belongs to and refuses a mismatched `ownerUserId` — do not try to work that out yourself. Only Owners
and Admins can use Outreach. Mosaico owns validation, duplicate-name checks, identity generation,
persistence and authorization.
