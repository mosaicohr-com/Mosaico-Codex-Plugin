---
name: mosaico-outreach-invite-run
description: Source Mosaico Outreach Leads and let Mosaico place them on days, write the owner's missing invitation drafts, send already-approved invitations, or perform those workflows safely.
---

# Mosaico Outreach Invitation Run

Before using any Outreach or browser tool, ask these questions in order unless the person already
provided the answer as part of the current invocation:

1. "Which days should this run cover: today, tomorrow, or a specific set of dates?"
2. "For those days, do you want to source Leads only, write missing invitation drafts, send approved invitations, or write drafts and send?"

Resolve today and tomorrow using the person's local business date. Preserve the exact selected dates
throughout the run. Accept one action and run only the selected scope. A scheduled run does not ask these questions: the **Source leads routine** section at the end of this skill carries its answers.
Sourcing takes no day from the person: Mosaico files each Lead on the first business day with room, so the days question applies to drafting, sending and inspection only.

## Start the run

1. Open LinkedIn's Me page in the authenticated browser and read the profile URL of the signed-in
   account. Report what you see; do not decide or correct it.
2. Call `outreach_start_run` with that URL as `observedLinkedInProfile` and the intent: `source_invitation_leads` for sourcing, `send_approved_invitations` for sending and for writing missing invitation drafts. Sourcing is always its own run; writing drafts and sending share one `send_approved_invitations` run.
   A sourcing start sends no quota and no colleague. Mosaico holds the sourcing plan on the Agents: each
   Agent has Leads per day (the most it may hold on one day), Leads per run (what one run must deliver) and
   Sourced by, set by a person in Outreach (Agent tab). Mosaico takes every active Agent that has both
   numbers and that the person sources (their own, and a colleague's that names them in Sourced by) and
   returns as `run.quota` the sum of their Leads per run, with the plan in `run.sourcingPlan`. Every run
   delivers its own Leads per run; nothing is taken off for earlier runs. Mosaico, not you, files each Lead on
   a day. Never send `quota` or `colleagueOwnerUserId`, and never ask the person for numbers.
   Lane: if the schedule's standing answers hold the line `sourcing scope: own` or `sourcing scope: colleagues`, pass
   exactly that word as `sourcingScope` on `outreach_start_run`. If there is no such line, send nothing. Never choose,
   change or invent a scope, and never send one with `quota` or `colleagueOwnerUserId`. Start a sourcing run once per
   session: never start a second one, whatever Mosaico answers. Read the outcome:
   - A normal run, with `run.quota` and `run.sourcingPlan`: go on. Check the echo: the answer's top-level
     `sourcingScope` must be the word you sent, or `all` when you sent none (`run.sourcingScope` is absent then). If it
     differs, say so in the report.
   - Every start answer names the Mosaico environment in `environmentName`. If it is not `production`, stop and report it; do not work in that environment. The report's first line is "Mosaico environment: production" (the name the answer gave).
   - The answer carries the lane in `sourcingScope`; the report's second line is "Mosaico lane: own", "Mosaico lane: colleagues" or "Mosaico lane: whole plan" (for `all`).
   - If the answer carries the note `previous-run-abandoned` (with `previousRun`), your last Source leads run of this lane was left with a line open (stopped, or closed by Mosaico after 30 quiet minutes). Say so right after the lane line, as "Previous run failed: stopped with N open" (N from `previousRun.openLines`), then go on. If the note is `previous-run-finished-not-ended`, that run had finished its work but was never ended: say so in one line, then go on. Mosaico gives either note once.
   - Blocked with `sourcing_plan_empty` (recommended action `set_agent_sourcing_numbers_in_outreach`): no Agent
     has both Leads per day and Leads per run for this person. This is loud: a failed run. Stop. A scheduled run quotes Mosaico's code and
     message verbatim and ends its report with this sentence: "Set Leads per day and Leads per run on an Agent in Outreach (Agent tab), then rerun."
   - Blocked with `sourcing-days-full` (recommended action `wait_for_free_days`): every planned Agent of this lane is full
     for the next 10 business days and no run was issued. This is not a failure. Stop and report: "Every Agent is full for the next 10 business days; nothing to source."
   - Blocked with `sourcing-run-busy` (recommended action `wait_for_current_run`): another Source leads run of this account
     is working, so no run was issued and there is no `runId`. This is not a failure. `busy` names the lane and when that
     run counts as idle (`busy.releasesAt`). Stop: do not start again and do not wait in this session. Report one line:
     "Another Source leads run is working on this account; nothing started."
   - Blocked with `sourcing-scope-empty` (recommended action `nothing_to_source`): no planned Agent is in this lane. This
     is not a failure. Stop and report: "Nothing to source for the <own|colleagues> Agents."
   - Blocked with `sourcing_scope_invalid` (recommended action `correct_sourcing_scope`): a scope was sent with a quota or a
     colleague, or for another intent. This is loud: report a failed run with Mosaico's code and message verbatim, and do
     not retry with another scope.
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
keep going. Mosaico records the skip on the run and does not count it toward the target. The skip is
`profile-exists-under-other-owner` with `heldByOtherOwner` (how many this run skipped); it also covers a person the
other owner dropped. It is never a failure: do not count it and do not stop for it. Stop only
when Mosaico returns a blocker or `human_decision_required`; then show the person the
owner, Lead and status it returned. `outreach_deposit_conversation` returns such a blocker for a new
Lead. Re-send with `acknowledgeProfileOnOtherOwner: true` only after the person decides to; never
set it yourself.

## Source Leads

A Source leads run finds Leads, saves them and lets Mosaico place them on days, then ends the run. It never writes an
invitation draft, for its own Leads or a colleague's: the Lead owner's Sync data run writes them (see **Write missing
invitation drafts**). Mosaico refuses a draft write inside any sourcing run with `sourcing-writes-no-drafts`.

1. Call `outreach_get_agents` with the `runId`. Never pass `ownerUserId` with it. It returns every Agent in this run's plan,
   yours and your colleagues', each with its own search and message instructions, checklist and attachments: work from every
   returned Agent's own instructions, including colleagues' Agents, for the Leads you save under it. Then call
   `outreach_get_day` with `intent: source_invitation_leads` and the `runId`. Leave `day` out: for a sourcing run Mosaico reads every day the run filed Leads on. Never send
   `targetCount` for sourcing: Mosaico takes the target from the run's sourcing plan. The answer's `workflowStatus.workNow`
   (also at the top of the answer) names the work to do now: see step 3.
2. Follow `workflowStatus.recommendedAction`. Use its remaining count, blockers and
   completion result; do not reconstruct them from separate records or conversation memory. The target is the run's
   sourcing plan: Mosaico reports what remains for each Agent (`remainingThisRun`), and `workflowStatus.counts.readyLeads`
   counts the ready Leads. When the
   recommended action is `verify_connection`, Mosaico lists the Leads whose connection is unknown or
   unverified in `workflowStatus.unverifiedLeads`, each with its profile URL: for each one run
   **Capture connection evidence**, then reread `outreach_get_day`. Never guess a connection. A colleague's Lead is never in that list for your run: only her own run
   verifies it. `workflowStatus.draftsToWrite` is on this read too; in a sourcing run its `writableInThisRun` is false and
   its `recommendedAction` is `none`. It is the Lead owner's Sync work: ignore it here.
3. Mosaico decides when sourcing ends, never your own judgement. Work `workflowStatus.workNow` and read it again at
   every decision point: after every saved Lead, every skipped candidate and every verification. While it says
   `state: work`, search for the Agent it names: `workNow.brief` is that Agent's own search instructions, word for word,
   `workNow.remainingThisRun` is what that Agent still owes in this run, and `workNow.agentName` names it. A supply note in a
   brief is for the final report, never a reason to stop. If `workNow.briefMissing` is true the Agent was deleted: read
   `workNow` again, because Mosaico closes its line. In a `colleagues` run your own day has no Agent of its own and Mosaico says
   so without a blocker: source for the owner `workNow` names and save for her as this skill says. While any line in `workflowStatus.sourcingPlan` has status `open`, keep sourcing. Sourcing is over only
   when `workNow` says `state: none` and `workflowStatus.completion` says the run is complete with reason
   `sourcing-quota-met` (every Agent delivered its Leads per run), `sourcing-days-full` (an Agent ran out of free days
   first: do not search for more to fill its shortfall) or `sourcing-agent-unavailable` (Mosaico closed an Agent that was
   switched off or deleted, or whose owner left: never source for it; report it from `unavailableAgents`). `workNow` with
   `state: none` and reason `run-ended` means Mosaico closed the run: stop and report it. While searching, call
   `outreach_get_run` at least every 10 minutes, or after every 10 candidates, even when nothing was saved: Mosaico closes a
   run that makes no Mosaico call for 30 minutes.
4. The stop rules, in Mosaico's words. Loading a few Leads is not completion; if a line is still `open`, continue.
   - Stop only when Mosaico says the run is complete (`workflowStatus.completion` is complete with reason sourcing-quota-met, sourcing-days-full or sourcing-agent-unavailable) and nothing is left to verify or sort, or when Mosaico recommends end_run or end_run_days_full.
   - There is no search limit: do as many searches as it takes, and "I could not find candidates", "few results", "weak results", "slow" and "enough found" are never a reason to stop.
   - When results are few, widen inside the Agent's brief (more keywords, more results pages, other filters, other regions the brief allows, Premium Daily Prospects) and keep searching; never widen past the brief's qualification rules.
   - If an Agent's brief says to report a lead supply constraint, note it for the final report and keep searching inside the brief; it never means stop.
   - A run that ends with any line still open is a failed run: report it as "run failed: stopped with N open".
   - A run keeps searching until Mosaico says the numbers are met. A candidate you reject, a person another owner already holds and a person already connected to the colleague are never failures, and Mosaico counts none in a new run.
   - Asking to end the run does not end it while a line is open: see **End the run**.
5. Save each qualified Lead through `outreach_save_lead` with `workNow.agentId` and no `ownerUserId` (see
   **Which Agent a Lead goes to**), which takes no connection state: the new Lead
   starts unknown. Never send `scheduledDate`: Mosaico ignores a day you send (warning
   `scheduled-date-ignored`) and files the Lead on the first business day with room; the answer's `placement`
   says the day it chose. For your own Lead, then run **Capture connection evidence** for it, so Mosaico records
   connected, invite-pending or not-connected; never for a colleague's Lead (only her own run verifies it).
   Do not write any invitation draft, for your Lead or hers, and do not approve or send anything. If a draft write is
   ever answered with `sourcing-writes-no-drafts` (state blocked, recommended action `continue_with_next_lead`), that is
   expected and not a failure: nothing was saved, the Lead stays saved and placed; continue with the next Lead.
6. Reread `outreach_get_day` after every saved Lead. Mosaico preserves partial progress and
   owns the completion predicate; a valid partial save is not a completed run.
7. After sourcing, verify across every day in `workflowStatus.runDays`, not just one day:
   `workflowStatus.days` lists each day with its Leads and those still to verify. When the recommended action is
   `end_run` or `end_run_days_full`, nothing is left to source, verify or sort: end the run and report.
8. Report a shortfall only from Mosaico: `workflowStatus.shortfalls` (an Agent that ran out of free days),
   `workflowStatus.unavailableAgents` (an Agent Mosaico closed as unavailable), or a genuine Mosaico, authentication, LinkedIn or human-decision blocker. State the exact counts and
   the reason; never report the run as complete while a line is `open`.
9. End the run (see **End the run**), then finish with **Report a sourcing run**.

## Which Agent a Lead goes to

In a sourcing run Mosaico plans the Agents. `outreach_get_day` lists them in `workflowStatus.sourcingPlan`,
each line giving the owner, `agentId`, `agentName`, `leadsPerDay`, `leadsPerRun`, `acceptedThisRun`,
`remainingThisRun`, a status (`open`, `met`, `days-full` or `agent-unavailable`) and the days its Leads were filed on.
`workNow` (in `workflowStatus.workNow` and at the top of the `outreach_get_day` and `outreach_get_run` answers, and in a
refusal to end the run) names the Agent to source for now. Pass `workNow.agentId` as `agentId` on every
`outreach_save_lead` and pass no `ownerUserId`: Mosaico saves the Lead for the owner of that Agent, so a colleague's
Agent saves her Lead. `workflowStatus.agentId` and `nextAgentId` are a fallback only when `workNow` is not there. Never
choose an Agent yourself, and never send `targetCount` or `scheduledDate` for sourcing. If Mosaico blocks a save:

- `agent-required`: save again once with `workNow.agentId`.
- `agent-not-in-sourcing-plan`: that Agent is not planned for this owner. Save again once with the
  `agentId` in Mosaico's hint.
- `planned-agent-quota-met`: that Agent has delivered its Leads per run, or has no free day, while another
  Agent of the owner is still `open`. Save again once with the `agentId` Mosaico gives.
- `planned-agent-unavailable`: that Agent was switched off or deleted, or its owner left, and Mosaico closed its
  line. Nothing was saved. The answer carries `workNow`: source for the Agent it names, and never try the unavailable
  Agent again. If `workNow` is `none`, end the run with `complete`; Mosaico accepts it.
- `sourcing-quota-met`: this owner's target is met. Source for the next owner Mosaico names, if any.
- `sourcing-days-full`: that Agent has no free day in the next 10 business days. Do not search for more
  for it.
- `skipped` with `profile-exists-under-other-owner`: another owner already holds that person (even one they dropped).
  Nothing was saved. Continue with the next candidate; it is never a failure.

Nothing was saved by a blocked or skipped save, and none of these counts as a failure. Then read `workNow` again
(reread `outreach_get_day`) for the next step.

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
Since plugin 0.9.11 a Claude run can save a colleague's Lead as verified not connected by the colleague check
(note `colleague-check-negative-proven`), or save it with its connection unknown (note
`colleague-check-negative-unproven`). A sourcing run drafts neither: her own Sync data run writes her invitation.
Codex never records connection evidence for a colleague's Lead; only her own run verifies it, and her invitation is
not sent before that (`own-evidence-required`).

## Write missing invitation drafts

Writing an invitation draft is the Lead owner's work, done in the Sync data routine for the person's own Leads only.
A Source leads run never does it: Mosaico refuses a draft write inside a sourcing run with `sourcing-writes-no-drafts`.
A draft is only a draft: a person approves it in Outreach before it can be sent.

1. Read `outreach_get_day` for today with `intent: send_approved_invitations` and the `runId`.
   `workflowStatus.draftsToWrite` is the work: `count`, `entries` (each with `leadId`, `name`, `agentId`, `day` and
   `action`), `writtenBy`, `writableInThisRun`, `allowedActions`, `recommendedAction` and a `note`. It is always a list;
   `entries` is empty when nothing is missing. `outreach_get_follow_ups` carries the same list as a top-level
   `draftsToWrite`. Mosaico builds it from the owner's own Leads; never rebuild it from other reads or from memory.
2. Follow `draftsToWrite.recommendedAction`. Work the list only when it is `draft_invitation_messages`. When it is `none`,
   write nothing: `note` says why.
3. Call `outreach_get_agents` with no arguments. It returns the person's own Agents, each with its `messageInstructions`
   and `messagingChecklist`. For each entry use the Agent whose id is the entry's `agentId`. If the entry has no
   `agentId`, or that Agent is not returned, skip the Lead and list it with the reason.
4. For each entry, in the order given, write one draft with `outreach_record_message`: the entry's `leadId`, a new
   `messageId`, `kind` `invite`, `direction` `outbound`, `sentAt` null, a `body` written from that Agent's
   `messageInstructions` and the Lead's stored profile, a `checklistReview` with one pass or fail result for every
   enabled rule of the Agent's `messagingChecklist`, and the `runId`. Pass no `ownerUserId`. If Mosaico rejects the
   review, correct the body as its guidance says and send it once more. Write a draft for an entry on this list and for
   no other Lead.
5. Never approve, send or mark sent a draft you wrote. Mosaico's answer for one Lead is final: a `skipped` result, a
   `blocked` state or `draft-already-exists` is recorded and the next entry is worked; it is never a halt.
6. Reread `outreach_get_day` once every entry has been tried. A Lead Mosaico refused stays on the list; do not try it
   again in this run. Stop when every entry has been tried or Mosaico reports a genuine blocker.
7. In the final report give the drafts written, each with its Lead, and the Leads skipped, each with its reason.

## Report a sourcing run

Report in plain words, using Mosaico's counts, not memory. The first line is "Mosaico environment: <environmentName>" from the start answer. The second is "Mosaico lane: own", "Mosaico lane: colleagues" or "Mosaico lane: whole plan", from the answer's `sourcingScope` (`all` is the whole plan). If that answer carried `previous-run-abandoned`, the next line is "Previous run failed: stopped with N open" (or one line saying the previous run finished but was not ended, for `previous-run-finished-not-ended`). Then:

- the `runOutcome` Mosaico gave when you ended the run;
- per Agent, from `workflowStatus.sourcingPlan` (or `sourcingProgress.lines` from `outreach_get_run`): name the
  owner and the Agent, and give the target (Leads per run), the Leads accepted, the Leads remaining and the
  status (`open`, `met` or `days-full`);
- per day, from `workflowStatus.runDays`: how many Leads were filed on each day;
- the shortfalls in `workflowStatus.shortfalls`: each Agent that ran out of free days and what it was still owed;
- the Agents Mosaico closed as unavailable (`workflowStatus.unavailableAgents`, or `sourcingProgress.unavailableAgents` from
  `outreach_get_run`, or `unavailableAgents` in the end answer): each with its reason (`agent-off`, `agent-deleted` or
  `owner-inactive`) and what it was still owed;
- "Candidates skipped as held by another owner: N", N from the `count` of `workflowStatus.collisions` (or of the `collisions`
  `outreach_get_run` returns). Those skips are never failures;
- the candidates skipped as already connected to that owner ("skipped as already connected to <owner>: N", from
  `workflowStatus.colleagueSkips`; its entries name the owner). Those skips are never failures;
- no drafts: a Source leads run writes none, and a draft write Mosaico refused with `sourcing-writes-no-drafts` is
  expected, never reported as a failure or a blocker.

A run whose `runOutcome` is not complete or blocked, or that Mosaico closed with a line open, is a failed run: report it as "run failed: stopped with N open". A run that saved nothing because of a blocker other than `sourcing-days-full` is a failed run: report it as
failed with Mosaico's code and message (for example `sourcing_plan_empty` or the blocker that stopped it),
including a run Mosaico refused at the start. Never report such a run as successful, and never describe a
partly filled plan as complete. A run that ends `sourcing-days-full` with nothing saved (refused at the start,
or every Agent without a free day) is not a failure: report "Every Agent is full for the next 10 business days; nothing to source." When Mosaico answers
`sourcing_plan_empty`, the report says: "Set Leads per day and Leads per run on an Agent in Outreach (Agent tab), then rerun."

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

Sourcing is never part of this: a Source leads run is its own run and its own schedule.

1. Complete **Write missing invitation drafts** first.
2. Reread the current Mosaico state for those dates.
3. Complete **Send approved invitations** only for messages that were already human-approved. Never
   approve a newly created draft automatically.

For every scope, Mosaico is the workflow authority for stored state, target completion, ownership,
validation, allowed actions and recovery. Stop only when the selected scope is complete, Mosaico
reports a genuine blocker, or a human decision is required. Mosaico decides which member a record belongs to from the run; do not try to work that out yourself.
Only Owners and Admins can use Outreach.

## End the run

End every run with `outreach_end_run` and the honest reason. Mosaico decides how the run ended, not you:

- `complete`: Mosaico says the plan is done: every planned Agent delivered its Leads per run, ran out of free days, or became unavailable (for sourcing, `sourcing-quota-met`, `sourcing-days-full` or `sourcing-agent-unavailable`; a sourcing run with nothing left to source, verify or sort has the recommended action `end_run` or `end_run_days_full`). Always call it on a finished run, even when nothing is left to do: a run you leave unended keeps the account busy for 30 minutes.
- `blocked`: a genuine blocker stops the run. Give `blockerCode` (`linkedin_account_changed` or `linkedin_identity_invalid`, given by Mosaico in this run, or `INTERNAL_SERVER_ERROR` when Mosaico's last three calls all failed) or `linkedInIssue` (`warning`, `captcha` or `restricted`) with a `note`.

These are the only two reasons. Never ask for `abandoned`; it no longer exists. If you ask to end a sourcing run while a line is open and nothing proves a blocker, Mosaico refuses: the answer is blocked with `sourcing-run-open`, the run stays open and writable, and it carries `workNow` and the one allowed action `continue_sourcing`. Do not retry the end and do not argue; read `workNow` and keep sourcing.
If a write answers `run_ended` (recommended action `report_run_closed`), Mosaico closed the run after 30 minutes without a call: stop, report "Mosaico closed this run after 30 minutes without a call", and do not start another run. A second `outreach_end_run` on a closed run answers `report_run_closed`.
Read the answer's `runOutcome` and report it. When it names `unavailableAgents`, say so.

## Source leads routine

This is the Source leads flow of Mosaico Outreach. It only finds Leads, saves them and lets Mosaico place them on days, then ends the run. It never writes invitation drafts, approves, sends or messages; the Sync data schedule, installed from Claude, does that.

The schedule's text carries only the person's standing answers: the timezone and, when it names a lane, the line `sourcing scope: own` or `sourcing scope: colleagues`; the action is "source Leads only". Neither the days nor the numbers are in the schedule: Mosaico files each Lead on a day, and Leads per day, Leads per run and who sources them are set on each Agent in Outreach (Agent tab), where Mosaico holds them. Take them from there; the schedule supplies the answers to this skill's opening questions, so do not ask them, do not show a menu, and do not ask which days or which scope. If a standing answer is missing, stop and report which one.

Resolve the current business date and time in the timezone from the schedule's standing answers. The person has supplied standing answers for this recurring automation: proceed without asking which days or which scope.

Use the authenticated LinkedIn browser. Never read, copy, export or reconstruct a LinkedIn cookie, token or session; never write a LinkedIn script of your own; never read a Connect, Message or Pending button as a connection state; never set a connection state yourself.

Step 1. Open LinkedIn's Me page once and read the profile URL of the signed-in account. Report it as observedLinkedInProfile to outreach_start_run. Send no quota and no colleague: Mosaico derives the quota from the sourcing plan on the Agents (the sum of the Leads per run of each owner's Agents). If the standing answers hold the line `sourcing scope: own` or `sourcing scope: colleagues`, pass exactly that word as sourcingScope on outreach_start_run; if there is no such line, send nothing; never choose, change or invent a scope. Start the sourcing run once (Step 2 and Step 3 use the same run), never start a second sourcing run in this session, and pass its runId on every read and write. If Mosaico blocks the start, stop and report the blocker; do not work around it. Read environmentName in the start answer. If it is not production, stop and report it; do not work in that environment. The report's first line is "Mosaico environment: production" (the name the answer gave); the second is "Mosaico lane: own", "Mosaico lane: colleagues" or "Mosaico lane: whole plan", from the answer's top-level sourcingScope, which must be the word you sent (all when you sent none): if it differs, say so in the report. If the answer carries the note previous-run-abandoned, your last Source leads run of this lane was left with a line open: say so right after the lane line, as "Previous run failed: stopped with N open" (N from previousRun.openLines), then go on; the note previous-run-finished-not-ended means that run had finished but was never ended: say so in one line, then go on. If it answers sourcing_plan_empty (recommended action set_agent_sourcing_numbers_in_outreach), stop: quote Mosaico's code and message verbatim, then end the report with this sentence: "Set Leads per day and Leads per run on an Agent in Outreach (Agent tab), then rerun." Do not ask the person for numbers. A sourcing_plan_empty stop is loud: a failed run. If it answers sourcing-days-full (recommended action wait_for_free_days), no run was issued because every planned Agent of this lane is full for the next 10 business days: this is not a failure; stop and report "Every Agent is full for the next 10 business days; nothing to source." If it answers sourcing-run-busy (recommended action wait_for_current_run), another Source leads run of this account is working, no run was issued and there is no runId: this is not a failure; stop, do not start again, and report "Another Source leads run is working on this account; nothing started." If it answers sourcing-scope-empty (recommended action nothing_to_source), no planned Agent is in this lane: this is not a failure; stop and report "Nothing to source for the <own|colleagues> Agents." If it answers sourcing_scope_invalid (recommended action correct_sourcing_scope), stop: quote Mosaico's code and message verbatim and report a failed run; do not retry with another scope. Otherwise the run carries run.quota and run.sourcingPlan.

Step 2. Run this skill with the selected action "source Leads only". Before you source, call outreach_get_agents with the runId. Never pass ownerUserId with it. It returns every Agent in this run's plan, yours and your colleagues', each with its own search and message instructions, checklist and attachments: work from every returned Agent's own instructions, including colleagues' Agents, for the Leads you save under it. Mosaico files every Lead on a day; you never choose one. Call outreach_get_day without day. Never send targetCount for sourcing. Never send scheduledDate. Each Lead is saved directly under the target owner by the run; there is no transfer step. Follow workflowStatus.recommendedAction and reread after every saved Lead. Work workflowStatus.workNow (also at the top of the answer) and read it again at every decision point: while it says state work, search for the Agent it names, inside workNow.brief, that Agent's own search instructions word for word; a supply note in the brief is for the final report, never a reason to stop. Keep sourcing while any line of workflowStatus.sourcingPlan is open; the stop is Mosaico's completion (Step 4), never your own judgement. While searching, call outreach_get_run at least every 10 minutes, or after every 10 candidates, even when nothing was saved: Mosaico closes a run that makes no Mosaico call for 30 minutes. Pass workNow.agentId on every outreach_save_lead and no ownerUserId, as this skill's "Which Agent a Lead goes to" says; if Mosaico blocks a save with agent-required, agent-not-in-sourcing-plan or planned-agent-quota-met, save again once with the agentId it gives; planned-agent-unavailable saves nothing and carries workNow: source for the Agent it names, and never try the unavailable one again; sourcing-quota-met and sourcing-days-full save nothing and are not failures; a candidate another owner already holds is skipped (profile-exists-under-other-owner, heldByOtherOwner), never a failure: continue with the next candidate; then read workNow again. This package cannot run the colleague-connection check (it ships no browser scripts): when Mosaico blocks a save for a colleague with colleague-check-required, do not retry or work around it; list the candidate as skipped and say that Leads for that colleague need a Claude run.

Step 3. Run this skill again with the same run and the same action "source Leads only", across every day in workflowStatus.runDays, not just one. This package cannot capture connection evidence: leave a Lead Mosaico lists as connection unverified unverified and list it as skipped. This run writes no invitation draft, for your Leads or a colleague's: the Lead owner's Sync data run writes them from the draftsToWrite list Mosaico gives it, so do not attempt one. If a draft write is ever answered with sourcing-writes-no-drafts (blocked, recommended action continue_with_next_lead), that is expected and not a failure: nothing was saved, the Lead stays saved and placed; continue. Never approve or send an invitation.

Step 4. Stop only when Mosaico says the run is complete (workflowStatus.completion is complete with reason sourcing-quota-met, sourcing-days-full or sourcing-agent-unavailable) and nothing is left to verify or sort, or when Mosaico recommends end_run or end_run_days_full. Never stop while any line of workflowStatus.sourcingPlan is open, and never because you think enough was found. A skipped candidate, a refused write for one Lead, or sourcing-quota-met or sourcing-days-full on a save is not a reason to stop. There is no search limit: do as many searches as it takes, and "I could not find candidates", "few results", "weak results", "slow" and "enough found" are never a reason to stop. When results are few, widen inside the Agent's brief (more keywords, more results pages, other filters, other regions the brief allows, Premium Daily Prospects) and keep searching; never widen past the brief's qualification rules. If an Agent's brief says to report a lead supply constraint, note it for the final report and keep searching inside the brief; it never means stop. A run keeps searching until Mosaico says the numbers are met: a candidate you reject, a person another owner already holds and a person already connected to the colleague are never failures, and Mosaico counts none in a new run. A run that ends with any line still open is a failed run: report it as "run failed: stopped with N open". Then end the run with outreach_end_run and the honest reason, and let Mosaico decide the outcome: always call it on a finished run, with reason complete when Mosaico says the plan is done (every Agent delivered, ran out of free days, or became unavailable); reason blocked, with the blockerCode Mosaico gave in this run (linkedin_account_changed, linkedin_identity_invalid, or INTERNAL_SERVER_ERROR after Mosaico's last three calls failed) or the linkedInIssue (warning, captcha or restricted) and a note, when a genuine blocker stops it. These are the only two reasons; never ask for abandoned, it no longer exists. If Mosaico answers sourcing-run-open, the end was refused and the run stays open: do not retry the end and do not argue; read workNow and keep sourcing. If a write answers run_ended (recommended action report_run_closed), Mosaico closed the run after 30 minutes without a call: stop, report "Mosaico closed this run after 30 minutes without a call", and do not start another run.

