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
Sourcing takes no day from the person: Mosaico files each Lead on the first business day with room, so the days question applies to sending and inspection only.

## Start the run

1. Open LinkedIn's Me page in the authenticated browser and read the profile URL of the signed-in
   account. Report what you see; do not decide or correct it.
   Or run the approved whoami script instead: send the browser pane's `javascript_tool` the one line
   `// mosaico run linkedin-whoami.js` as the whole script. The plugin's gate inserts the approved script, so
   never retype it. Pass its output exactly as returned (every field, `integrity` included) as
   `identityEvidence` to `outreach_start_run`. Mosaico compares the identifiers from the record. If the script
   is unavailable, read the Me page as above. Fallback, only when the gate refuses the directive: print the
   approved script without changing it,

   ```bash
   cat "${CLAUDE_PLUGIN_ROOT:-$(dirname "$(dirname "$(find ~/.claude/plugins -path '*/mosaico-claude/browser/linkedin-whoami.js' -print -quit)")")}/browser/linkedin-whoami.js"
   ```

   and run it word for word with the browser pane's `javascript_tool`.
2. Call `outreach_start_run` with that URL as `observedLinkedInProfile` and the intent: `source_invitation_leads` for sourcing, `send_approved_invitations` for sending. When doing both, start a separate run for each scope.
   A sourcing start sends no quota and no colleague. Mosaico holds the sourcing plan on the Agents: each
   Agent has Leads per day (the most it may hold on one day), Leads per run (what one run must deliver) and
   Sourced by, set by a person in Outreach (Agent tab). Mosaico takes every active Agent that has both
   numbers and that the person sources (their own, and a colleague's that names them in Sourced by) and
   returns as `run.quota` the sum of their Leads per run, with the plan in `run.sourcingPlan`. Every run
   delivers its own Leads per run; nothing is taken off for earlier runs. Mosaico, not you, files each Lead on
   a day. Never send `quota` or `colleagueOwnerUserId`, and never ask the person for numbers. Read the outcome:
   - A normal run, with `run.quota` and `run.sourcingPlan`: go on.
   - Every start answer names the Mosaico environment in `environmentName`. If it is not `production`, stop and report it; do not work in that environment. The report's first line is "Mosaico environment: production" (the name the answer gave).
   - If the answer carries the note `previous-run-abandoned` (with `previousRun`), your last Source leads run was left with a line open. Say so right after the environment line, as "Previous run failed: stopped with N open" (N from `previousRun.openLines`), then go on.
   - Blocked with `sourcing_plan_empty` (recommended action `set_agent_sourcing_numbers_in_outreach`): no Agent
     has both Leads per day and Leads per run for this person. Stop. A scheduled run quotes Mosaico's code and
     message verbatim and ends its report with this sentence: "Set Leads per day and Leads per run on an Agent in Outreach (Agent tab), then rerun."
   - Blocked with `sourcing-days-full` (recommended action `wait_for_free_days`): every planned Agent is full
     for the next 10 business days and no run was issued. This is not a failure. Stop and report: "Every Agent is full for the next 10 business days; nothing to source."
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
   Or run the whoami script again and pass its output exactly as returned as `identityEvidence` on the write.
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

## Script output goes to Mosaico exactly as returned

Every approved script returns an `integrity` field, `{ algorithm: "fnv1a32", digest }`, computed in the
page over everything else it returns. Wherever a script's output goes to Mosaico (`identityEvidence` from
the whoami script, the connection evidence, `sentInvitationEvidence`, `colleagueConnectionEvidence`), pass it exactly as returned: every
field, `integrity` included, never retyped, trimmed, reformatted, translated or "fixed". Mosaico recomputes
the digest and refuses an altered copy with `evidence-altered`: nothing is stored, and the recommended
action is `recapture`. Then run the approved script again and pass the new output unchanged. Never edit
the copy to make it pass.

## Source Leads and prepare drafts

1. Call `outreach_get_agents` with the `runId`. Never pass `ownerUserId` with it. It returns every Agent in this run's plan,
   yours and your colleagues', each with its own search and message instructions, checklist and attachments: work from every
   returned Agent's own instructions, including colleagues' Agents, for the Leads you save under it. Then call
   `outreach_get_day` with `intent: source_invitation_leads` and the `runId`. Leave `day` out: for a sourcing run Mosaico reads every day the run filed Leads on. Never send
   `targetCount` for sourcing: Mosaico takes the target from the run's sourcing plan.
2. Follow `workflowStatus.recommendedAction`. Use its prepared count, remaining count, blockers and
   completion result; do not reconstruct them from separate records or conversation memory. When the
   recommended action is `verify_connection`, Mosaico lists the Leads whose connection is unknown or
   unverified in `workflowStatus.unverifiedLeads`, each with its profile URL: for each one run
   **Capture connection evidence**, then reread `outreach_get_day`. Never guess a connection and never
   skip to drafting for a listed Lead. A colleague's Lead is never in that list for your run: only her own run
   verifies it.
3. Mosaico decides when sourcing ends, never your own judgement. While any line in
   `workflowStatus.sourcingPlan` has status `open`, keep sourcing: search, broaden suitable searches, check
   profiles and save qualified Leads with their profile details, following `nextOwnerUserId` and
   `nextAgentId`. Sourcing is over only when `workflowStatus.completion` says the run is complete with reason
   `sourcing-quota-met` (every Agent delivered its Leads per run) or `sourcing-days-full` (an Agent ran out
   of free days first: do not search for more to fill its shortfall).
