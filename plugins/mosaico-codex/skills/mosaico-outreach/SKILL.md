---
name: mosaico-outreach
description: Run, resume, or inspect a Mosaico Outreach day through the connected Mosaico MCP server and an authenticated browser.
---

# Mosaico Outreach

Mosaico is the workflow authority and system of record. The model operates the workflow; it does not
reconstruct workflow state from conversation memory, draft lists, batch history or browser state.

## Start or resume

1. Resolve the person's explicit intent and calendar date and preserve that date throughout the run.
   Only Owners and Admins can use Outreach.
2. When the skill is invoked without an explicit intent, ask "What do you want to do in Mosaico
   Outreach?" and present these action headers and descriptions. Person-specific recommended actions
   may be mentioned inside the matching action, but must never replace the two all-dates follow-up
   actions:
   - **Source invitation Leads** — Source each Agent's Leads per run, which Mosaico files into free days, and save
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
   - **Repair the Outreach backlog** — List the repair queue Mosaico keeps behind the daily Sync data
     run and what a person should do. Read-only here; the repair itself runs from Claude.
   - **Install the Outreach schedules** — Idempotently create the Source leads schedule (every two
     hours in business hours). Sync data (connections and messaging, once a day, the only one that
     sends) and Repair (once a week) are installed from Claude, because Codex cannot capture
     connection evidence.
   Route Agent management to `$mosaico:mosaico-outreach-agent-management`, Lead management to
   `$mosaico:mosaico-outreach-lead-management`, the read-only repair queue to
   `$mosaico:mosaico-outreach-repair-run`, and schedule installation to
   `$mosaico:mosaico-outreach-schedule-install`.
3. Use the current application-owned read for the resolved intent. Before any of
   these reads, open LinkedIn's Me page, report the profile URL you see to `outreach_start_run` with
   the matching intent (`inspect_day` for inspection), keep the `runId`, pass it on every Outreach
   read and write, and stop and tell the person on any blocker. Never pass `ownerUserId` on a write. Never read a Message, Connect or Pending button as a connection state: the invite and follow-up skills carry LinkedIn's own profile data to Mosaico, which decides.
   The invite and follow-up skills give the exact steps. Do not ask the menu again when the person's intent is already explicit:
   - Invitation sourcing: call `outreach_get_day` with
     `intent: source_invitation_leads` and the sourcing `runId`, no `day` and never a `targetCount`.
     Start that run with no quota and no colleague, as the invite-run skill describes.
   - Approved invitation delivery: call `outreach_get_day` with the preserved `day` and
     `intent: send_approved_invitations`.
   - Day inspection: call `outreach_get_day` with the preserved `day` and `intent: inspect_day`.
   - Follow-up checking or delivery: call `outreach_get_follow_ups`; it is calendar-agnostic.
   The schedule action is platform configuration and does not require an Outreach read before
   invoking its installer.
   The sourcing plan lives on each Agent in Outreach (Agent tab): Leads per day (the most on one day), Leads per run
   (what one run delivers) and Sourced by (a colleague, or the owner when empty). An Agent is sourced only when it is on and
   both numbers are set. Every run delivers its Leads per run and Mosaico files them into free days, so the skills and
   schedules carry no numbers and no days. If no Agent has both numbers, Mosaico says so and the run tells the person to set
   them there; if every Agent is full for the next 10 business days, there is nothing to source.
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