Step 5. Start the report with the line "Mosaico environment: <environmentName>", then the line "Mosaico lane: own", "Mosaico lane: colleagues" or "Mosaico lane: whole plan", and, when the start answer carried previous-run-abandoned, the line "Previous run failed: stopped with N open". Report separately, using Mosaico's counts, not memory: the runOutcome Mosaico gave when you ended the run; for each owner and each of their Agents in workflowStatus.sourcingPlan, the target (Leads per run), the Leads accepted, the Leads remaining and the status (name the owner and the Agent); for each day in workflowStatus.runDays, how many Leads were filed on it; the shortfalls in workflowStatus.shortfalls; the Agents Mosaico closed as unavailable (unavailableAgents, with each reason: agent-off, agent-deleted or owner-inactive); "Candidates skipped as held by another owner: N" (N from the count of workflowStatus.collisions); candidates skipped as already connected to each owner (from workflowStatus.colleagueSkips), candidates skipped with reasons, Leads left unverified, blockers. A run whose runOutcome is not complete or blocked, or that Mosaico closed with a line open, is a failed run: report it as "run failed: stopped with N open". A run that saved nothing because of a blocker other than days-full is a failed run: report it as failed with Mosaico's code (for example sourcing_plan_empty) and message, also when Mosaico refused the start, and never as successful. A run that ends sourcing-days-full with nothing saved is not a failure: report "Every Agent is full for the next 10 business days; nothing to source." No drafts are written in this run, and a draft write Mosaico refused with sourcing-writes-no-drafts is not reported as a failure. Preserve Mosaico as workflow authority and never modify another owner's records.

Guards: pacing between page loads and run expiry are enforced by Mosaico; a LinkedIn warning or captcha stops the run, which then reports.