4. The stop rules, in Mosaico's words. Loading a few Leads is not completion; if a line is still `open`, continue.
   - Stop only when Mosaico says the run is complete (`workflowStatus.completion` is complete with reason sourcing-quota-met or sourcing-days-full) and nothing is left to verify or draft, when Mosaico recommends end_run_days_full, or when Mosaico reports stop_run after the tenth failure (then write the sourcing report Mosaico asks for).
   - There is no search limit: do as many searches as it takes, and "I could not find candidates", "few results", "weak results", "slow" and "enough found" are never a reason to stop.
   - When results are few, widen inside the Agent's brief (more keywords, more results pages, other filters, other regions the brief allows, Premium Daily Prospects) and keep searching; never widen past the brief's qualification rules.
   - If an Agent's brief says to report a lead supply constraint, note it for the final report and keep searching inside the brief; it never means stop.
   - A run that ends with any line still open and no stop_run is a failed run: report it as "run failed: stopped with N open".
5. Save each qualified Lead through `outreach_save_lead` with the `agentId` the day read gave for that owner (see
   **Which Agent a Lead goes to**), which takes no connection state: the new Lead
   starts unknown. Never send `scheduledDate`: Mosaico ignores a day you send (warning
   `scheduled-date-ignored`) and files the Lead on the first business day with room; the answer's `placement`
   says the day it chose. For a candidate you save for a colleague, first run **Check a candidate against the
   colleague** when it applies, then follow **Draft a colleague's invitation**: never run **Capture connection
   evidence** for a colleague's Lead. For your own Lead run **Capture connection evidence** for the saved Lead, so
   Mosaico records connected, invite-pending or not-connected before any draft is written. Write the missing
   outbound Invite draft only for a Lead Mosaico lists as verified, or for a colleague's Lead saved with the note
   `colleague-check-negative-proven`. Do not approve or send any invitation in this scope.
6. Reread `outreach_get_day` after every saved Lead and draft. Mosaico preserves partial progress and
   owns the completion predicate; a valid partial save is not a completed run.
7. After sourcing, verify and draft across every day in `workflowStatus.runDays`, not just one day:
   `workflowStatus.days` lists each day with its Leads, those still to verify and those without a draft.
   When the recommended action is `end_run_days_full`, nothing is left to verify, sort or draft: end the
   run and report.
8. Report a shortfall only from Mosaico: `workflowStatus.shortfalls` (an Agent that ran out of free days),
   or a genuine Mosaico, authentication, LinkedIn or human-decision blocker. State the exact counts and
   the reason; never report the run as complete while a line is `open`.
9. End the run (see **End the run**), then finish with **Report a sourcing run**.

## Source Leads only

Use this scope when the Leads go to the owners in the run's sourcing plan (the person's own Agents, and a
colleague's Agent that names the person in Sourced by) before any draft is written, so that each owner's
drafts are later written under their own Agent and voice.

1. Same as "Source Leads and prepare drafts", but the target is the run's sourcing plan: each Agent's Leads
   per run, not the 20 of a prepared day. Mosaico keeps the plan and reports what remains for each Agent
   (`remainingThisRun`); use its counts, and `workflowStatus.counts.readyLeads` for the ready Leads, not
   the prepared count.
2. Save each qualified Lead with its profile details and the planned `agentId` through `outreach_save_lead`, which takes no
   connection state (for a candidate you save for a colleague, first run **Check a candidate against the
   colleague** when it applies, and never run **Capture connection evidence** for her Lead), then, for your own
   Lead, run **Capture connection evidence** for it. Do not write any invitation draft in this scope (a colleague's
   proven Lead is drafted in **Source Leads and prepare drafts**), and do not approve or send anything.
3. Reread `outreach_get_day` after every saved Lead and continue until Mosaico says the run is complete
   (reason `sourcing-quota-met` or `sourcing-days-full`) or returns a blocker, `human_decision_required`
   or `stop_run`.
4. End the run (see **End the run**), then finish with **Report a sourcing run**. A run with a line still `open` is not complete.

## Which Agent a Lead goes to

In a sourcing run Mosaico plans the Agents. `outreach_get_day` lists them in `workflowStatus.sourcingPlan`,
each line giving the owner, `agentId`, `agentName`, `leadsPerDay`, `leadsPerRun`, `acceptedThisRun`,
`remainingThisRun`, a status (`open`, `met` or `days-full`) and the days its Leads were filed on.
`workflowStatus.agentId` is the Agent to pass as `agentId` on `outreach_save_lead` for the owner of that
read, and `workflowStatus.nextAgentId` is the one for the next owner (`nextOwnerUserId`) who still has an
`open` Agent. Pass the `agentId` the read gave for that owner on every save. Never choose an Agent yourself,
and never send `targetCount` or `scheduledDate` for sourcing. If Mosaico blocks a save:

- `agent-required`: save again once with the `agentId` the day read gave for that owner.
- `agent-not-in-sourcing-plan`: that Agent is not planned for this owner. Save again once with the
  `agentId` in Mosaico's hint.
- `planned-agent-quota-met`: that Agent has delivered its Leads per run, or has no free day, while another
  Agent of the owner is still `open`. Save again once with the `agentId` Mosaico gives.
- `sourcing-quota-met`: this owner's target is met. Source for the next owner Mosaico names, if any.
- `sourcing-days-full`: that Agent has no free day in the next 10 business days. Do not search for more
  for it.

