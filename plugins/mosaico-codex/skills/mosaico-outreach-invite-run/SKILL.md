---
name: mosaico-outreach-invite-run
description: Source 20 qualified Mosaico Outreach Leads per selected day and prepare drafts, send already-approved invitations, or perform both workflows safely.
---

# Mosaico Outreach Invitation Run

Before using any Outreach or browser tool, ask these questions in order unless the person already
provided the answer as part of the current invocation:

1. "Which days should this run cover: today, tomorrow, or a specific set of dates?"
2. "For those days, do you want to source Leads and prepare invitation drafts, source Leads only, send approved invitations, or both?"

Resolve today and tomorrow using the person's local business date. Preserve the exact selected dates
throughout the run. Accept one action and run only the selected scope. A scheduled run does not ask these questions: the **Source leads routine** section at the end of this skill carries its answers.

## Start the run

1. Open LinkedIn's Me page in the authenticated browser and read the profile URL of the signed-in
   account. Report what you see; do not decide or correct it.
2. Call `outreach_start_run` with that URL as `observedLinkedInProfile` and the intent: `source_invitation_leads` for sourcing, `send_approved_invitations` for sending. When doing both, start a separate run for each scope.
   A sourcing start sends no quota and no colleague. Mosaico holds the sourcing plan on the Agents: each
   Agent has Leads per day and Sourced by, set by a person in Outreach (Agent tab). Mosaico takes every
   active Agent the person sources (their own, and a colleague's that names them in Sourced by), works out
   how many Leads each owner still needs today (Leads per day minus the Leads already accepted today, so a
   later run only tops up) and returns that as `run.quota`, with the plan in `run.sourcingPlan`. Never send
   `quota` or `colleagueOwnerUserId`, and never ask the person for numbers. Read the outcome:
   - A normal run, with `run.quota` and `run.sourcingPlan`: go on.
   - Blocked with `sourcing_plan_empty` (recommended action `set_leads_per_day_in_outreach`): no Agent has
     Leads per day for this person. Stop. A scheduled run quotes Mosaico's code and message verbatim and
     ends its report with this sentence: "Set Leads per day on an Agent in Outreach (Agent tab), then rerun."
   - A run issued with the note `sourcing-plan-already-met`: every Agent is already at its number. Do no
     sourcing and end with a short report; `outreach_get_day` then says the run is complete, reason
     `sourcing-quota-met`.
3. Keep the returned `runId` and pass it on every `outreach_get_day` or `outreach_get_follow_ups`
   read and on every `outreach_save_lead`, `outreach_update_lead`, `outreach_record_message`,
   `outreach_deposit_conversation`, `outreach_mark_message_sent`, `outreach_record_delivery_block`
   and `outreach_record_connection_evidence` call. Never pass `ownerUserId` on
   a write; Mosaico takes the owner from the run.
4. Tell a run-level blocker from a one-Lead outcome. A run-level blocker is about the run itself:
   LinkedIn identity mismatch or not registered, the run expired, unknown or foreign, sign-in lost,
   or Mosaico or LinkedIn failing. Only then stop and tell the person what Mosaico says; do not retry
   with a different profile or work around it. Everything else is about one Lead or one Message:
   a `skipped` result, a `blocked` state, a refused write, a `history-mismatch`, a draft that
   already exists, a conflict, a not-found. Record what Mosaico returned, skip that Lead and
   continue with the next one; Mosaico keeps the Lead for a person in To sort. A scheduled run
   never stops for one Lead.
5. Before `outreach_deposit_conversation`, `outreach_mark_message_sent`,
   `outreach_record_delivery_block` and `outreach_record_connection_evidence`, open the Me page again
   and pass the profile you see then as `observedLinkedInProfile`.
6. If an Owner or Admin asks to run for a colleague, pass that member's id as `onBehalfOfMemberId` on
   `outreach_start_run` only. The LinkedIn account must then be that colleague's.

When a profile already exists under another owner, read the state Mosaico returns and follow its
recommended action. If `outreach_save_lead` returns `skipped` with `continue_sourcing`, nothing was
saved and this is not a blocker: note the candidate for your final report, source a replacement and
keep going. Mosaico records the skip on the run and does not count it toward the target. Stop only
when Mosaico returns a blocker, `human_decision_required` or `stop_run`; then show the person the
owner, Lead and status it returned. `outreach_deposit_conversation` returns such a blocker for a new
Lead. Re-send with `acknowledgeProfileOnOtherOwner: true` only after the person decides to; never
set it yourself.

## Source Leads and prepare drafts

1. Read `outreach_get_agents`, then call `outreach_get_day` for each selected day with
   `intent: source_invitation_leads` and the `runId`. Never send `targetCount` for sourcing:
   Mosaico takes the target from the run's sourcing plan.
2. Follow `workflowStatus.recommendedAction`. Use its prepared count, remaining count, blockers and
   completion result; do not reconstruct them from separate records or conversation memory. When the
   recommended action is `verify_connection`, Mosaico lists the Leads whose connection is unknown or
   unverified in `workflowStatus.unverifiedLeads`, each with its profile URL: for each one run
   **Capture connection evidence**, then reread `outreach_get_day`. Never guess a connection and never
   skip to drafting for a listed Lead.
3. A day is incomplete until Mosaico says the sourcing plan is met. Continue searching, broadening suitable
   searches, checking profiles, saving qualified Leads with their profile details and preparing
   missing invitation drafts until it does.
4. Do not stop because the work is slow, difficult, expensive or because an initial search produced
   only a few Leads. Loading a few Leads is not completion; if Mosaico still shows Leads remaining, continue until
   it says the plan is met.
5. Save each qualified Lead through `outreach_save_lead` with the `agentId` the day read gave for that owner (see
   **Which Agent a Lead goes to**), which takes no connection state: the new Lead
   starts unknown. Then run **Capture connection evidence** for it, so Mosaico records connected,
   invite-pending or not-connected before any draft is written. Write the missing outbound Invite draft
   only for a Lead Mosaico lists as verified. Do not approve or send any invitation in this scope.
6. Reread `outreach_get_day` after every saved Lead and draft. Mosaico preserves partial progress and
   owns the completion predicate; a valid partial save is not a completed run.
7. Report a shortfall only when a genuine Mosaico, authentication, LinkedIn or human-decision blocker
   prevents further work. State the exact completed count, remainder and blocker; never report the
   day as complete while Mosaico shows Leads remaining.
8. Finish with **Report a sourcing run**.

## Source Leads only

Use this scope when the Leads go to the owners in the run's sourcing plan (the person's own Agents, and a
colleague's Agent that names the person in Sourced by) before any draft is written, so that each owner's
drafts are later written under their own Agent and voice.

1. Same as "Source Leads and prepare drafts", but the target is the run's sourcing plan: each Agent's Leads
   per day minus the Leads already accepted today, not the 20 of a prepared day. Mosaico keeps the plan and
   reports what remains for each Agent; use its counts, and `workflowStatus.counts.readyLeads` for the
   ready Leads, not the prepared count.
2. Save each qualified Lead with its profile details and the planned `agentId` through `outreach_save_lead`, which takes no
   connection state, then run **Capture connection evidence** for it. Do not write any invitation draft
   in this scope, and do not approve or send anything.
3. Reread `outreach_get_day` after every saved Lead and continue until Mosaico says the sourcing plan is met
   (complete, reason `sourcing-quota-met`) or returns a blocker, `human_decision_required` or `stop_run`.
4. Finish with **Report a sourcing run**. A run below its plan is not complete.

## Which Agent a Lead goes to

In a sourcing run Mosaico plans the Agents. `outreach_get_day` lists them in `workflowStatus.sourcingPlan`,
each entry giving the owner, `agentId`, `agentName`, `leadsPerDay`, `acceptedToday` and `remainingToday`.
`workflowStatus.agentId` is the Agent to pass as `agentId` on `outreach_save_lead` for the owner of that
read, and `workflowStatus.nextAgentId` is the one for the next owner (`nextOwnerUserId`) who still needs
Leads. Pass the `agentId` the read gave for that owner on every save. Never choose an Agent yourself and
never send `targetCount` for sourcing. If Mosaico blocks a save:

- `agent-not-in-sourcing-plan`: that Agent is not planned for this owner. Save again once with the
  `agentId` in Mosaico's hint.
- `planned-agent-quota-met`: that Agent is already at its Leads per day while another Agent of the owner
  still needs Leads. Save again once with the `agentId` Mosaico gives.
- `agent-required`: save again once with the `agentId` the day read gave for that owner.

Then reread `outreach_get_day`. Nothing was saved by a blocked save.

## The colleague check (Claude only)

When a candidate is saved for a colleague, a Claude run first checks in Sales Navigator whether the
candidate is already connected to that colleague, with the plugin's approved script, and passes its output to
Mosaico as `colleagueConnectionEvidence` on `outreach_save_lead`. Mosaico decides: it skips a candidate who is
already connected (`already-connected-to-colleague`, not a failure and not counted toward the target). This
package ships no browser scripts, so Codex cannot run that check and cannot pass the evidence. Never
make up evidence and never work around the answer. When Mosaico blocks a save for a colleague with
`colleague-check-required`, nothing was saved: do not retry it, list the candidate as skipped with Mosaico's code
and reason, and say in the report that Leads for that colleague need a Claude run. Saves for the run owner
need no check. Read `workflowStatus.colleagueChecks` and `workflowStatus.colleagueSkips` only to report them.

## Report a sourcing run

Report in plain words, using Mosaico's counts, not memory: for each owner and each of their Agents in
`workflowStatus.sourcingPlan`, the Leads saved and the Leads remaining today (name the owner and the Agent), the candidates skipped as already connected
to that owner ("skipped as already connected to <owner>: N", from `workflowStatus.colleagueSkips`; its
entries name the owner), and any shortfall with its blocker. A run
that saved nothing is a failed run: report it as failed with Mosaico's code and message (for example
`sourcing_plan_empty` or the blocker that stopped it), including a run
Mosaico refused at the start. Never report such a run as successful, and never describe a partly filled
plan as complete. A run Mosaico issued with the note `sourcing-plan-already-met` saved nothing because every
Agent was already at its number: report it as complete, not failed. When Mosaico answers
`sourcing_plan_empty`, the report says: "Set Leads per day on an Agent in Outreach (Agent tab), then rerun."

