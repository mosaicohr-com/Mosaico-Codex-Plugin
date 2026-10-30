---
name: mosaico-outreach-lead-management
description: Review, update, or create owned Mosaico Outreach Lead records without changing Agents or Messages.
---

# Manage Mosaico Outreach Leads

Lead records only: never update, delete, classify, approve or send Messages, and never change Agents. The one
exception is asking for a new draft. Only Owners and Admins can use Outreach. At the start ask whether the person
wants to update Leads, load a new Lead, load a file of already-sourced Leads, ask for a new draft, or move Leads
between colleagues.

Run (not needed for loading a file): run the approved whoami capture, pass its output unchanged as `identityEvidence`
to `outreach_start_run` with `intent: manage_leads`, and pass the `runId` on every call; never pass `ownerUserId`.
If a call is refused because the connector is acting as a member of another organisation, or its acting session ended, stop and report Mosaico's sentence word for word. Never end the acting session yourself. The connector and cookie rules of `/mosaico:mosaico-outreach` apply. A refusal about one Lead is
recorded and shown; a run-level blocker stops the work.

- Update: read `outreach_get_leads` and `outreach_get_agents`, show the Leads, and let the person pick the exact
  Leads and new values. Never infer a bulk target from a partial name. Then `outreach_update_lead`, once per Lead.
  Contact again later is `changes.nextTouchOn` (YYYY-MM-DD, proposed from the person's words, `null` clears it);
  Mosaico judges the day and returns the allowed days when it refuses one.
- Load a new Lead: choose an active Agent, ask for the Lead's values, then `outreach_save_lead`.
- Load a file of Leads: confirm the Agent, map the columns to `name`, `linkedInProfileUrl`, `company`, `jobTitle`
  and `notes`, and show the mapping and row count. Send the rows in pages with `outreach_load_leads` (no run; never
  pass `ownerUserId`), report Mosaico's answer row by row and follow its `nextAction`. Never resend a rejected row
  with changed data without asking.
- New draft: `outreach_request_redraft` with the `leadId`, and the `messageId` when one is named. Mosaico returns it
  to Draft; the next routine run writes it. Report anything it lists as `alreadyWaiting`.
- Move Leads between colleagues (Owner or Admin): `outreach_transfer_lead` or `outreach_transfer_leads`; show the
  preview and, when Mosaico asks, which Lead to merge into.

Confirm every Lead change with the person immediately before the call. A held Lead is skipped
with its reason; never re-send it. Read again and report what was saved.
