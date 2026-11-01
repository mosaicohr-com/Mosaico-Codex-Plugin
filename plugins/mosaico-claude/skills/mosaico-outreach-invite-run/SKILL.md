---
name: mosaico-outreach-invite-run
description: Load Mosaico Outreach Leads and let Mosaico place them on days, write the owner's missing invitation drafts, send already-approved invitations, or perform those workflows safely.
---

# Mosaico Outreach Invitation Run

For Send invitations (sends approved invitations, checks connections, writes and rewrites invitation drafts),
Withdraw stale invitations and Load leads. Mosaico
decides what to do and in what order. Do not ask the person for days, scopes or counts.

## The run

1. Start: run the approved whoami capture and pass its output unchanged as `identityEvidence` to
   `outreach_start_run`. Intent: `send_approved_invitations` (Send invitations), `manage_leads` (Withdraw). Load leads starts no run. If whoami cannot run, send the Me page's profile address as
   `observedLinkedInProfile`. Keep the `runId` and pass it on every call; never pass `ownerUserId`. An Owner or Admin
   running for a colleague passes `onBehalfOfMemberId` at the start only, and the pane must be hers.
2. Read: `outreach_get_day` with the intent and `runId` (Send invitations also with today's date), or `outreach_get_withdraw_queue` with the `runId`.
3. Do exactly what `step` says: make `step.call`, adding only what `supplyAlso` names (when it names
   `identityEvidence`, run whoami again and pass its output unchanged); run `step.evidence.directive`; write from
   `step.agentInstructions` and `step.guidance`. Follow `then`, then repeat until the step names `outreach_end_run`.
4. A run-level blocker (`recommendedAction`) stops the run: tell the person what Mosaico said. A refusal about one
   Lead is recorded and the run goes on.
5. End with `outreach_end_run`. Give `report.lines` and `report.sections` unchanged, adding only what a heading asks for.
6. An answer without `step` means the plugin and the Mosaico server must be updated together: stop and say so. Likewise if a saved routine text needs a newer plugin than 0.13.0 or a section this skill lacks: stop and report that the plugin needs updating.

## What only this machine can enforce

- Use only the production Mosaico connector connected in Claude. None connected: stop and say to connect it in
  Claude's connectors (not /mcp). Never a stage, test, localhost or amplifyapp server. Another environment than
  production stops the run.
- If a call is refused because the connector is acting as a member of another organisation, or its acting session
  ended, stop and report Mosaico's sentence word for word. Never end the acting session yourself.
- LinkedIn captures run only in Claude's built-in browser pane, never the Chrome extension, only through the
  one-line directive `// mosaico run <script>.js <PLACEHOLDER>=<value>` as the whole script. Never print, retype,
  paraphrase, reorder, shorten or extend a script. If the gate refuses it, read the script with the file-reading
  tool and run it word for word; with no browser folder in the plugin, stop and report that it needs updating.
- Pass every script's output to Mosaico unchanged, `integrity` included; on `evidence-altered` capture again.
- Never read, copy, export or reconstruct a LinkedIn cookie, token or session, or write a LinkedIn script yourself.
- A LinkedIn warning, captcha or restriction stops the run at once: end it `blocked` with `linkedInIssue` and a note.
- Contradictory state from a tool: record it with `incident_log_mcp_report`; never use memory instead of Mosaico.
- A held Lead is skipped with its reason; never re-send it.
- If LinkedIn asks for the person's email, send nothing and record `email-required`, never `cannot-message`.
- In a Withdraw run, record a withdrawal only after LinkedIn shows the invitation gone; never click Connect or Message.
- Routines Board: when the routine text has a `routines board:` line, write this run to that board in one batch
  after the report, with the `ArtifactData` tool, in the shape the page's header comment gives (`assets/routines-board.html`).
  A failed board write is one line in the report, never a halt.

## Load leads routine

Start no run and open no LinkedIn page. Read the Leads the person gave you and load each Agent's rows with
`outreach_load_leads`, one page at a time, following `nextAction`. Report placed, skipped and rejected rows as Mosaico
answers; fix or re-send none. With nothing to load, say "Nothing to load." Board key `load-leads`.

## Send invitations routine

Run intent `send_approved_invitations`. Open `https://www.linkedin.com/feed/` once. Board key `send-invitations`.

## Withdraw stale invitations routine

Run intent `manage_leads`, read `outreach_get_withdraw_queue`. Open `https://www.linkedin.com/feed/` once. Board key `withdraw`.

If a tool named here is missing: role or no subscription; with an active subscription, the list is out of date: reconnect.
