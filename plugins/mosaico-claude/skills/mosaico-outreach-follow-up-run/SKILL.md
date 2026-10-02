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

If `outreach_save_lead` or `outreach_deposit_conversation` reports that the profile already exists
under another owner, stop and show the person the owner, Lead and status. Re-send with
`acknowledgeProfileOnOtherOwner: true` only after the person decides to; never set it yourself.

## Check for new follow-ups

1. Work across all dates and read `outreach_get_follow_ups` with the `runId`. When the recommended
   action is `verify_connection`, Mosaico lists the Leads whose connection is unknown or unverified in
   `unverifiedLeads`, each with its profile URL: for each one run **Capture connection evidence**, then
   reread `outreach_get_follow_ups`. Never guess a connection and never skip to drafting for a listed
   Lead.
2. For each returned Lead, open its pages directly: `navigation.messageUrl` (the stored
   conversation) when present, otherwise `navigation.profileUrl`. Do not search LinkedIn lists for
   Leads that carry a URL, and never read a LinkedIn list or button to decide whether a Lead is
   connected.
3. Inspect each relevant currently visible LinkedIn conversation.
4. Deposit each complete visible conversation oldest to newest through
   `outreach_deposit_conversation`, passing the conversation's URL as `linkedInMessageUrl` so the next
   run opens it directly. Do not compare it with stored history or decide which reply is newer;
   Mosaico owns identity matching, chronology, follow-up state, blockers and allowed actions.
5. Save every missing follow-up reply through `outreach_record_message` as an outbound follow-up
   draft with `sentAt` null.
6. If the person opted into connected Leads without replies, also save missing follow-up drafts for
   those Leads when Mosaico permits `draft_follow_up` (Mosaico permits it only for a Lead it lists as
   verified). Use their visible profile, stored conversation
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

## Capture connection evidence

Whether you are connected to a Lead is a fact in LinkedIn's own data, not on the page's buttons. This
procedure carries that data to Mosaico unchanged; Mosaico reads it and decides. Never read a Message,
Connect or Pending button as a connection state, never choose a field by what it means and never decide
the relationship yourself.

This capture needs the built-in browser pane. It does not work through the Chrome extension, because
the extension's script tool cannot read the LinkedIn session cookie the call needs and its network
listing returns no response bodies.

Run these steps in order for one Lead:

1. Open LinkedIn's Me page and read the profile URL of the signed-in account. This is
   `observedLinkedInProfile`.
2. Open the Lead's `linkedInProfileUrl` in the built-in browser pane, so the LinkedIn session cookie is
   present. No reload is needed.
3. Run this fixed script with the browser pane's `javascript_tool`,
   changing only `PUBLIC_IDENTIFIER` to the last segment of the profile URL's path (the part after
   `/in/`, with no trailing slash or query). Do not paraphrase, reorder or extend the script. The query id inside it is the one known to work today: if LinkedIn
   stops answering it, stop and report that; do not guess another.

```js
const id = "PUBLIC_IDENTIFIER";
const csrf = (document.cookie.match(/JSESSIONID="?([^;"]+)/) || [])[1];
const r = await fetch("https://www.linkedin.com/voyager/api/graphql?includeWebMetadata=true&variables=(vanityName:" + encodeURIComponent(id) + ")&queryId=voyagerIdentityDashProfiles.34ead06db82a2cc9a778fac97f69ad6a", { credentials: "include", headers: { "csrf-token": csrf, "x-restli-protocol-version": "2.0.0", "accept": "application/vnd.linkedin.normalized+json+2.1" } });
const j = r.ok ? await r.json() : null;
const inc = (j && j.included) || [];
({ status: r.status, capturedAt: new Date().toISOString(), entries: inc.filter(e => /MemberRelationship$/.test(String(e["$type"])) || (e.publicIdentifier === id && /profile\.Profile$/.test(String(e["$type"])))) })
```

4. If `status` is not 200 or `entries` is empty, stop: leave the Lead unverified, list it as skipped
   and continue with the next Lead.
5. Call `outreach_record_connection_evidence` with `leadId`, `profileUrl` (the Lead's
   `linkedInProfileUrl`), `capturedAt` and `entries` exactly as the script returned them, the `runId`
   and `observedLinkedInProfile`. Report Mosaico's answer in plain words: connected, invite-pending,
   not-connected, or the blocker it returned. If Mosaico refused or the capture gave it nothing usable,
   leave the Lead unverified, list it as skipped and continue; follow any action Mosaico names, and do
   nothing else.

## Both

1. Complete **Check for new follow-ups** first.
2. Reread the current Mosaico state.
3. Complete **Send approved drafts** only for messages that were already human-approved. Never
   approve a newly created draft automatically.

## One pass per thread

The scope for a scheduled daily run: each LinkedIn conversation is opened once, and replies are
handled before anything else is sent.

1. Read `outreach_get_follow_ups` with the `runId`. Work through every returned Lead in order. When
   the recommended action is `verify_connection`, run **Capture connection evidence** for each Lead in
   `unverifiedLeads` first and reread; never guess a connection and never draft for a Lead Mosaico
   still lists as unverified.
2. For each Lead, open `navigation.messageUrl` directly (the profile URL when there is no thread
   yet). If that URL opens a different
   person's conversation, do not deposit it: call `outreach_update_lead` with
   `linkedInMessageUrl: null` and `reason: wrong-person`, then open the Lead's profile and use
   Message to find the right thread; if it cannot be found, continue with the next Lead.
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
   `sentAt` null. Mosaico decides which Leads are due, including an accepted invitation without a
   reply, and permits a draft only for a Lead it lists as verified. Never approve a draft; never send a
   draft created in this run.
7. Continue until every Lead has been handled or Mosaico reports a genuine blocker (Mosaico,
   sign-in or LinkedIn failure). One Lead that fails is recorded and skipped, never a halt.
8. Report sends, recorded outcomes, drafts written, Leads left unverified, and skipped Leads with
   reasons, separately.

For every scope, Mosaico is the workflow authority. Follow its allowed actions and recommended
action. Stop only when the selected scope is complete, Mosaico reports a genuine blocker, or a human
decision is required. Mosaico decides which member a record belongs to from the run; do not try to work that out
yourself. Only Owners and Admins can use Outreach.
