---
name: mosaico-outreach-agent-management
description: Review, update, or create owned Mosaico Outreach Agents without changing Leads or Messages.
---

# Manage Mosaico Outreach Agents

At the start of every run, read `outreach_get_agents` and show a complete report of all loaded owned
Agents. Include each Agent's name, Agent id, active state, search instructions, message
instructions, `leadsPerDay` (Leads per day), `leadsPerRun` (Leads per run), `sourcedByUserId` (Sourced by) and
whether it is sourced (`sourcing`, with `sourcingReason` as Mosaico wrote it).

Explain that only name, search instructions, message instructions, active state, `leadsPerDay`,
`leadsPerRun` and `sourcedByUserId` can be changed.
Ask whether the person wants to update an existing Agent or create a new Agent. Do not offer changes
to ownership, ids, timestamps, Leads or Messages.

## Sourcing plan fields

Each Agent carries three fields that drive the Source leads routine. `leadsPerDay` is the most Leads (1 to 100)
the Agent may hold on one day. `leadsPerRun` is how many Leads (1 to 100) one Source leads run must deliver for
it. `sourcedByUserId` ("Sourced by") is the active member whose Source leads run sources it; empty means the
Agent's owner. `outreach_update_agent` and `outreach_create_agent` set them. Only an Owner or Admin, or the
Agent's owner, can; Sourced by must be an active member, so take the member from `get_team_profiles`
("Person ID") and never guess one.

Every read of an Agent also says whether it is sourced. `sourcing` is `sourced` (the Agent is on and has both
numbers), `not-configured` (it is on but Leads per day or Leads per run is missing) or `off`; `sourcingMissing`
lists the numbers still to set and `sourcingReason` says why in one sentence. Report that sentence as Mosaico
wrote it. Turning an Agent on needs no numbers, and an Agent that is on without them still works for
follow-ups; Source leads sources it only when both numbers are set. Setting one number without the other is
allowed and leaves the Agent not sourced until both are set. Mosaico files each Lead on a free day itself and
never puts more than the Agent's Leads per day on one day.

## Update an existing Agent

1. Ask which reported Agent to update and which editable fields should change.
2. Preserve every field the person did not request to change.
3. Summarize the exact patch and ask for confirmation immediately before calling
   `outreach_update_agent`.
4. Reread `outreach_get_agents` and report the saved result.

## Create a new Agent

1. Ask for the Agent name, search instructions, message instructions and initial active state, and, if the
   person wants it sourced automatically, Leads per day, Leads per run and Sourced by (both numbers are needed
   for it to be sourced).
2. Do not ask the person to invent an Agent id; Mosaico generates it.
3. Summarize the complete new Agent and ask for confirmation immediately before calling
   `outreach_create_agent`.
4. Reread `outreach_get_agents` and report the created Agent.

This skill works only on the signed-in person's own Agents. Do not pass `ownerUserId`. Only Owners
and Admins can use Outreach. Mosaico owns validation, duplicate-name checks, identity generation,
persistence and authorization.
