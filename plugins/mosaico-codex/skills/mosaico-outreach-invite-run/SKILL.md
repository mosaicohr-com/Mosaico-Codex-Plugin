---
name: mosaico-outreach-invite-run
description: Load Mosaico Outreach Leads and let Mosaico place them on days, write the owner's missing invitation drafts, send already-approved invitations, or perform those workflows safely.
---

# Mosaico Outreach Invitation Run

For Send invitations, Withdraw stale invitations and Load leads. Mosaico decides what to do and in what order. Do not ask the person for days, scopes or counts. Codex
cannot run the approved LinkedIn captures: a step that needs one is for Claude's built-in browser pane.

## The run

1. Start: open LinkedIn's Me page and send the profile address you see as `observedLinkedInProfile` to
   `outreach_start_run`, with `clientCapabilities: { browserEvidence: false }`. Intent: `send_approved_invitations`
   or `manage_leads` (Withdraw). Load leads starts no run. Keep the `runId` and pass it on every call; never pass
   `ownerUserId`.
2. Read: `outreach_get_day` with the intent and `runId` (Send invitations also with today's date), or `outreach_get_withdraw_queue` with the `runId`.
3. Do exactly what `step` says: make `step.call`, adding only what `supplyAlso` names; write from
   `step.agentInstructions` and `step.guidance`. Follow `then`, then repeat until the step names `outreach_end_run`.
   A step with a `blocker` has no call: record nothing for it, report it, and go on only as Mosaico's answer allows.
4. A run-level blocker (`recommendedAction`) stops the run: tell the person what Mosaico said. A refusal about one
   Lead is recorded and the run goes on.
5. End with `outreach_end_run`. Give `report.lines` and `report.sections` unchanged, adding only what a heading asks for.
6. An answer without `step` means the plugin and the Mosaico server must be updated together: stop and say so.

## What only this machine can enforce

- Use only the production Mosaico connector added in Codex. None connected: stop and say to add it. Never a stage,
  test, localhost or amplifyapp server. Another environment than production stops the run.
- If a call is refused because the connector is acting as a member of another organisation, or its acting session
  ended, stop and report Mosaico's sentence word for word. Never end the acting session yourself.
- Never read, copy, export or reconstruct a LinkedIn cookie, token or session, or write a LinkedIn script yourself.
- A LinkedIn warning, captcha or restriction stops the run at once: end it `blocked` with `linkedInIssue` and a note.
- Contradictory state from a tool: record it with `incident_log_mcp_report`; never use memory instead of Mosaico.
- A held Lead is skipped with its reason; never re-send it.
- If LinkedIn asks for the person's email, send nothing and record `email-required`, never `cannot-message`.
- In a Withdraw run, record a withdrawal only after LinkedIn shows the invitation gone; never click Connect or Message.

## Load leads routine

Start no run and open no LinkedIn page. Read the Leads the person gave you and load each Agent's rows with
`outreach_load_leads`, one page at a time, following `nextAction`. Report placed, skipped and rejected rows as Mosaico
answers; fix or re-send none. With nothing to load, say "Nothing to load." If the saved text needs a newer plugin than
0.13.3, stop and report that the plugin needs updating.
