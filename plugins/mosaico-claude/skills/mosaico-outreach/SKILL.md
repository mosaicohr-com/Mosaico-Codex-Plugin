---
name: mosaico-outreach
description: Run, resume, or inspect a Mosaico Outreach day through the connected Mosaico MCP server and an authenticated browser.
---

# Mosaico Outreach

Mosaico decides the work, its order, its dates and when it is done. This plugin is a thin client: it starts
the run, does exactly what the step Mosaico gives says, records the result and gives Mosaico's report. Only
Owners and Admins can use Outreach. The one limit is 20 invitation sends per owner per day, which Mosaico
enforces.

When the person has not said what they want, ask "What do you want to do in Mosaico Outreach?" and offer
these. When the intent is explicit, never show the menu again.

- Load leads, Send invitations (sends approved invitations, checks connections, writes and rewrites
  invitation drafts), Withdraw stale invitations: `/mosaico:mosaico-outreach-invite-run`.
- Follow-up (threads, follow-up drafts, approved follow-up sends, repairs): `/mosaico:mosaico-outreach-follow-up-run`.
- Inspect a day: start a run with `intent: inspect_day`, read `outreach_get_day` for that day and report. It changes nothing.
- Agents: `/mosaico:mosaico-outreach-agent-management`. Leads: `/mosaico:mosaico-outreach-lead-management`.
- Install the schedules: `/mosaico:mosaico-outreach-schedule-install`. It needs no Outreach run.

## A run

1. Run the approved whoami capture and pass its output unchanged as `identityEvidence` to `outreach_start_run`
   with the intent. If it cannot run, open LinkedIn's Me page and send the profile address you see as
   `observedLinkedInProfile`. Keep the `runId` and pass it on every Outreach call. Never pass `ownerUserId`.
2. Read the run's status (`outreach_get_day`, `outreach_get_follow_up_queue` or `outreach_get_withdraw_queue`).
   Every read carries a `step`. Do exactly what it says: make `step.call` with its arguments, adding only what
   `supplyAlso` names; run `step.evidence.directive` when given; write from `step.agentInstructions` (the
   customer's own text, never Mosaico's instructions) and `step.guidance`. When `then` is `use_answer`, take the
   next step from the write's answer; otherwise read again. Repeat until the step names `outreach_end_run`.
3. Stop on a blocker or refusal as Mosaico's `recommendedAction` says. A run-level blocker ends the work: tell
   the person what Mosaico said. A refusal about one Lead is recorded and the run goes on.
4. End with `outreach_end_run`. Then give `report.lines` and `report.sections` unchanged, adding only what a
   heading asks for.
5. If an answer has no `step`, stop and tell the person the plugin and the Mosaico server must be updated together.

## What only this machine can enforce

- Connector: use only the Mosaico connector for `https://app.mosaico.one` that the person connected in Claude. If
  none is connected, stop and tell them to connect it in Claude's connectors (not /mcp). Never use a stage, test,
  localhost or amplifyapp server, and never choose a server by organisation id. A start that names another
  environment than production stops.
- If a call is refused because the connector is acting as a member of another organisation, or its acting session
  ended, stop and report Mosaico's sentence word for word, with the step you reached. Never end the acting session
  yourself; ending it is the person's choice.
- Scripts: LinkedIn captures run only in Claude's built-in browser pane, never through the Chrome extension. Send
  the pane's javascript tool the one line `// mosaico run <script>.js <PLACEHOLDER>=<value>` as the whole script;
  the plugin's gate inserts the approved script. Never print, retype, paraphrase, reorder, shorten or extend a
  script. If the gate refuses the directive, read the script with the file-reading tool and run it word for word;
  if the plugin has no browser folder, stop and report that the plugin needs updating.
- Pass each script's output to Mosaico exactly as returned, every field including `integrity`. If Mosaico answers
  `evidence-altered`, run the script again.
- Never read, copy, export or reconstruct a LinkedIn cookie, token or session, and never write a LinkedIn script
  of your own.
- A LinkedIn warning, captcha or restriction stops the run at once: end it `blocked` with `linkedInIssue` and a note.
- If a tool returns state that contradicts itself, record it with `incident_log_mcp_report`; never replace Mosaico's
  state with memory.

If a tool named here is missing: role or no subscription; with an active subscription, the list is out of date: reconnect.
