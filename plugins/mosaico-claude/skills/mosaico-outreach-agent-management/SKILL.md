---
name: mosaico-outreach-agent-management
description: Review, update, or create owned Mosaico Outreach Agents without changing Leads or Messages.
---

# Manage Mosaico Outreach Agents

Agents are the instructions Mosaico gives a run: search and message instructions, the Messaging Checklist, the
sourcing plan and an active switch. This skill reads and changes Agents only, never Leads or Messages. Only
Owners and Admins can use Outreach; an Owner or Admin may manage another member's Agents with `ownerUserId`.

1. Read `outreach_get_agents` and show every Agent: name, id, active state, instructions, Leads per day, Leads per
   run, Sourced by, and Mosaico's own sourcing sentence as written.
2. Ask whether to update an Agent or create one. Only name, instructions, active state, Leads per day, Leads per
   run and Sourced by can change. Take a Sourced by member from `get_team_profiles` ("Person ID"); never guess one.
3. Keep every field the person did not change. Summarise the exact change and ask the person to confirm it
   immediately before `outreach_update_agent` or `outreach_create_agent`. Do not invent an Agent id; Mosaico makes it.
4. Read `outreach_get_agents` again and report the saved Agent. Mosaico validates, refuses what is wrong and says why;
   report its sentence and do not work around it.
