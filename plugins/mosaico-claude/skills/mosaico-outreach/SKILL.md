---
name: mosaico-outreach
description: Run, resume, or inspect a Mosaico Outreach day through the connected Mosaico MCP server and an authenticated browser.
---

# Mosaico Outreach

Mosaico owns workflow state, transitions, dates, validation, recovery and completion. Resolve an
explicit intent once. When this skill is invoked without an explicit intent, ask "What do you want
to do in Mosaico Outreach?" and present these action headers and descriptions. Person-specific
recommended actions may be mentioned inside the matching action, but must never replace the two
all-dates follow-up actions:

- **Source invitation Leads** — Fill today or selected days to exactly 20 qualified Leads and save
  personalized invitation drafts. Never approve or send.
- **Send approved invitations** — Send only exact invitation messages already approved in Mosaico
  for the selected day. Verify each one on LinkedIn before marking it sent.
- **Check for new follow-ups — all dates** — Check every recorded Outreach Lead regardless of
  scheduled day, review visible LinkedIn conversations, and save missing follow-up drafts. Never
  approve or send.
- **Send approved follow-up drafts** — Across all dates, send only exact follow-up messages whose
  current Mosaico status is Approved. Verify each delivery on LinkedIn before marking it sent.
- **Inspect an Outreach day** — Read a day's Leads and message states without making changes.
- **Manage Outreach Agents** — Review, create, or update owned Agents.
- **Manage Outreach Leads** — Review, add, or update owned Lead records without changing Messages.
- **Install daily invitation schedule** — Idempotently create the local-time 8:00 AM preparation and
  8:00 PM approved-delivery schedules.

Route Agent management to `/mosaico:mosaico-outreach-agent-management`, Lead management to
`/mosaico:mosaico-outreach-lead-management`, and schedule installation to
`/mosaico:mosaico-outreach-schedule-install`.

Use the current application-owned read for the resolved intent. For invitation sourcing call
`outreach_get_day` with the preserved `day`, `intent: source_invitation_leads`, and the requested
`targetCount` (20 for the standard run). For approved invitation delivery use
`intent: send_approved_invitations`; for inspection use `intent: inspect_day`. For follow-up
checking or delivery call the calendar-agnostic `outreach_get_follow_ups`. Do not ask the menu again
when the person's intent is explicit. The schedule action is platform configuration and needs no
Outreach read before its installer. Follow the returned recommended action and reread status after
every transition. Call `outreach_get_agents` before qualification or writing and use the selected
active Agent's search instructions, message instructions and Messaging Checklist for judgment only.

Human approval applies to the exact current message. For LinkedIn delivery, perform the authorized
browser action, verify the external result, report evidence through the tool named by Mosaico and
reread status. Never infer delivery from a click or reconstruct workflow state from conversation
memory. Record contradictory tool behavior through the dedicated MCP incident tool.