## Send approved invitations

1. Call `outreach_get_day` for each selected date with `intent: send_approved_invitations` and
   the `runId`. Work only on exact outbound Invite messages returned as
   Approved and permitted by `workflowStatus`. Messages listed under
   `workflowStatus.blockedDeliveries` are never sent; do not retry them. When the recommended action
   is `verify_connection`, run **Capture connection evidence** for each Lead in
   `workflowStatus.unverifiedLeads` and reread the day before sending anything.
2. Never approve, rewrite, replace or substitute an invitation. If the approved body does not exactly
   match the body about to be sent, stop for that invitation and report the blocker.
3. Before each invitation run **Capture connection evidence** for its Lead. Mosaico answers connected,
   invite-pending or not-connected and records it. Send the invitation only when the answer is
   not-connected and Mosaico still lists the invitation as Approved. For connected or invite-pending
   Mosaico removes the invitation from the send list itself: do nothing more and continue with the next
   one. If the capture gave Mosaico nothing it could use, do not send: leave the Lead unverified, list
   it as skipped and continue. Never call `outreach_record_delivery_block` with `already-connected` or
   `invite-pending`.
4. Send through the authenticated LinkedIn browser.
5. Verify each invitation against LinkedIn rather than trusting the click.
6. Call `outreach_mark_message_sent` only after successful delivery verification, using the exact
   Lead and Message identities and the exact send time when LinkedIn exposes it, otherwise null.
   Codex cannot run the approved sent-invitations script, so it cannot pass `sentInvitationEvidence`: Mosaico
   records the mark as a reading of the screen and answers `send-proof-missing`. Say so in the final
   report, with each Lead. A Claude run, which runs the sent-invitations script after the send, confirms a send from
   LinkedIn's data and is the one to send invitations. If Mosaico answers `send-not-confirmed` it did
   not go out: do not retype it and do not mark it sent; call `outreach_record_delivery_block` with
   `reason: cannot-message` and continue.
