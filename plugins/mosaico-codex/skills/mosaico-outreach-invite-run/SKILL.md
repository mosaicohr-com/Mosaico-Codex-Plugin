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
throughout the run. Accept one action and run only the selected scope.

## Start the run

1. Open LinkedIn's Me page in the authenticated browser and read the profile URL of the signed-in
   account. Report what you see; do not decide or correct it.
2. Call `outreach_start_run` with that URL as `observedLinkedInProfile` and the intent: `source_invitation_leads` for sourcing, `send_approved_invitations` for sending. When doing both, start a separate run for each scope.
   A sourcing start must also say who receives the Leads and how many each, or Mosaico issues no run
   (the application never guesses a colleague). Send one of two things with `outreach_start_run`:
   - `quota`: a map from each active owner's member id to the number of accepted Leads that owner
     must reach (a whole number from 1 to 100). It must always include the run owner's own id, for
     example `{"<run owner member id>": 3, "<colleague member id>": 3}`. Naming anyone but the run owner
     needs an Owner or Admin.
   - `colleagueOwnerUserId`: the member id of one active colleague, distinct from the run owner. Mosaico
     then gives the run owner and that colleague 5 each.

   The person's standing answer says who receives Leads and how many; use it as given. Member ids come
   from `get_team_profiles` (each person's "Person ID"); never invent one or take one from memory. If
   neither a quota nor a colleague is known, do not start the run: ask the person who receives the Leads
   and how many each. A scheduled run cannot ask: it stops, quotes Mosaico's code and message verbatim when
   Mosaico gave one, and ends its report with this sentence: "Fix: run /mosaico:mosaico-outreach-schedule-install (Codex: the mosaico-outreach-schedule-install skill), answer who receives the Leads and how many each, and it will put the quota map into this schedule." If
   Mosaico answers `sourcing_participant_required`, the start needs `colleagueOwnerUserId` or `quota`; if it
   answers `sourcing_quota_invalid`, the map is wrong (an id that is not an active member, the run owner
   missing, or a target outside 1 to 100). Mosaico's answer says what to fix: fix exactly that from the
   person's answer and start again once, never with a guessed colleague or number. The quota decides when
   the run is complete. When the person answered those two questions in this run, make the offer in
   **Offer to save the quota into the Source leads schedule**, below.
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

## Offer to save the quota into the Source leads schedule

Do this only when the person answered who receives the Leads and how many each during this run. It does
not apply when the quota came from a schedule's standing answer. Once you have the answer, ask once,
before you start the run or straight after: "Do you want me to save this into your Source leads schedule,
so the scheduled runs use it too?" The run does not depend on the answer.

- Yes: follow "Update the Source leads quota in place" in the `$mosaico:mosaico-outreach-schedule-install`
  skill, which updates the Codex Source leads automation, for that automation only. Ask nothing else,
  change nothing else in it, and keep its times. Read the saved automation back and tell the person what
  it now holds.
- No: use the answer for this run only, and say in the report that the quota was used for this run only and
  the Source leads schedule is unchanged.
- If no Source leads automation is installed, say so and offer to install one with
  `$mosaico:mosaico-outreach-schedule-install`. Do not skip the offer silently.

## Source Leads and prepare drafts

1. Read `outreach_get_agents`, then call `outreach_get_day` for each selected day with
   `intent: source_invitation_leads`, `targetCount: 20`, and the `runId`.
2. Follow `workflowStatus.recommendedAction`. Use its prepared count, remaining count, blockers and
   completion result; do not reconstruct them from separate records or conversation memory. When the
   recommended action is `verify_connection`, Mosaico lists the Leads whose connection is unknown or
   unverified in `workflowStatus.unverifiedLeads`, each with its profile URL: for each one run
   **Capture connection evidence**, then reread `outreach_get_day`. Never guess a connection and never
   skip to drafting for a listed Lead.
3. A day with fewer than 20 qualified Leads is incomplete. Continue searching, broadening suitable
   searches, checking profiles, saving qualified Leads with their profile details and preparing
   missing invitation drafts until every selected day contains 20.
4. Do not stop because the work is slow, difficult, expensive or because an initial search produced
   only a few Leads. Loading 3 Leads is not completion; if 17 are still missing, continue until all
   17 are found.
5. Save each qualified Lead through `outreach_save_lead`, which takes no connection state: the new Lead
   starts unknown. Then run **Capture connection evidence** for it, so Mosaico records connected,
   invite-pending or not-connected before any draft is written. Write the missing outbound Invite draft
   only for a Lead Mosaico lists as verified. Do not approve or send any invitation in this scope.
6. Reread `outreach_get_day` after every saved Lead and draft. Mosaico preserves partial progress and
   owns the 20-Lead completion predicate; a valid partial save is not a completed run.
7. Report a shortfall only when a genuine Mosaico, authentication, LinkedIn or human-decision blocker
   prevents further work. State the exact completed count, remainder and blocker; never report the
   day as complete below 20.
8. Finish with **Report a sourcing run**.

## Source Leads only

Use this scope when the Leads go to the owners named in the run's quota (the person alone, a colleague,
or several members) before any draft is written, so that each owner's drafts are later written under
their own Agent and voice.

1. Same as "Source Leads and prepare drafts", but the target is the quota sent at the start of the run:
   each owner's accepted-Lead target, not the 20 of a prepared day. Mosaico keeps the quota and reports
   what remains for each owner; use its counts, and `workflowStatus.counts.readyLeads` for the ready
   Leads, not the prepared count.
2. Save each qualified Lead with its profile details through `outreach_save_lead`, which takes no
   connection state, then run **Capture connection evidence** for it. Do not write any invitation draft
   in this scope, and do not approve or send anything.
3. Reread `outreach_get_day` after every saved Lead and continue until Mosaico says the quota is met or
   returns a blocker, `human_decision_required` or `stop_run`.
4. Finish with **Report a sourcing run**. A run below its quota is not complete.

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

Report in plain words, using Mosaico's counts, not memory: for each owner in the quota, the Leads saved
and the quota remaining (name the owner and the member id), the candidates skipped as already connected
to that owner ("skipped as already connected to <owner>: N", from `workflowStatus.colleagueSkips`; its
entries name the owner), and any shortfall with its blocker. A run
that saved nothing is a failed run: report it as failed with Mosaico's code and message (for example
`sourcing_participant_required`, `sourcing_quota_invalid` or the blocker that stopped it), including a run
Mosaico refused at the start. Never report such a run as successful, and never describe a partly filled
quota as complete. If the person answered the quota questions in this run, say whether the quota was saved into the
Source leads automation or used for this run only.

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

1. Complete **Source Leads and prepare drafts** first and reach 20 Leads on every selected date.
2. Reread the current Mosaico state for those dates.
3. Complete **Send approved invitations** only for messages that were already human-approved. Never
   approve a newly created draft automatically.

For every scope, Mosaico is the workflow authority for stored state, target completion, ownership,
validation, allowed actions and recovery. Stop only when the selected scope is complete, Mosaico
reports a genuine blocker, or a human decision is required. Mosaico decides which member a record belongs to from the run; do not try to work that out yourself.
Only Owners and Admins can use Outreach.