Nothing was saved by a blocked save, and none of these counts as a failure. Then reread `outreach_get_day`
for the next step.

## Check a candidate against the colleague

This applies in **Source Leads and prepare drafts** and **Source Leads only**, to a candidate you are about to
save for a colleague (an owner other than the run owner). Whether the candidate is already connected to that
colleague is a fact in LinkedIn's Sales Navigator, not something to judge. This procedure carries it to
Mosaico unchanged; Mosaico reads it and decides. Never decide it from the screen, from a result list or from
a name, and never use it as a connection state: it sets none.

Mosaico tells you when it is needed. When `outreach_get_day` (with `intent: source_invitation_leads` and the
`runId`) lists the colleague in `workflowStatus.colleagueChecks` with `allowed: true`, run the check for every
candidate you will save for that colleague, once, right before `outreach_save_lead`. When there is no such
entry, or `allowed` is false (the entry says why), save as usual with no evidence. A Lead for the run owner
never needs it. Mosaico supplies the colleague's identifier in that entry; you never choose or retype it.

1. Take the candidate's public identifier: the part of the profile URL you are about to save after `/in/`, with
   no trailing slash or query, or the opaque id when that is what the URL holds (it starts with `ACoAA`). Use it as it is.
2. The entry's `directive` is the line to run, with `<candidate>` left for you to fill. Replace only
   `<candidate>` with that identifier; leave the colleague's identifier exactly as Mosaico wrote it. Send the
   result as the whole script with the browser pane's `javascript_tool` from a Sales Navigator page (any
   `https://www.linkedin.com/sales/` page; open `https://www.linkedin.com/sales/home` first when the pane is
   elsewhere): `// mosaico run linkedin-salesnav-colleague-connection.js PUBLIC_IDENTIFIER=<candidate> COLLEAGUE_IDENTIFIER=<the colleague's identifier from Mosaico>`.
   The plugin's gate inserts the approved script; never print, retype, paraphrase, reorder, shorten or
   extend it. It sends LinkedIn's own session and CSRF material to LinkedIn only, never returns it, and
   returns only ids: no name, headline or result row leaves the page.
   Fallback, only when the gate refuses the directive: print the approved script without changing it,

   ```bash
   cat "${CLAUDE_PLUGIN_ROOT:-$(dirname "$(dirname "$(find ~/.claude/plugins -path '*/mosaico-claude/browser/linkedin-salesnav-colleague-connection.js' -print -quit)")")}/browser/linkedin-salesnav-colleague-connection.js"
   ```

   then run the printed script with the browser pane's `javascript_tool`, changing only the values on its
   first two lines (the candidate's identifier on the first, the colleague's on the second), in quotes. The
   gate refuses anything else.
3. Pass the script's whole output exactly as returned (every field, `integrity` included) as
   `colleagueConnectionEvidence` on the `outreach_save_lead` call for this candidate and this colleague, with
   everything else you pass for a save. Do this whatever its `state` is (`ok`, `colleague-not-resolved`,
   `candidate-not-resolved` or `error`), and also when `signedIn` is false: Mosaico reads it and decides.
   Never trim, retype or "fix" it, and never leave a field out. Since plugin 0.9.11 the output also carries the
   proof fields `complete`, `controlTotal`, `visibility` and `unreadableRows` inside the sealed object: pass them
   exactly as returned too, and send a `null` as `null` rather than leaving the field out.