7. Reread the same day after each send, capture or recorded outcome and continue until Mosaico reports
   completion or a genuine blocker (Mosaico, sign-in or LinkedIn failure). One Lead that cannot be
   invited never stops the run.
8. In the final report list recorded outcomes and Leads left unverified separately from sends and
   blockers, each with its Lead and reason, and name the sends marked by screen.

## Capture connection evidence

Whether you are connected to a Lead is a fact in LinkedIn's own data, not on the page's buttons. Mosaico
records a connection state only from that data, carried by the connection-evidence capability of the
Mosaico plugin for Claude Code: one approved script, run word for word in the signed-in LinkedIn page and
enforced by that plugin's browser-script gate. The Codex package has no such capability, so this run does
not capture connection evidence. For the same reason the Codex package cannot run the approved whoami
script either; read LinkedIn's Me page as above:

1. Never read, copy, export or look for a LinkedIn cookie, token or session: not from the page, browser
   storage, profile files, DevTools data or the keychain. Never write a script that calls LinkedIn.
2. Do not call `outreach_record_connection_evidence`; it accepts only what the approved script returns.
3. Leave the Lead unverified and list it as skipped, noting in the report only what the LinkedIn page
   visibly shows (a Message, Connect or Pending button) for the person to read. That note is never a
   connection state and never a reason to draft or send.
4. Continue with the next Lead. When the run cannot proceed without a verified connection, stop that
   step and report it.

## Both

1. Complete **Source Leads and prepare drafts** first, until Mosaico says the sourcing plan is met for every selected date.
2. Reread the current Mosaico state for those dates.
3. Complete **Send approved invitations** only for messages that were already human-approved. Never
   approve a newly created draft automatically.

