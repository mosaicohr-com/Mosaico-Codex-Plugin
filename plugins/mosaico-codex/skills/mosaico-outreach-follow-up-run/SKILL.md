---
name: mosaico-outreach-follow-up-run
description: Check Mosaico Outreach for new LinkedIn follow-ups, send already-approved drafts, or perform both workflows safely.
---

# Mosaico Outreach Follow-up Run

For Follow-up: Mosaico lists the connections to capture, threads to read, follow-up drafts to write or rewrite,
approved follow-ups to send and the repairs it can decide from evidence. Codex cannot run the approved LinkedIn
captures, so most steps name a blocker here: this skill reads the queue and reports what a person should do from
Claude. Mosaico decides what to do and in what order.

## The run

1. Start: open LinkedIn's Me page and send the profile address you see as `observedLinkedInProfile` to
   `outreach_start_run` with `intent: follow_up_pass` and `clientCapabilities: { browserEvidence: false }`. Keep the
   `runId` and pass it on every call; never pass `ownerUserId`.
2. Read `outreach_get_follow_up_queue` with the `runId` (not `outreach_get_follow_ups`).
3. Do exactly what `step` says: make `step.call`, adding only what `supplyAlso` names; write from
   `step.agentInstructions` and `step.guidance`. Follow `then`, then repeat until the step names `outreach_end_run`.
   A step with a `blocker` has no call: report it and go on only as Mosaico's answer allows. Never reorder or skip items.
4. A run-level blocker (`recommendedAction`) stops the run: tell the person what Mosaico said.
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

## Follow-up routine

Follow-up runs from Claude. If a saved text names this routine here, stop and report that it must run from Claude.