4. Mosaico's answer is final:
   - `skipped` with code `already-connected-to-colleague` (recommended action `continue_sourcing`): the
     candidate is already connected to the colleague. Nothing was saved. This is not a failure and does not
     count toward the target. Source the next candidate and keep going.
   - `blocked` with code `colleague-check-required` (recommended action `run_colleague_check`): nothing was
     saved and the check was missing or unusable. Its `reason` says which: `evidence-missing`,
     `evidence-altered`, `colleague-evidence-malformed`, `colleague-evidence-inconsistent`,
     `observation-stale` (older than ten minutes: run it again just before the save),
     `observation-time-invalid`, `colleague-mismatch` (it was run for another colleague: use the identifier in
     Mosaico's directive), `candidate-mismatch` (it was run for another person: run it for this candidate) or
     `candidate-is-colleague`. Run the script again with the directive Mosaico returned and send the new output
     unchanged; never retype or edit the old one. Do this once per candidate. If Mosaico still blocks it, list
     the candidate as skipped with Mosaico's code and reason and continue. For `candidate-is-colleague`
     running again cannot help: the candidate is the colleague herself, so do not save it, list it as skipped
     and continue.
   - Saved, with the note `colleague-check-negative-proven`: the candidate was not found in the colleague's
     connections and the check showed that the search could have found them (every result page read, her
     connections visible to the account that searched, no result row unread). Mosaico saved the Lead as verified
     not connected by the colleague check, and the answer says `awaitingOwnerCheck` true. Draft her invitation at
     once: see **Draft a colleague's invitation**. Nothing is sent until her own run records her own connection
     evidence.
   - Saved, with the note `colleague-check-negative-unproven`: the candidate was not found in the colleague's
     connections, or could not be looked up, and the check could not show that the search would have found them
     (the note says why, for example a script older than 0.9.11 or an unread page). That is **not** proof that they are
     not connected (she may hide her connections): the Lead is saved with its connection unknown, so never write "not
     connected" about it. Do not draft it (Mosaico refuses with `lead-awaiting-owner-check`) and do not verify it:
     it stays undrafted and her own Sync run checks it first. Continue sourcing.
   - Saved, with a note: `colleague-check-unavailable` means the check cannot work for this colleague (the page was signed out,
     LinkedIn refused it, or she could not be found in Sales Navigator): the candidate was saved without it, and
     Mosaico asks for no more checks for that colleague in this run, so save her next candidates without
     evidence. `colleague-check-cap-reached` means this run has used all its checks (30 candidates, or three times the Leads per run of the colleagues' Agents when that is more): save the rest without evidence.
5. A colleague's Lead never goes through **Capture connection evidence**, and the colleague check is never
   passed to `outreach_record_connection_evidence`: only her own run verifies her Lead, from her own LinkedIn
   account. Mosaico answers `evidence-owner-mismatch` to any evidence recorded for it and writes nothing. The
   save answer never recommends `verify_connection` for her Lead; do not add that step yourself.

When the script file is missing or the gate refuses it, do not work around it: do not save the candidate for
the colleague, list it as skipped with the reason, and continue.

## Draft a colleague's invitation

This applies to a Lead you saved for a colleague with the note `colleague-check-negative-proven`, in **Source
Leads and prepare drafts** (and in the **Source leads routine**'s drafting step). Her own Agent's instructions,
from `outreach_get_agents`, govern the invitation text.

1. Write the invitation draft in the same run: `outreach_record_message` as an outbound `invite` draft with
   `sentAt` null, the Lead's `leadId`, the `runId`, the review of the body against her Agent's rules, and
   no `ownerUserId` on the call: Mosaico finds her from the Leads this run accepted. Never approve or send it.
2. To see which of her Leads still need a draft, read her day: `outreach_get_day` with `intent: source_invitation_leads`,
   the `runId`, no `day`, and her member id (from her line in `workflowStatus.sourcingPlan`)
   as `ownerUserId`. This is a read only. Never pass `ownerUserId` on a write.
   Its `workflowStatus.days` lists her Leads without a draft, and `awaitingOwnerCheck` lists her Leads that wait
   for her own check.
3. A Lead saved with `colleague-check-negative-unproven` stays undrafted: Mosaico refuses its draft with
   `lead-awaiting-owner-check`. A sourcing run writes only the invitation draft for her Lead; any other draft
   for her is refused with `colleague-draft-invite-only`. Take Mosaico's answer as final, record it and continue.
4. Her invitation is sent only by her own Sync run, after it records her own connection evidence for the Lead.
   Mosaico does not offer it for sending before that (`own-evidence-required`).

## Report a sourcing run

Report in plain words, using Mosaico's counts, not memory. The first line is "Mosaico environment: <environmentName>" from the start answer; if that answer carried `previous-run-abandoned`, the next line is "Previous run failed: stopped with N open". Then:

- the `runOutcome` Mosaico gave when you ended the run;
- per Agent, from `workflowStatus.sourcingPlan` (or `sourcingProgress.lines` from `outreach_get_run`): name the
  owner and the Agent, and give the target (Leads per run), the Leads accepted, the Leads remaining and the
  status (`open`, `met` or `days-full`);
- per day, from `workflowStatus.runDays`: how many Leads were filed on each day;
- the shortfalls in `workflowStatus.shortfalls`: each Agent that ran out of free days and what it was still owed;
- the candidates skipped as already connected to that owner ("skipped as already connected to <owner>: N", from
  `workflowStatus.colleagueSkips` or the `colleagueSkips` Mosaico returns with `outreach_get_run`; its entries
  name the owner). Those skips are never failures;
- from Mosaico's notes, any colleague whose check was unavailable and why;
- the Leads saved for each colleague, split into "verified not connected by colleague check (proven)" (note
  `colleague-check-negative-proven`) and "unproven, awaiting her Sync" (note `colleague-check-negative-unproven`,
  and any Lead awaiting her own check on her day read): a Lead saved after "not found" without the proof has its
  connection unknown, not "not connected";
- the invitation drafts written for each colleague.

A run Mosaico records as abandoned (`runOutcome` abandoned) is a failed run: report it as "run failed: stopped with N open". A run that saved nothing because of a blocker other than `sourcing-days-full` is a failed run: report it as
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
   `invite-pending`. An invitation for a Lead whose only not-connected evidence is a colleague check (another
   member's sourcing run saved it as not connected) is held back: Mosaico lists it in `workflowStatus.heldInvitations` with
   `own-evidence-required`, not for sending, and lists the Lead first in `workflowStatus.unverifiedLeads` with the
   reason `colleague-verified-needs-own-check`. Verify it from your own pane like any unverified Lead, then reread.
   If `outreach_mark_message_sent` answers `own-evidence-required`, run **Capture connection evidence** for that
   Lead, reread the day, and continue as Mosaico then says.
4. Send through the authenticated LinkedIn browser: click Connect and type the approved note. Do not
   judge from the screen whether it worked; LinkedIn's data says so, in the next step.
5. **Confirm the send from data.** LinkedIn's profile data cannot show a pending invitation; only its
   Sent invitations list can. Straight away, run the approved sent-invitations script with the Lead's
   script identifier after the send and pass its output exactly as returned as `sentInvitationEvidence`
   (**Capture the sent invitation**) to `outreach_mark_message_sent`, with the exact Lead and Message identities, the exact
   send time when LinkedIn exposes it, otherwise null, fresh `identityEvidence` (run the whoami script
   again) and the `runId`. Mosaico reads the capture: it accepts the mark only when the Lead is on the
   list with a send time after your check before the send, and records the send time as the proof. Report
   its answer in plain words. Never call `outreach_record_connection_evidence` for this capture. Do not
   pass `sendEvidence`: it is the connection-evidence script's output and proves only that the person
   accepted at once, so for anything else Mosaico answers `send-evidence-cannot-prove` and writes nothing.
6. If Mosaico answers `send-not-confirmed`, LinkedIn's Sent invitations list does not show the invitation:
   it did not go out. Do not retype the note and do not mark it sent. Retry the send once, run the script
   again and pass its output again as `sentInvitationEvidence`. If Mosaico answers `send-not-confirmed`
   again, call `outreach_record_delivery_block` with `reason: cannot-message` and continue with the next
   invitation. For `send-evidence-stale`, `send-evidence-before-send` or `send-evidence-malformed`, the
   capture was unusable: run the script again once and pass it again; if it is still refused, leave the
   invitation Approved, list it as skipped with the code and continue (the next run checks the Lead
   before sending, so an invitation that did go out is never sent twice). For `send-evidence-lead-mismatch`,
   the capture was for another profile: run the script for this Lead's own script identifier. For
   `send-evidence-cannot-prove`, run the sent-invitations script and pass its output as
   `sentInvitationEvidence`.
7. Never mark an invitation sent from the screen alone. Only when the script cannot run (the script file
   is missing, the gate refuses it, or LinkedIn stops answering it), and the Connect click and note
   visibly went through, call `outreach_mark_message_sent` without `sentInvitationEvidence`: Mosaico
   records it as a reading of the screen and answers `send-proof-missing`. Say so in the final report,
   with each Lead.
8. Reread the same day after each send, capture or recorded outcome and continue until Mosaico reports
   completion or a genuine blocker (Mosaico, sign-in or LinkedIn failure). One Lead that cannot be
   invited never stops the run.
9. In the final report list recorded outcomes and Leads left unverified separately from sends and
   blockers, each with its Lead and reason, and count the sends confirmed from data separately from
   any marked by screen.

## Capture connection evidence

Whether you are connected to a Lead is a fact in LinkedIn's own data, not on the page's buttons. This
procedure carries that data to Mosaico unchanged; Mosaico reads it and decides. Never read a Message,
Connect or Pending button as a connection state, never choose a field by what it means and never decide
the relationship yourself.

The capture is the plugin's connection-evidence capability: one approved script, shipped at
`browser/linkedin-connection-evidence.js` inside the installed plugin, run through a one-line run directive in the signed-in
LinkedIn page by the built-in browser pane. It sends LinkedIn's own session and CSRF material to LinkedIn
only and never returns it; it returns only LinkedIn's relationship fields for the one profile, with names
and every other field dropped. The plugin's browser-script gate refuses any other script that touches
LinkedIn or a credential store. Never read, copy, export or look for a LinkedIn cookie, token or session:
not from the page, browser storage, profile files, DevTools data or the keychain. Never write a script of
your own that calls LinkedIn. The capture does not work through the Chrome extension, because the
extension's script tool runs outside the signed-in page's session and its network listing returns no
response bodies.

Run these steps in order for one Lead:

1. Open LinkedIn's Me page and read the profile URL of the signed-in account. This is
   `observedLinkedInProfile`.
   Or run the approved whoami script, as in **Start the run**, and pass its output exactly as returned as
   `identityEvidence` to `outreach_start_run`. If the script is unavailable, read the Me page.
2. Open the Lead's `linkedInProfileUrl` in the built-in browser pane. No reload is needed.
3. Run the script with the browser pane's `javascript_tool` by sending one line as the whole script:
   `// mosaico run linkedin-connection-evidence.js PUBLIC_IDENTIFIER=<public identifier>`, where the identifier
   is the Lead's `scriptIdentifier` from the Mosaico read when it is present (a member id or a public identifier, whatever Mosaico supplies), otherwise the part of the Lead's `linkedInProfileUrl` after `/in/`, with no trailing slash or query,
   without quotes. This is whatever stands there: a name such as `jane-doe`, or an id that starts with `ACoAA`. Use it as it is; do not look the Lead up or swap one for the other. The plugin's gate inserts the approved script; never print, retype, paraphrase, reorder,
   shorten or extend it. The query inside it is the one known to work today: if LinkedIn stops answering it,
   stop and report that; do not guess another.
   Fallback, only when the gate refuses the directive: print the approved script without changing it,

   ```bash
   cat "${CLAUDE_PLUGIN_ROOT:-$(dirname "$(dirname "$(find ~/.claude/plugins -path '*/mosaico-claude/browser/linkedin-connection-evidence.js' -print -quit)")")}/browser/linkedin-connection-evidence.js"
   ```

   then run the printed script with the browser pane's `javascript_tool`, changing only the value on its first
   line to that last segment, in quotes. Do not paraphrase, reorder, shorten or extend it: the gate refuses
   anything else.
4. If `signedIn` is false, the pane is not signed in to LinkedIn: stop the capture and report it. If
   `status` is not 200, `state` is `error` or `entries` is empty, stop: leave the Lead unverified, list it as
   skipped with the script's `errorStep` and `status` (they say why) and continue with the next Lead.
5. Call `outreach_record_connection_evidence` with the script's whole output exactly as returned
   (`status`, `signedIn`, `capturedAt`, `state`, `errorStep`, `profileIdentifier`, `requestedIdentifier`,
   `resolvedIdentifier`, `memberUrn`, `entries` and `integrity`; none of them changed), plus `profileUrl`
   (the Lead's `linkedInProfileUrl`), `leadId`, the `runId` and the identity evidence (`identityEvidence`
   from the whoami script, or `observedLinkedInProfile`). Report Mosaico's answer in plain words: connected, invite-pending,
   not-connected, or the blocker it returned. If Mosaico refused or the capture gave it nothing usable,
   leave the Lead unverified, list it as skipped and continue; follow any action Mosaico names, and do
   nothing else.

When the capability is unavailable (the script file is missing, the gate refuses it, or the pane cannot be
signed in), do not work around it. Leave the Lead unverified, note in the report only what the LinkedIn
page visibly shows (a Message, Connect or Pending button) for the person to read, never record that as a
connection state, and continue with the next Lead or stop the step and report it.

## Capture the sent invitation

Whether an invitation went out is a fact in LinkedIn's own Sent invitations list. This procedure carries
that data to Mosaico unchanged; Mosaico reads it and decides. Never judge from the screen whether a send
worked.

The capture is the plugin's sent-invitations script: one approved script, shipped at
`browser/linkedin-sent-invitations.js` inside the installed plugin, run through a one-line run directive in the signed-in
LinkedIn page by the built-in browser pane. It sends LinkedIn's own session and CSRF material to LinkedIn
only and never returns it; it looks for the one Lead on the Sent invitations list (up to five pages of a
hundred) and returns only whether it was found, when it was sent and the two URNs. The endpoint it calls
has not been validated against a live account yet: if it stops answering, stop and report that, and do not
guess another. The plugin's browser-script gate refuses any other script that touches LinkedIn or a
credential store, and the capture does not work through the Chrome extension.

Run these steps right after the send, for the Lead you just sent to:

1. Run the script with the browser pane's `javascript_tool` from any linkedin.com page by sending one line as the
   whole script: `// mosaico run linkedin-sent-invitations.js PUBLIC_IDENTIFIER=<public identifier>`, where the
   identifier is the Lead's `scriptIdentifier` from the Mosaico read when it is present (a member id or a public identifier, whatever Mosaico supplies), otherwise the part of the Lead's `linkedInProfileUrl` after `/in/`, with no trailing slash or query, without quotes. This is whatever stands there: a name such as `jane-doe`, or an id that starts with `ACoAA`. Use it as it is; do not look the Lead up or swap one for the other. The plugin's gate inserts the approved script;
   never print, retype, paraphrase, reorder, shorten or extend it.
   Fallback, only when the gate refuses the directive: print the approved script without changing it,

   ```bash
   cat "${CLAUDE_PLUGIN_ROOT:-$(dirname "$(dirname "$(find ~/.claude/plugins -path '*/mosaico-claude/browser/linkedin-sent-invitations.js' -print -quit)")")}/browser/linkedin-sent-invitations.js"
   ```

   then run the printed script with the browser pane's `javascript_tool` from any linkedin.com page, changing
   only the value on its first line to the same identifier, in quotes. Do not paraphrase, reorder,
   shorten or extend it: the gate refuses anything else.
2. If `signedIn` is false, the pane is not signed in to LinkedIn: stop and report it. If `state` is
   `error`, pass it anyway: Mosaico answers `send-evidence-malformed` and tells you to run it again. Its
   `errorStep` (`profile` or `sent-invitations`) and `status` say why; name them in the report.
3. Pass the script's whole output exactly as returned (every field, `integrity` included, and so
   `requestedIdentifier`, `resolvedIdentifier` and `memberUrn` too) as
   `sentInvitationEvidence` to `outreach_mark_message_sent`. If Mosaico answers `evidence-altered`, run the
   script again and pass the new output unchanged.

When the script is unavailable, do not work around it: see step 7 of **Send approved invitations**.

## Both

1. Complete **Source Leads and prepare drafts** first, until Mosaico says the sourcing run is complete (`sourcing-quota-met` or `sourcing-days-full`).
2. Reread the current Mosaico state for those dates.
3. Complete **Send approved invitations** only for messages that were already human-approved. Never
   approve a newly created draft automatically.

For every scope, Mosaico is the workflow authority for stored state, target completion, ownership,
validation, allowed actions and recovery. Stop only when the selected scope is complete, Mosaico
reports a genuine blocker, or a human decision is required. Mosaico decides which member a record belongs to from the run; do not try to work that out yourself.
Only Owners and Admins can use Outreach.

## End the run

End every run with `outreach_end_run` and the honest reason. Mosaico decides how the run ended, not you:

- `complete`: Mosaico says the run is complete (for sourcing, `sourcing-quota-met` or `sourcing-days-full`, or the failure stop after the tenth failure once the sourcing report is written).
- `blocked`: a genuine blocker stops the run. Give `blockerCode`, a code Mosaico returned in this run, or `linkedInIssue` (`warning`, `captcha` or `restricted`) with a `note`.

Never ask for `complete` or `blocked` to end a run you stopped yourself: Mosaico checks the claim and records a wrong one as abandoned, with the open lines, and a sourcing run left with a line open is a failed run.
Write a sourcing report with `outreach_record_sourcing_report` only when Mosaico reports `stop_run` after the tenth failure. While a line is open and Mosaico has not said so, it refuses with `sourcing-not-complete`: go back to searching.
Read the answer's `runOutcome` and report it.

## Source leads routine

This is the Source leads flow of Mosaico Outreach. It only finds Leads and writes invitation drafts. It never approves, sends or messages; the Sync data schedule does that.

**Mosaico connector.** Use the Mosaico connector that serves production (https://app.mosaico.one), the one the person connected in Claude. The plugin ships no Mosaico server of its own. If no Mosaico connector is connected, stop and tell the person to connect it in Claude's connectors (not /mcp), then rerun. Never use a server whose address contains amplifyapp.com, stage, staging, test or localhost; if that is the only Mosaico server available, stop and report it. Do not choose a server because its organisation id matches; stage and production share ids.

The schedule's text carries only the person's standing answers: the timezone and the LinkedIn public identifier; the actions are "source Leads only", then "source Leads and prepare invitation drafts". Neither the days nor the numbers are in the schedule: Mosaico files each Lead on a day, and Leads per day, Leads per run and who sources them are set on each Agent in Outreach (Agent tab), where Mosaico holds them. Take them from there; the schedule supplies the answers to this skill's opening questions, so do not ask them, do not show a menu, and do not ask which days or which scope. If a standing answer is missing, stop and report which one.

Resolve the current business date and time in the timezone from the schedule's standing answers. The person has supplied standing answers for this recurring automation: proceed without asking which days or which scope.

Do every LinkedIn step in Claude's built-in browser pane, from any linkedin.com page, signed in to the person's LinkedIn (the public identifier from the schedule's standing answers). Obtain connection evidence and identity only through the plugin's approved capture scripts, run by sending the browser javascript tool the one-line directive `// mosaico run <script>.js <PLACEHOLDER>=<value>` (the plugin's gate inserts the approved script; never retype a script), exactly as the skills describe; if the gate refuses the directive, run the approved script word for word with only the first line's value changed (the thread script's second line holds the Lead's name). The first-line value for every per-Lead script is the Lead's scriptIdentifier from the Mosaico read when it is present (a member id or a public identifier, whatever Mosaico supplies), otherwise the part of its linkedInProfileUrl after /in/. The thread script also takes the Lead's name from the Mosaico read, so its directive is `// mosaico run linkedin-thread-messages.js PUBLIC_IDENTIFIER=<scriptIdentifier> LEAD_NAME=<the Lead's name>`. The approved scripts are browser/linkedin-whoami.js, browser/linkedin-connection-evidence.js and browser/linkedin-salesnav-colleague-connection.js; read each from the installed plugin. Read each script file with the file-reading tool, one file at a time, by its path under the installed plugin's browser folder; do not print them with a shell command. If the installed plugin has no browser folder, stop and report that the plugin needs updating. Never read, copy, export or reconstruct a LinkedIn cookie, token or session; never write a LinkedIn script of your own; never read a Connect, Message or Pending button as a connection state; never set a connection state yourself. If a capture is unavailable or Mosaico cannot use its result, leave that Lead unverified, list it as skipped, and continue.

Step 1. Open any linkedin.com page once. Run the approved whoami script and pass its output unchanged as identityEvidence to outreach_start_run (omit observedLinkedInProfile). Send no quota and no colleague: Mosaico derives the quota from the sourcing plan on the Agents (the sum of the Leads per run of each owner's Agents). Only if the whoami script cannot run, open the Me page and report its profile URL as observedLinkedInProfile instead. Start the sourcing run once (Step 2 and Step 3 use the same run) and pass its runId on every read and write; before each evidence write, run the whoami script again and pass its output as identityEvidence. If Mosaico blocks the start, stop and report the blocker; do not work around it. Read environmentName in the start answer. If it is not production, stop and report it; do not work in that environment. The report's first line is "Mosaico environment: production" (the name the answer gave). If the answer carries the note previous-run-abandoned, your last Source leads run was left with a line open: say so right after that line, as "Previous run failed: stopped with N open" (N from previousRun.openLines), then go on. If it answers sourcing_plan_empty (recommended action set_agent_sourcing_numbers_in_outreach), stop: quote Mosaico's code and message verbatim, then end the report with this sentence: "Set Leads per day and Leads per run on an Agent in Outreach (Agent tab), then rerun." Do not ask the person for numbers. If it answers sourcing-days-full (recommended action wait_for_free_days), no run was issued because every planned Agent is full for the next 10 business days: this is not a failure; stop and report "Every Agent is full for the next 10 business days; nothing to source." Otherwise the run carries run.quota and run.sourcingPlan.

Step 2. Run this skill with the selected action "source Leads only". Before you source, call outreach_get_agents with the runId. Never pass ownerUserId with it. It returns every Agent in this run's plan, yours and your colleagues', each with its own search and message instructions, checklist and attachments: work from every returned Agent's own instructions, including colleagues' Agents, for the Leads you save under it. Mosaico files every Lead on a day; you never choose one. Call outreach_get_day without day. Never send targetCount for sourcing. Never send scheduledDate. Each Lead is saved directly under the target owner by the run; there is no transfer step. Follow workflowStatus.recommendedAction and reread after every saved Lead. Keep sourcing while any line of workflowStatus.sourcingPlan is open, following workflowStatus.nextOwnerUserId and nextAgentId; the stop is Mosaico's completion (Step 4), never your own judgement. Read workflowStatus.sourcingPlan, workflowStatus.agentId and workflowStatus.nextAgentId from outreach_get_day and pass the agentId for the owner you save for on every outreach_save_lead, as this skill's "Which Agent a Lead goes to" says; if Mosaico blocks a save with agent-required, agent-not-in-sourcing-plan or planned-agent-quota-met, save again once with the agentId it gives; sourcing-quota-met and sourcing-days-full save nothing and are not failures: reread outreach_get_day for the next step. Before saving a candidate for a colleague, when outreach_get_day lists that colleague in workflowStatus.colleagueChecks with allowed true, run the colleague-connection check as this skill describes: send the directive from that entry, `// mosaico run linkedin-salesnav-colleague-connection.js PUBLIC_IDENTIFIER=<the candidate's identifier> COLLEAGUE_IDENTIFIER=<the colleague's identifier from workflowStatus.colleagueChecks>`, from a Sales Navigator page (open https://www.linkedin.com/sales/home first), and pass its whole output unchanged as colleagueConnectionEvidence on outreach_save_lead. Pass the output exactly as returned, every field including complete, controlTotal, visibility and unreadableRows (a null stays a null, never left out) and integrity. Mosaico's answer is final: a skipped candidate (already connected to the colleague) is not a failure; a candidate saved with the note colleague-check-negative-proven is verified not connected by the colleague check, and you draft her invitation in Step 3; a candidate saved with colleague-check-negative-unproven is not proven unconnected and stays undrafted, so continue sourcing. Never run the connection-evidence script for a colleague's Lead and never call outreach_record_connection_evidence for it: Mosaico answers evidence-owner-mismatch, and only her own Sync run verifies it.

Step 3. Run this skill again with the same run and the selected action "source Leads and prepare invitation drafts", across every day in workflowStatus.runDays, not just one. For each of your own Leads Mosaico lists as connection unverified, open its profile, run the approved connection-evidence script and pass the result unchanged to outreach_record_connection_evidence. Write a missing invitation draft only for a Lead Mosaico lists as verified. For each colleague with Leads saved in this run, read her day (outreach_get_day with intent source_invitation_leads, the runId and her member id from workflowStatus.sourcingPlan as ownerUserId; a read only) and, as this skill's "Draft a colleague's invitation" says, write the missing invitation draft with outreach_record_message (her leadId, no ownerUserId on the call) for each Lead saved with colleague-check-negative-proven; leave the unproven ones undrafted. Never approve or send an invitation.

Step 4. Stop only when Mosaico says the run is complete (workflowStatus.completion is complete with reason sourcing-quota-met or sourcing-days-full) and nothing is left to verify or draft, when Mosaico recommends end_run_days_full, or when Mosaico reports stop_run after the tenth failure (then write the sourcing report Mosaico asks for). Never stop while any line of workflowStatus.sourcingPlan is open, and never because you think enough was found. A skipped candidate, a refused write for one Lead, or sourcing-quota-met or sourcing-days-full on a save is not a reason to stop. There is no search limit: do as many searches as it takes, and "I could not find candidates", "few results", "weak results", "slow" and "enough found" are never a reason to stop. When results are few, widen inside the Agent's brief (more keywords, more results pages, other filters, other regions the brief allows, Premium Daily Prospects) and keep searching; never widen past the brief's qualification rules. If an Agent's brief says to report a lead supply constraint, note it for the final report and keep searching inside the brief; it never means stop. A run that ends with any line still open and no stop_run is a failed run: report it as "run failed: stopped with N open". Then end the run with outreach_end_run and the honest reason, and let Mosaico decide the outcome: reason complete when Mosaico says the run is complete or the failure stop fired; reason blocked, with the blockerCode Mosaico gave in this run or the linkedInIssue (warning, captcha or restricted) and a note, when a genuine blocker stops it. Never write a sourcing report while a line is open unless Mosaico says the failure stop fired; before then Mosaico refuses it with sourcing-not-complete and you keep searching. Mosaico records a complete or blocked claim it cannot back as abandoned.

Step 5. Start the report with the line "Mosaico environment: <environmentName>" and, when the start answer carried previous-run-abandoned, the line "Previous run failed: stopped with N open". Report separately, using Mosaico's counts, not memory: the runOutcome Mosaico gave when you ended the run; for each owner and each of their Agents in workflowStatus.sourcingPlan, the target (Leads per run), the Leads accepted, the Leads remaining and the status (name the owner and the Agent); for each day in workflowStatus.runDays, how many Leads were filed on it; the shortfalls in workflowStatus.shortfalls; candidates skipped as already connected to each owner (from workflowStatus.colleagueSkips), the Leads saved for each colleague as "verified not connected by colleague check (proven)" (note colleague-check-negative-proven) and as "unproven, awaiting her Sync" (note colleague-check-negative-unproven), drafts written (and the drafts written for each colleague), candidates skipped with reasons, Leads left unverified, blockers. A run Mosaico records as abandoned is a failed run: report it as "run failed: stopped with N open". A run that saved nothing because of a blocker other than days-full is a failed run: report it as failed with Mosaico's code (for example sourcing_plan_empty) and message, also when Mosaico refused the start, and never as successful. A run that ends sourcing-days-full with nothing saved is not a failure: report "Every Agent is full for the next 10 business days; nothing to source." Nothing merely drafted may be described as approved or sent. Preserve Mosaico as workflow authority and never modify another owner's records.

Guards: pacing between page loads and run expiry are enforced by Mosaico; a LinkedIn warning or captcha stops the run, which then reports.
