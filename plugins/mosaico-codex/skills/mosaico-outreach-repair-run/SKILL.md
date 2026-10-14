---
name: mosaico-outreach-repair-run
description: List Mosaico's Outreach repair queue and what a person should do about it. Read-only in Codex; the repair itself runs from Claude.
---

# Mosaico Outreach Repair Queue (read-only)

The Outreach repair backlog is the work behind the daily Follow-up and Send invitations runs: Leads nobody verified, drafts that
break a rule, addresses LinkedIn redirected, one person held twice, declines nobody applied. Working it
needs LinkedIn's own data (a profile capture, a thread capture), and only Claude's built-in browser pane
can capture that. So the Codex package only reads the queue and says what a person should do. It never
starts a Repair run, never writes to Mosaico, never sends or approves anything, never reads a LinkedIn
page and never captures connection evidence. This package cannot capture connection evidence.

Mosaico owns the list, its order and the exact call for every item. Do not rebuild it from other reads.
Only Owners and Admins can use Outreach.

## While the connector is acting as a member

Outreach runs only as the person themselves and never inside a customer. If an Outreach call is refused with
"Outreach and incident tools are not available while your connector is acting as a member of another
organisation. End the session first.", the connector is acting as a member of a customer's organisation. Stop
there. Report that sentence word for word, the step you reached and anything done that Mosaico did not
record. Do not try the call again, do not use another tool or the browser to get round it, and do not end the
session yourself: ending it is the person's choice, in the Mosaico web console or by asking you. A scheduled
run reports and stops the same way.

If a call is refused with a sentence that begins "Your session acting as" and says "This call did not run.
Repeat it", the acting session ended while you worked. Mosaico refuses the next call once to tell you. Repeat
that same call once, with the same arguments. It then runs as the person in their own organisation, and the
run goes on.

## List the queue

1. Call `outreach_get_repair_queue` with no `runId`. A read without a run lists the items and withholds
   every write action; that is expected here. Do not pass `ownerUserId` unless an Owner or Admin asks for a colleague's queue.
2. Report in plain words, from Mosaico's answer and not from memory:
   - `summary`: how many items each group holds (`duplicates`, `addresses`, `declinedPending`, `mismatches`,
     `repairSuggestions`, `unverified`) and the total, with `summary.needsPerson` counted separately;
   - for each listed item, in the order Mosaico gives them (`workOrder`, then the order inside the group):
     `personName`, its one-line `reason` and the action it needs (`action`);
   - `excludedAsFollowUpWork` (top level and in `summary`): the Repair queue holds only the backlog outside the follow-up queue
     (server release 20261013a), because the Follow-up routine makes the repairs of the Leads it lists; duplicate pairs stay here;
   - `progress.remaining` and `nextCursor` when more items exist (pass `nextCursor` as `cursor` to list the
     next ones), and the cap: a Repair run works at most `cap.perRun` items.
3. Say what a person should do:
   - Run the Repair routine from Claude: start the Claude plugin's `mosaico:mosaico-outreach-repair-run`
     skill (or wait for its weekly schedule). It starts a run with `outreach_start_run` intent `repair`,
     verifies connections with `outreach_record_connection_evidence`, reads threads and records outcomes with
     `outreach_deposit_conversation`, fixes addresses and drops declined Leads with `outreach_update_lead`,
     links duplicate Leads with `outreach_link_duplicate_leads`, captures the connections list with
     `outreach_record_connections_snapshot`, and reports from `outreach_get_run`.
   - For items in `summary.needsPerson` (a Lead with no profile address to open, a thread Mosaico found no
     conversation for twice, or a profile capture that failed twice), a person checks or adds the profile
     address in Outreach, To sort.
   - For a history-mismatch item, a person compares the stored sent Messages with the LinkedIn thread in
     Outreach, To sort, then clears the flag; the Repair routine only looks for a decline there.
4. Do not call any write tool, do not start a run, do not open LinkedIn and do not offer to. If the person
   wants the repair done, point them to Claude.

Never pass `ownerUserId` on a write; this skill makes none.
