---
name: mosaico-outreach-follow-up-run
description: Check Mosaico Outreach for new LinkedIn follow-ups, send already-approved drafts, or perform both workflows safely.
---

# Mosaico Outreach Follow-up Run

For Follow-up: Mosaico lists the connections to capture, threads to read, follow-up drafts to write or rewrite,
approved follow-ups to send and the repairs it can decide from evidence (duplicates, redirected addresses,
unapplied declines, history mismatches). It writes follow-up drafts only, never invitation drafts. Mosaico
decides what to do and in what order. Do not ask the person for days or scopes.

## The run

1. Start: open `https://www.linkedin.com/feed/` once, run the approved whoami capture and pass its output
   unchanged as `identityEvidence` to `outreach_start_run` with `intent: follow_up_pass`. If whoami cannot run,
   send the Me page's profile address as `observedLinkedInProfile`. Keep the `runId` and pass it on every call;
   never pass `ownerUserId`.
2. Read `outreach_get_follow_up_queue` with the `runId`.
3. Do exactly what `step` says: make `step.call`, adding only what `supplyAlso` names (when it names
   `identityEvidence`, run whoami again and pass its output unchanged); run `step.evidence.directive`; write from
   `step.agentInstructions` and `step.guidance`. Follow `then`, then repeat until the step names `outreach_end_run`.
   Never reorder or skip items.
4. A run-level blocker (`recommendedAction`) stops the run: tell the person what Mosaico said. A refusal about one
   Lead is recorded and the run goes on.
5. End with `outreach_end_run`. Give `report.lines` and `report.sections` unchanged, adding only what a heading asks for.
6. An answer without `step` means the plugin and the Mosaico server must be updated together: stop and say so. Likewise if a saved routine text needs a newer plugin than 0.13.3 or a section this skill lacks: stop and report that the plugin needs updating.

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
- Routines Board: when the routine text has a `routines board:` line, write this run to that board in one batch
  after the report, with the `ArtifactData` tool, in the shape the page's header comment gives (`assets/routines-board.html`).
  A failed board write is one line in the report, never a halt.

## Follow-up routine

Run intent `follow_up_pass`, as above. Board key `follow-up`.

## Routines report routine

Starts no Outreach run and opens no LinkedIn page. Without a `routines board:` line, stop and report that there is
nothing to do. Otherwise read `outreach_get_routine_setup`, follow the `steps` and `reportHeadings` of the routine
`routines_report`, and use the `boardKey` of each routine. Load `ArtifactData`, `list_scheduled_tasks` and
`list_task_runs` with ToolSearch. Write to the board only what a run's own report states, in one batch, in the
shape the page's header comment gives. It touches nothing else.

## Sync data routine (superseded)

A saved schedule that says "This is the Sync data routine" is the old single schedule. Run nothing from it: start no
run, open no LinkedIn page, change nothing. Report that it must be reinstalled with the
`mosaico:mosaico-outreach-schedule-install` skill.

If a tool named here is missing: role or no subscription; with an active subscription, the list is out of date: reconnect.
