---
name: mosaico-outreach-follow-up-run
description: Check Mosaico Outreach for new LinkedIn follow-ups, send already-approved drafts, or perform both workflows safely.
---

# Mosaico Outreach Follow-up Run

Before using any Outreach or browser tool, ask exactly:

> Do you want to check for new follow-ups, send approved drafts, or both?

Accept only **check for new follow-ups**, **send approved drafts**, or **both**, and run only that
scope. If the answer includes checking, ask before using tools:

> Do you also want me to write follow-up drafts for connected Leads who accepted the connection but have not replied?

Treat the answer as an additional drafting scope, not permission to approve or send those drafts. 

## Start the run

1. Open LinkedIn's Me page in the authenticated browser and read the profile URL of the signed-in
   account. Report what you see; do not decide or correct it.
2. Call `outreach_start_run` with that URL as `observedLinkedInProfile` and the intent: `check_follow_ups` for checking, `send_approved_follow_ups` for sending. When doing both, start a separate run for each scope.
3. Keep the returned `runId` and pass it on every `outreach_get_day` or `outreach_get_follow_ups`
   read and on every `outreach_save_lead`, `outreach_update_lead`, `outreach_record_message`,
   `outreach_deposit_conversation` and `outreach_mark_message_sent` call. Never pass `ownerUserId` on
   a write; Mosaico takes the owner from the run.
4. If Mosaico returns a blocker at any step, stop and tell the person what it says. Do not retry with
   a different profile or work around it. In a scheduled run, a blocker means stop and report.
5. Before `outreach_deposit_conversation` and `outreach_mark_message_sent`, open the Me page again and
   pass the profile you see then as `observedLinkedInProfile`.
6. If an Owner or Admin asks to run for a colleague, pass that member's id as `onBehalfOfMemberId` on
   `outreach_start_run` only. The LinkedIn account must then be that colleague's.

If `outreach_save_lead` or `outreach_deposit_conversation` reports that the profile already exists
under another owner, stop and show the person the owner, Lead and status. Re-send with
`acknowledgeProfileOnOtherOwner: true` only after the person decides to; never set it yourself.

## Check for new follow-ups

1. Work across all dates and read `outreach_get_follow_ups` with the `runId`.
2. Open `https://www.linkedin.com/mynetwork/invite-connect/connections/` and identify new
   connections that correspond to recorded Mosaico Outreach Leads.
3. Inspect each relevant currently visible LinkedIn conversation.
4. Deposit each complete visible conversation oldest to newest through
   `outreach_deposit_conversation`. Do not compare it with stored history or decide which reply is
   newer; Mosaico owns identity matching, chronology, follow-up state, blockers and allowed actions.
5. Save every missing follow-up reply through `outreach_record_message` as an outbound follow-up
   draft with `sentAt` null.
6. If the person opted into connected Leads without replies, also save missing follow-up drafts for
   those Leads when Mosaico permits `draft_follow_up`. Use their visible profile, stored conversation
   context and assigned Agent instructions; do not invent a reply from the Lead.
7. Continue drafting when Mosaico permits `draft_follow_up` even if a separate historical
   `message.kind` sorting issue remains.
8. Do not approve or send any message in this scope.

## Send approved drafts

1. Work only on exact outbound follow-up messages whose current Mosaico status is already Approved.
2. Never approve, rewrite or substitute a message. If the approved body does not exactly match the
   body about to be sent, stop for that message and report the blocker.
3. Send through the authenticated LinkedIn browser.
4. Verify delivery on LinkedIn rather than trusting the click.
5. Call `outreach_mark_message_sent` only after successful delivery verification, using the exact
   Lead and Message identities and the exact send time when LinkedIn exposes it, otherwise null.
6. Continue until every currently approved follow-up draft is sent or Mosaico reports a genuine
   blocker.

## Both

1. Complete **Check for new follow-ups** first.
2. Reread the current Mosaico state.
3. Complete **Send approved drafts** only for messages that were already human-approved. Never
   approve a newly created draft automatically.

For every scope, Mosaico is the workflow authority. Follow its allowed actions and recommended
action. Stop only when the selected scope is complete, Mosaico reports a genuine blocker, or a human
decision is required. Mosaico decides which member a record belongs to from the run; do not try to work that out
yourself. Only Owners and Admins can use Outreach.
