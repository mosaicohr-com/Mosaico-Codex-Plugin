---
name: mosaico-outreach-agent-management
description: Review, update, or create owned Mosaico Outreach Agents without changing Leads or Messages.
---

# Manage Mosaico Outreach Agents

At the start of every run, read `outreach_get_agents` and show a complete report of all loaded owned
Agents. Include each Agent's name, Agent id, active state, search instructions, message
instructions, `leadsPerDay` (Leads per day) and `sourcedByUserId` (Sourced by).

Explain that only name, search instructions, message instructions, active state, `leadsPerDay` and
`sourcedByUserId` can be changed.
Ask whether the person wants to update an existing Agent or create a new Agent. Do not offer changes
to ownership, ids, timestamps, Leads or Messages.

## Sourcing plan fields

Each Agent carries two fields that drive the Source leads routine. `leadsPerDay` is how many Leads (1 to 100)
Source leads tops the Agent up to each day; empty means it is not sourced automatically. `sourcedByUserId`
("Sourced by") is the active member whose Source leads run sources it; empty means the Agent's owner.
`outreach_update_agent` and `outreach_create_agent` set them. Only an Owner or Admin, or the Agent's owner,
can; Sourced by must be an active member, so take the member from `get_team_profiles` ("Person ID") and never
guess one. Mosaico works out from them how many Leads each person still needs today.

## Update an existing Agent

1. Ask which reported Agent to update and which editable fields should change.
2. Preserve every field the person did not request to change.
3. Summarize the exact patch and ask for confirmation immediately before calling
   `outreach_update_agent`.
4. Reread `outreach_get_agents` and report the saved result.

## Create a new Agent

1. Ask for the Agent name, search instructions, message instructions and initial active state, and, if the
   person wants it sourced automatically, Leads per day and Sourced by.
2. Do not ask the person to invent an Agent id; Mosaico generates it.
3. Summarize the complete new Agent and ask for confirmation immediately before calling
   `outreach_create_agent`.
4. Reread `outreach_get_agents` and report the created Agent.

This skill works only on the signed-in person's own Agents. Do not pass `ownerUserId`. Only Owners
and Admins can use Outreach. Mosaico owns validation, duplicate-name checks, identity generation,
persistence and authorization.
