---
name: mosaico-outreach
description: Run, resume, or inspect a Mosaico Outreach day through the connected Mosaico MCP server and an authenticated browser.
---

# Mosaico Outreach

Mosaico is the workflow authority and system of record. The model operates the workflow; it does not
reconstruct workflow state from conversation memory, draft lists, batch history or browser state.

## Start or resume

1. Resolve the person's explicit intent and calendar date and preserve that date throughout the run.
2. When the skill is invoked without an explicit intent, ask "What do you want to do in Mosaico
   Outreach?" and present these action headers and descriptions. Person-specific recommended actions
   may be mentioned inside the matching action, but must never replace the two all-dates follow-up
   actions:
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
   - **Install daily invitation schedule** — Idempotently create the local-time 8:00 AM preparation
     and 8:00 PM approved-delivery schedules.
   Route Agent management to `$mosaico:mosaico-outreach-agent-management`, Lead management to
   `$mosaico:mosaico-outreach-lead-management`, and schedule installation to
   `$mosaico:mosaico-outreach-schedule-install`.
3. Use the current application-owned read for the resolved intent. Do not ask the menu again when
   the person's intent is already explicit:
   - Invitation sourcing: call `outreach_get_day` with the preserved `day`,
     `intent: source_invitation_leads`, and the requested `targetCount` (20 for the standard run).
   - Approved invitation delivery: call `outreach_get_day` with the preserved `day` and
     `intent: send_approved_invitations`.
   - Day inspection: call `outreach_get_day` with the preserved `day` and `intent: inspect_day`.
   - Follow-up checking or delivery: call `outreach_get_follow_ups`; it is calendar-agnostic.
   The schedule action is platform configuration and does not require an Outreach read before
   invoking its installer.
4. Follow the returned recommended action and reread workflow status after every transition.
5. Continue while the server reports remaining work.
6. Stop only for server-declared completion, a typed external blocker or a human decision.

## Qualification and writing

Call `outreach_get_agents` before qualification or message writing. Use the selected active Agent's
search instructions, message instructions and Messaging Checklist for judgment and language only.
Agent guidance does not determine workflow order, dates, recovery or authorization.

## Approval and delivery

Human approval applies to the exact current message body. LinkedIn delivery requires an authenticated
browser. Perform the authorized browser action, verify the result against LinkedIn, report the
accepted evidence through the named Mosaico tool, and reread workflow status.

Nothing is recorded merely because it happened in the browser. Never claim delivery without evidence
accepted by Mosaico.

## Incidents

If a tool returns contradictory or unusable workflow state, record the evidence with the dedicated
MCP incident tool. Do not change dates, duplicate leads, bypass approval or substitute prompt memory
for server state.
