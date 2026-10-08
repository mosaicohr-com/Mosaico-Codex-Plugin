---
name: mosaico-outreach
description: Run, resume, or inspect a Mosaico Outreach day through the connected Mosaico MCP server and an authenticated browser.
---

# Mosaico Outreach

Mosaico owns workflow state, transitions, dates, validation, recovery and completion. Resolve an
explicit intent once. Only Owners and Admins can use Outreach. When this skill is invoked without an explicit intent, ask "What do you want
to do in Mosaico Outreach?" and present these action headers and descriptions. Person-specific
recommended actions may be mentioned inside the matching action, but must never replace the two
all-dates follow-up actions:

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
- **Repair the Outreach backlog** — Work the repair queue Mosaico keeps behind the daily Sync data
  run: Leads nobody verified, drafts that break a rule, redirected addresses, duplicate Leads and
  declines nobody applied. Up to the cap Mosaico sets for one run. Never approve or send.
- **Install the Outreach schedules** — Idempotently create three local-time schedules: Sync data
  (connections and messaging, once a day), Source leads (every two hours in business hours, at
  least 60 minutes from Sync) and Repair (once a week, Sunday 10:00 AM by default, also on demand).
  Only Sync data sends.

Route Agent management to `/mosaico:mosaico-outreach-agent-management`, Lead management to
`/mosaico:mosaico-outreach-lead-management`, repair to `/mosaico:mosaico-outreach-repair-run`, and
schedule installation to `/mosaico:mosaico-outreach-schedule-install`.

**Mosaico connector.** Use the Mosaico connector that serves production (https://app.mosaico.one), the one the person connected in Claude. The plugin ships no Mosaico server of its own. If no Mosaico connector is connected, stop and tell the person to connect it in Claude's connectors (not /mcp), then rerun. Never use a server whose address contains amplifyapp.com, stage, staging, test or localhost; if that is the only Mosaico server available, stop and report it. Do not choose a server because its organisation id matches; stage and production share ids. The `outreach_start_run` answer names the environment (`environmentName`); a run on anything but production stops.

Use the current application-owned read for the resolved intent. For invitation sourcing call
`outreach_get_day` with `intent: source_invitation_leads` and the sourcing `runId`, no `day` and never a `targetCount`; start the sourcing run with no quota and no colleague, as the invite-run skill describes. For approved invitation delivery use
`intent: send_approved_invitations`; for inspection use `intent: inspect_day`. For follow-up
checking or delivery call the calendar-agnostic `outreach_get_follow_ups`. For repair start the run with
`intent: repair` and read `outreach_get_repair_queue`. Before any of
those reads, open LinkedIn's Me page, report the profile URL you see to `outreach_start_run` with the
matching intent (`inspect_day` for inspection), keep the `runId`, pass it on every Outreach read and
write, and stop and tell the person on any blocker. Never pass `ownerUserId` on a write. Never read a Message, Connect or Pending button as a connection state: the invite and follow-up skills carry LinkedIn's own profile data to Mosaico, which decides. Run an approved script by sending the browser javascript tool its one-line directive, `// mosaico run <script>.js <PLACEHOLDER>=<value>`, as the whole script: the plugin's gate inserts the approved script, so never retype one (word for word with only the first line's value changed remains a fallback). The value for every per-Lead script is the Lead's `scriptIdentifier` from the Mosaico read when present (a member id or a public identifier, whatever Mosaico supplies), otherwise the part of its profile URL after `/in/`. Every approved script's output (identity, connection evidence, connections pages, thread, sent invitations, the Sales Navigator colleague check) goes to Mosaico exactly as returned, every field including `integrity`, never retyped, trimmed, reformatted, translated or "fixed"; Mosaico refuses an altered copy with `evidence-altered` and recommends `recapture`: run the script again and pass the new output unchanged. The invite
and follow-up skills give the exact steps. Do
not ask the menu again when the person's intent is explicit. The schedule action is platform configuration and needs no
Outreach read before its installer. Follow the returned recommended action and reread status after
every transition. Call `outreach_get_agents` before qualification or writing (for a sourcing run, with the `runId`, which returns every Agent in the run's plan) and use the selected
active Agent's search instructions, message instructions and Messaging Checklist for judgment only.

The sourcing plan lives on each Agent in Outreach (Agent tab): Leads per day (the most on one day), Leads per run
(what one run delivers) and Sourced by (a colleague, or the owner when empty). An Agent is sourced only when it is on and
both numbers are set. Every run delivers its Leads per run and Mosaico files them into free days, so the skills and
schedules carry no numbers and no days. If no Agent has both numbers, Mosaico says so and the run tells the person to set
them there; if every Agent is full for the next 10 business days, there is nothing to source.

A candidate saved for a colleague first goes through the Sales Navigator colleague check (invite-run skill). From
plugin 0.9.11 its output also carries `complete`, `controlTotal`, `visibility` and `unreadableRows`, and it goes to
Mosaico unchanged. Mosaico, not the model, decides what it proves. When the check shows the search could have found
the candidate and did not (a proven negative), Mosaico saves the Lead as verified not connected by the colleague
check and the run drafts her invitation at once; otherwise the Lead is saved with its connection unknown, stays
undrafted, and her own run verifies it first. The send guard: a colleague's invitation is never sent on that check
alone; her own Sync run must record her own connection evidence first (`own-evidence-required`). A run never
records connection evidence for a colleague's Lead (`evidence-owner-mismatch`). The risk accepted: nobody has yet
tested a colleague who hides her connections, so a proven negative could in rare cases be wrong; the send guard
contains it, because nothing goes out before her own check.

Human approval applies to the exact current message. For LinkedIn delivery, perform the authorized
browser action, verify the external result, report evidence through the tool named by Mosaico and
reread status. Never infer delivery from a click or reconstruct workflow state from conversation
memory. Record contradictory tool behavior through the dedicated MCP incident tool.
