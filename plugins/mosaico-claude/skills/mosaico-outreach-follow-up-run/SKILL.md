---
name: mosaico-outreach-follow-up-run
description: Check Mosaico Outreach for new LinkedIn follow-ups, send already-approved drafts, perform both, or run one pass per thread, safely.
---

# Mosaico Outreach Follow-up Run

Before using any Outreach or browser tool, ask exactly:

> Do you want to check for new follow-ups, send approved drafts, both, or one pass per thread?

Accept only **check for new follow-ups**, **send approved drafts**, **both**, or **one pass per
thread**, and run only that scope. If the answer includes checking, ask before using tools:

> Do you also want me to write follow-up drafts for connected Leads who accepted the connection but have not replied?

Treat the answer as an additional drafting scope, not permission to approve or send those drafts. 

## Start the run

1. Open LinkedIn's Me page in the authenticated browser and read the profile URL of the signed-in
   account. Report what you see; do not decide or correct it.
2. Call `outreach_start_run` with that URL as `observedLinkedInProfile` and the intent: `check_follow_ups` for checking, `send_approved_follow_ups` for sending. When doing both, start a separate run for each scope.
3. Keep the returned `runId` and pass it on every `outreach_get_day` or `outreach_get_follow_ups`
   read and on every `outreach_save_lead`, `outreach_update_lead`, `outreach_record_message`,
   `outreach_deposit_conversation`, `outreach_mark_message_sent` and `outreach_record_delivery_block`
   call. Never pass `ownerUserId` on
   a write; Mosaico takes the owner from the run.
4. If Mosaico returns a blocker at any step, stop and tell the person what it says. Do not retry with
   a different profile or work around it. In a scheduled run, a blocker means stop and report.
5. Before `outreach_deposit_conversation`, `outreach_mark_message_sent` and
   `outreach_record_delivery_block`, open the Me page again and
   pass the profile you see then as `observedLinkedInProfile`.
6. If an Owner or Admin asks to run for a colleague, pass that member's id as `onBehalfOfMemberId` on
   `outreach_start_run` only. The LinkedIn account must then be that colleague's.

If `outreach_save_lead` or `outreach_deposit_conversation` reports that the profile already exists
under another owner, stop and show the person the owner, Lead and status. Re-send with
`acknowledgeProfileOnOtherOwner: true` only after the person decides to; never set it yourself.

## Check for new follow-ups

1. Work across all dates and read `outreach_get_follow_ups` with the `runId`.
2. For each returned Lead, open its pages directly: `navigation.messageUrl` (the stored
   conversation) when present, otherwise `navigation.profileUrl`. Do not search LinkedIn lists for
   Leads that carry a URL. Open `https://www.linkedin.com/mynetwork/invite-connect/connections/`
   only to find new connections among Leads that have no conversation URL yet.
3. Inspect each relevant currently visible LinkedIn conversation.
4. Deposit each complete visible conversation oldest to newest through
   `outreach_deposit_conversation`, passing the conversation's URL as `linkedInMessageUrl` so the next
   run opens it directly. Do not compare it with stored history or decide which reply is newer;
   Mosaico owns identity matching, chronology, follow-up state, blockers and allowed actions.
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
   Messages Mosaico returns as blocked are never sent; do not retry them.
2. Never approve, rewrite or substitute a message. If the approved body does not exactly match the
   body about to be sent, stop for that message and report the blocker.
3. Open the conversation directly through the `linkedInMessageUrl` Mosaico returns when present;
   otherwise open the Lead's profile and use Message. If the conversation cannot be opened or the
   person cannot be messaged, call `outreach_record_delivery_block` with `reason: cannot-message` and
   continue with the next message. Recording an outcome is not a blocker.
4. Send through the authenticated LinkedIn browser.
5. Verify delivery on LinkedIn rather than trusting the click.
6. Call `outreach_mark_message_sent` only after successful delivery verification, using the exact
   Lead and Message identities and the exact send time when LinkedIn exposes it, otherwise null.
7. Continue until every currently approved follow-up draft is sent or recorded, or Mosaico reports a
   genuine blocker (Mosaico, sign-in or LinkedIn failure). One Lead that cannot be messaged never
   stops the run.
8. In the final report list recorded outcomes separately from sends and blockers, each with its
   Lead and reason.

## Both

1. Complete **Check for new follow-ups** first.
2. Reread the current Mosaico state.
3. Complete **Send approved drafts** only for messages that were already human-approved. Never
   approve a newly created draft automatically.

## One pass per thread

The scope for a scheduled daily run: each LinkedIn conversation is opened once, and replies are
handled before anything else is sent.

1. Read `outreach_get_follow_ups` with the `runId`. Work through every returned Lead in order.
2. For each Lead, open `navigation.messageUrl` directly (the profile URL when there is no thread
   yet; the connections page only for Leads without any URL).
3. Deposit the complete visible conversation oldest to newest through
   `outreach_deposit_conversation`, passing the conversation's URL as `linkedInMessageUrl`. If
   Mosaico reports `returnedToDraft`, that Lead's approved follow-up is now a draft because a new
   reply arrived: do not send it.
4. Reread the Lead's state. If Mosaico still lists an approved outbound follow-up for it, send it
   exactly as approved, verify delivery on LinkedIn and call `outreach_mark_message_sent` only after
   successful verification.
5. If the conversation cannot be opened or the person cannot be messaged, call
   `outreach_record_delivery_block` with `reason: cannot-message` and continue with the next Lead.
6. Save every missing follow-up draft Mosaico permits through `outreach_record_message` with
   `sentAt` null, including a first follow-up for each accepted invitation without a reply. Never
   approve a draft; never send a draft created in this run.
7. Continue until every Lead has been handled or Mosaico reports a genuine blocker (Mosaico,
   sign-in or LinkedIn failure). One Lead that fails is recorded and skipped, never a halt.
8. Report sends, recorded outcomes, drafts written, and skipped Leads with reasons, separately.

For every scope, Mosaico is the workflow authority. Follow its allowed actions and recommended
action. Stop only when the selected scope is complete, Mosaico reports a genuine blocker, or a human
decision is required. Mosaico decides which member a record belongs to from the run; do not try to work that out
yourself. Only Owners and Admins can use Outreach.
