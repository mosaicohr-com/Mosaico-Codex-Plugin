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
3. Keep the returned `runId` and pass it on every `outreach_get_day` or `outreach_get_follow_ups`
   read and on every `outreach_save_lead`, `outreach_update_lead`, `outreach_record_message`,
   `outreach_deposit_conversation`, `outreach_mark_message_sent` and `outreach_record_delivery_block`
   call. Never pass `ownerUserId` on
   a write; Mosaico takes the owner from the run.
4. Tell a run-level blocker from a one-Lead outcome. A run-level blocker is about the run itself:
   LinkedIn identity mismatch or not registered, the run expired, unknown or foreign, sign-in lost,
   or Mosaico or LinkedIn failing. Only then stop and tell the person what Mosaico says; do not retry
   with a different profile or work around it. Everything else is about one Lead or one Message:
   a `skipped` result, a `blocked` state, a refused write, a `history-mismatch`, a draft that
   already exists, a conflict, a not-found. Record what Mosaico returned, skip that Lead and
   continue with the next one; Mosaico keeps the Lead for a person in To sort. A scheduled run
   never stops for one Lead.
5. Before `outreach_deposit_conversation`, `outreach_mark_message_sent` and
   `outreach_record_delivery_block`, open the Me page again and
   pass the profile you see then as `observedLinkedInProfile`.
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
   `intent: source_invitation_leads`, `targetCount: 20`, and the `runId`.
2. Follow `workflowStatus.recommendedAction`. Use its prepared count, remaining count, blockers and
   completion result; do not reconstruct them from separate records or conversation memory.
3. A day with fewer than 20 qualified Leads is incomplete. Continue searching, broadening suitable
   searches, checking profiles, saving qualified Leads with their profile details and preparing
   missing invitation drafts until every selected day contains 20.
4. Do not stop because the work is slow, difficult, expensive or because an initial search produced
   only a few Leads. Loading 3 Leads is not completion; if 17 are still missing, continue until all
   17 are found.
5. Save each qualified Lead and its missing outbound Invite draft through the Mosaico tools. Do not
   approve or send any invitation in this scope.
6. Reread `outreach_get_day` after every saved Lead and draft. Mosaico preserves partial progress and
   owns the 20-Lead completion predicate; a valid partial save is not a completed run.
7. Report a shortfall only when a genuine Mosaico, authentication, LinkedIn or human-decision blocker
   prevents further work. State the exact completed count, remainder and blocker; never report the
   day as complete below 20.

## Source Leads only

Use this scope when the Leads will be shared with a colleague before any draft is written, so that
each owner's drafts are later written under their own Agent and voice.

1. Same as "Source Leads and prepare drafts", but the target is the number of ready Leads the person
   named (for example 40), read from `workflowStatus.counts.readyLeads`, not the prepared count.
2. Save each qualified Lead with its profile details through `outreach_save_lead`. Do not write any
   invitation draft in this scope, and do not approve or send anything.
3. Reread `outreach_get_day` after every saved Lead and continue until `counts.readyLeads` reaches
   the named number or Mosaico returns a blocker, `human_decision_required` or `stop_run`.
4. Report the exact count of ready Leads and any shortfall with its blocker. A day below the named
   number is not complete.

## Send approved invitations

1. Call `outreach_get_day` for each selected date with `intent: send_approved_invitations` and
   the `runId`. Work only on exact outbound Invite messages returned as
   Approved and permitted by `workflowStatus`. Messages listed under
   `workflowStatus.blockedDeliveries` are never sent; do not retry them.
2. Never approve, rewrite, replace or substitute an invitation. If the approved body does not exactly
   match the body about to be sent, stop for that invitation and report the blocker.
3. Open the Lead's LinkedIn profile (use the `linkedInProfileUrl` Mosaico returns when present) and
   read the connection control before doing anything else:
   - **Connect** — send the invitation.
   - **Message** (already a connection) — do not invite. Call `outreach_record_delivery_block` with
     `reason: already-connected`. Mosaico marks the Lead connected so it moves to follow-ups.
   - **Pending** (an invitation is already waiting) — do not invite again. Call
     `outreach_record_delivery_block` with `reason: invite-pending`.
   Recording an outcome is not a blocker: Mosaico removes that Message from the send list and you
   continue with the next one.
4. Send through the authenticated LinkedIn browser.
5. Verify each invitation against LinkedIn rather than trusting the click.
6. Call `outreach_mark_message_sent` only after successful delivery verification, using the exact
   Lead and Message identities and the exact send time when LinkedIn exposes it, otherwise null.
7. Reread the same day after each send or recorded outcome and continue until Mosaico reports
   completion or a genuine blocker (Mosaico, sign-in or LinkedIn failure). One Lead that cannot be
   invited never stops the run.
8. In the final report list recorded outcomes separately from sends and blockers, each with its
   Lead and reason.

## Both

1. Complete **Source Leads and prepare drafts** first and reach 20 Leads on every selected date.
2. Reread the current Mosaico state for those dates.
3. Complete **Send approved invitations** only for messages that were already human-approved. Never
   approve a newly created draft automatically.

For every scope, Mosaico is the workflow authority for stored state, target completion, ownership,
validation, allowed actions and recovery. Stop only when the selected scope is complete, Mosaico
reports a genuine blocker, or a human decision is required. Mosaico decides which member a record belongs to from the run; do not try to work that out yourself.
Only Owners and Admins can use Outreach.