For every scope, Mosaico is the workflow authority for stored state, target completion, ownership,
validation, allowed actions and recovery. Stop only when the selected scope is complete, Mosaico
reports a genuine blocker, or a human decision is required. Mosaico decides which member a record belongs to from the run; do not try to work that out yourself.
Only Owners and Admins can use Outreach.

## Source leads routine

This is the Source leads flow of Mosaico Outreach. It only finds Leads and writes invitation drafts. It never approves, sends or messages; the Sync data schedule, installed from Claude, does that.

The schedule's text carries only the person's standing answers: the timezone; the day is the next business day and the actions are "source Leads only", then "source Leads and prepare invitation drafts". The number of Leads per day and who sources them are not in the schedule: they are set on each Agent in Outreach (Agent tab), and Mosaico holds them. Take them from there; the schedule supplies the answers to this skill's opening questions, so do not ask them, do not show a menu, and do not ask which days or which scope. If a standing answer is missing, stop and report which one.

Resolve the current business date and time in the timezone from the schedule's standing answers. The person has supplied standing answers for this recurring automation: proceed without asking which days or which scope.

Use the authenticated LinkedIn browser. Never read, copy, export or reconstruct a LinkedIn cookie, token or session; never write a LinkedIn script of your own; never read a Connect, Message or Pending button as a connection state; never set a connection state yourself.

Step 1. Open LinkedIn's Me page once and read the profile URL of the signed-in account. Report it as observedLinkedInProfile to outreach_start_run. Send no quota and no colleague: Mosaico derives the quota from the sourcing plan on the Agents. Start the sourcing run once (Step 2 and Step 3 use the same run) and pass its runId on every read and write. If Mosaico blocks the start, stop and report the blocker; do not work around it. If it answers sourcing_plan_empty (recommended action set_leads_per_day_in_outreach), stop: quote Mosaico's code and message verbatim, then end the report with this sentence: "Set Leads per day on an Agent in Outreach (Agent tab), then rerun." Do not ask the person for numbers. If Mosaico issues the run with the note sourcing-plan-already-met, every Agent is already at its number: do no sourcing and end with a short report (outreach_get_day then says the run is complete, reason sourcing-quota-met). Otherwise the run carries run.quota and run.sourcingPlan.

Step 2. Run this skill with the selected day the next business day and the selected action "source Leads only". Mosaico assigns the day and keeps the quota it derived from the plan. Each Lead is saved directly under the target owner by the run; there is no transfer step. Follow workflowStatus.recommendedAction and reread after every saved Lead. Never send targetCount for sourcing. Read workflowStatus.sourcingPlan, workflowStatus.agentId and workflowStatus.nextAgentId from outreach_get_day and pass the agentId for the owner you save for on every outreach_save_lead, as this skill's "Which Agent a Lead goes to" says; if Mosaico blocks a save with agent-not-in-sourcing-plan, planned-agent-quota-met or agent-required, save again once with the agentId it gives. This package cannot run the colleague-connection check (it ships no browser scripts): when Mosaico blocks a save for a colleague with colleague-check-required, do not retry or work around it; list the candidate as skipped and say that Leads for that colleague need a Claude run.

Step 3. Run this skill again with the same day and the selected action "source Leads and prepare invitation drafts". This package cannot capture connection evidence. Do not draft for a Lead Mosaico lists as connection unverified; leave it unverified and list it as skipped. Write a missing invitation draft only for a Lead Mosaico lists as verified. Never approve or send an invitation.

Step 4. Stop only when Mosaico says the sourcing plan is met (complete, reason sourcing-quota-met), or when Mosaico reports stop_run after the tenth failure. In that case write the sourcing report Mosaico asks for. A skipped candidate or a refused write for one Lead is not a reason to stop.

Step 5. Report separately, using Mosaico's counts, not memory: Leads saved and Leads remaining today for each owner and each of their Agents in workflowStatus.sourcingPlan (name the owner and the Agent), candidates skipped as already connected to each owner (from workflowStatus.colleagueSkips), drafts written, candidates skipped with reasons, Leads left unverified, blockers. A run that saved nothing is a failed run: report it as failed with Mosaico's code (for example sourcing_plan_empty) and message, also when Mosaico refused the start, and never as successful; a run Mosaico issued with sourcing-plan-already-met saved nothing because every Agent was already at its number, so report it as complete. Nothing merely drafted may be described as approved or sent. Preserve Mosaico as workflow authority and never modify another owner's records.

Guards: pacing between page loads and run expiry are enforced by Mosaico; a LinkedIn warning or captcha stops the run, which then reports.
