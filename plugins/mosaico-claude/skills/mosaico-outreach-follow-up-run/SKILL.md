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
2. Call `outreach_start_run` with that URL as `observedLinkedInProfile` and the intent: `check_follow_ups` for checking, `send_approved_follow_ups` for sending. When doing both, start a separate run for each scope.
3. Keep the returned `runId` and pass it on every `outreach_get_day` or `outreach_get_follow_ups`
   read and on every `outreach_save_lead`, `outreach_update_lead`, `outreach_record_message`,
   `outreach_deposit_conversation`, `outreach_mark_message_sent`, `outreach_record_delivery_block`,
   `outreach_record_connection_evidence` and `outreach_record_connections_snapshot` call. Never pass `ownerUserId` on
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
   `outreach_record_delivery_block`, `outreach_record_connection_evidence` and
   `outreach_record_connections_snapshot`, open the Me page again
   and pass the profile you see then as `observedLinkedInProfile`.
   Or run the whoami script again and pass its output exactly as returned as `identityEvidence` on the write.
   A thread deposit needs `identityEvidence`, not a reading: Mosaico takes the owner's member id from it.
6. If an Owner or Admin asks to run for a colleague, pass that member's id as `onBehalfOfMemberId` on
   `outreach_start_run` only. The LinkedIn account must then be that colleague's.

If `outreach_save_lead` or `outreach_deposit_conversation` reports that the profile already exists
under another owner, stop and show the person the owner, Lead and status. Re-send with
`acknowledgeProfileOnOtherOwner: true` only after the person decides to; never set it yourself.

## Script output goes to Mosaico exactly as returned

Every approved script returns an `integrity` field, `{ algorithm: "fnv1a32", digest }`, computed in the
page over everything else it returns (the connections script also seals each page). Wherever a script's
output goes to Mosaico (`identityEvidence` from the whoami script, connection evidence, the pages of the
connections list, `threadEvidence`, `sentInvitationEvidence`), pass it exactly as returned: every field,
`integrity` included, never retyped, trimmed, reformatted, translated or "fixed". Mosaico recomputes the
digest and refuses an altered copy with `evidence-altered`: nothing is stored, and the recommended action
is `recapture`. Then run the approved script again and pass the new output unchanged. Never edit the copy
to make it pass.

## No pressure, and what Mosaico refuses

A no ends the Lead. Never draft a follow-up for a Lead who said no, never ask twice, never try to change
the Lead's mind. Mosaico enforces this, and it also stops us chasing our own silence:

- `follow-up-declined`: the Lead's latest message said no. Mosaico has moved the Lead to Drop and refuses
  new drafts for it.
- `follow-up-awaiting-reply`: the latest message sent on the Lead is ours and it is not the invitation
  note. Our own unanswered message blocks a new one. `outreach_get_follow_ups` gives such a Lead
  `followUpReason` `awaiting-reply` and never lists it as actionable. `connection-accepted-no-reply` now
  means only that the invitation note is the last message, or that nothing has been sent yet.
- `follow-up-thread-unread`: Mosaico has not read this Lead's thread (see `thread-not-found-in-window` in
  **Capture the thread**). It refuses drafts for the Lead until its thread is read.

When `outreach_record_message` is answered with one of these codes as skipped or blocked, never work around
it: record what Mosaico returned, skip the Lead and continue with the next one. Do not reword the draft,
do not try another kind of message and do not ask the person to override it.

## Repair drafts first

Each time Mosaico stores a thread or an outcome, it checks every unsent draft on that Lead against these
rules and discards the ones that no longer qualify. The deposit answer lists them as
`draftsDiscarded: [{ messageId, reason }]`, where the reason is `follow-up-declined`,
`follow-up-awaiting-reply` or `follow-up-thread-unread`. Mosaico also re-derives a stored thread from the
evidence: who sent each message and which message is the invitation note, replacing earlier by-eye
records. A thread deposited from the script is the truth.

When `outreach_get_follow_ups` returns the recommended action `repair_drafts`, it also returns
`repairSuggestions`: the Leads that hold unsent drafts which break the rules given what Mosaico has
stored, each with its reasons. Before drafting anything new, and before sending any approved draft, visit
each Lead in `repairSuggestions` first: run **Capture the thread** for it and deposit with `outcome`, then
reread `outreach_get_follow_ups`. Report in plain words how many drafts Mosaico discarded, for which
Leads and for which reasons.

## Check for new follow-ups

1. Work across all dates and read `outreach_get_follow_ups` with the `runId`. When the recommended
   action is `capture_connections`, run **Capture recent connections** once, then reread. When the
   recommended action is `verify_connection`, Mosaico lists the Leads whose connection is unknown or unverified in
   `unverifiedLeads`, each with its profile URL: for each one run **Capture connection evidence**, then
   reread `outreach_get_follow_ups`. When it is `repair_drafts`, do **Repair drafts first**, then reread.
   Never guess a connection and never skip to drafting for a listed Lead.
2. For each returned Lead, read its thread from LinkedIn's data: run **Capture the thread** with the
   Lead's public identifier and pass the output exactly as returned as `threadEvidence` to
   `outreach_deposit_conversation`, with fresh `identityEvidence` and the `outcome` of the Lead's latest
   message. The script needs no particular page.
   Do not search LinkedIn lists for Leads, and never read a LinkedIn list or button to decide whether a
   Lead is connected.
3. Only when the script cannot run, use the by-eye fallback in **Capture the thread** for that Lead, and
   say so in the report.
4. Do not compare the thread with stored history or decide which reply is newer; Mosaico owns identity
   matching, chronology, direction, follow-up state, blockers and allowed actions.
5. Save every missing follow-up reply through `outreach_record_message` as an outbound follow-up
   draft with `sentAt` null, only for a Lead Mosaico permits it for. A Lead who said no, or whose latest
   sent message is ours and unanswered, gets no draft (see **No pressure, and what Mosaico refuses**).
6. If the person opted into connected Leads without replies, also save missing follow-up drafts for
   those Leads when Mosaico permits `draft_follow_up` (Mosaico permits it only for a Lead it lists as
   verified). Use their visible profile, stored conversation
   context and assigned Agent instructions; do not invent a reply from the Lead.
7. Continue drafting when Mosaico permits `draft_follow_up` even if a separate historical
   `message.kind` sorting issue remains.
8. Do not approve or send any message in this scope.
9. In the final report say how many drafts Mosaico discarded (`draftsDiscarded`), for which Leads and
   for which reasons, how many Leads each outcome (declined, interested, neutral) was recorded for, and
   which Leads were "thread not found in window", each in plain words.

## Send approved drafts

1. Work only on exact outbound follow-up messages whose current Mosaico status is already Approved.
   Messages Mosaico returns as blocked are never sent; do not retry them. When `outreach_get_follow_ups`
   recommends `repair_drafts`, do **Repair drafts first** before sending anything.
2. Never approve, rewrite or substitute a message. If the approved body does not exactly match the
   body about to be sent, stop for that message and report the blocker.
3. Open the conversation directly through the `linkedInMessageUrl` Mosaico returns when present;
   otherwise open the Lead's profile and use Message. If the conversation cannot be opened or the
   person cannot be messaged, call `outreach_record_delivery_block` with `reason: cannot-message` and
   continue with the next message. Recording an outcome is not a blocker.
4. Send through the authenticated LinkedIn browser: type the approved message and send it. Do not judge
   from the screen whether it worked; LinkedIn's data says so, in the next step.
5. **Confirm the send from data.** Straight after the send, run the approved thread script again for the
   same Lead (**Capture the thread**, steps 1 to 4) and call `outreach_mark_message_sent` with the exact
   Lead and Message identities, the exact send time when LinkedIn exposes it, otherwise null, the script's
   output exactly as returned (`integrity` included) as `threadEvidence`, fresh `identityEvidence` and the
   `runId`. Mosaico reads the
   thread: it accepts the mark only when the newest message from you in it is the approved message,
   delivered after your check before the send. Report its answer in plain words. Do not call
   `outreach_deposit_conversation` for this capture; the mark records it.
6. If Mosaico answers `send-not-confirmed`, LinkedIn's data does not show the message: it did not go out.
   Do not retype it and do not mark it sent. Retry the send once, run the thread script again and pass
   its output again as `threadEvidence`. If Mosaico answers `send-not-confirmed` again, call
   `outreach_record_delivery_block` with `reason: cannot-message` and continue with the next message.
   For `send-evidence-stale` or `send-evidence-malformed`, the capture was unusable: run the script again
   once and pass it again; if it is still refused, leave the message Approved, list it as skipped with
   the code and continue. For `send-evidence-lead-mismatch`, run the script for this Lead's own public
   identifier.
7. Never mark a message sent from the screen alone. Only when the script cannot run (the script file is
   missing, the gate refuses it, or LinkedIn stops answering it), and the message visibly appears in the
   thread, call `outreach_mark_message_sent` without `threadEvidence`: Mosaico records it as a reading of
   the screen and answers `send-proof-missing`. Say so in the final report, with each Lead.
8. Continue until every currently approved follow-up draft is sent or recorded, or Mosaico reports a
   genuine blocker (Mosaico, sign-in or LinkedIn failure). One Lead that cannot be messaged never
   stops the run.
9. In the final report list recorded outcomes separately from sends and blockers, each with its
   Lead and reason, and count the sends confirmed from data separately from any marked by screen.

## Capture the thread

Whether a person replied, when, and who said what, is a fact in LinkedIn's own messaging data, not on the
page. This procedure carries that data to Mosaico unchanged; Mosaico reads it, works out each message's
direction and time itself, and decides what is a reply. Never read a thread by eye when the script can
run, never type messages next to it, never decide that a reply arrived and never decide a message's
direction.

The capture is the plugin's thread script: one approved script, shipped at
`browser/linkedin-thread-messages.js` inside the installed plugin, run through a one-line run directive in the signed-in
LinkedIn page by the built-in browser pane, under the same rules as **Capture connection evidence**. It
sends LinkedIn's own session and CSRF material to LinkedIn only and never returns it. It finds the
one-to-one conversation between the signed-in account and the Lead by paging LinkedIn's primary-inbox
conversation list with LinkedIn's own paged query (up to 8 pages, about 160 conversations; message requests
and the Other tab are not searched) and returns the participants' member ids and the messages oldest
first, each with only its delivery time, its sender and its text, plus `coverage` (`complete` or
`page-limit`), `pagesRead` and the `integrity` seal. Names and every other field are dropped. It runs in
Claude's built-in browser pane only: the Chrome extension cannot run it, and Codex cannot either.

Run these steps in order for one Lead:

1. Run the approved whoami script, as in **Start the run**, and keep its output exactly as returned as
   `identityEvidence` for the deposit. It goes stale: when the output you hold is older than 8 minutes,
   run it again.
2. Run the script with the browser pane's `javascript_tool` on any linkedin.com page by sending one line as the
   whole script: `// mosaico run linkedin-thread-messages.js PUBLIC_IDENTIFIER=<public identifier>`, where the
   identifier is the part of the Lead's `linkedInProfileUrl` after `/in/`, with no trailing slash or query,
   without quotes. The plugin's gate inserts the approved script; never print, retype, paraphrase, reorder,
   shorten or extend it. The queries inside it are the ones known to work today: if LinkedIn stops
   answering them, stop and report that; do not guess others.
   Fallback, only when the gate refuses the directive: print the approved script without changing it,

   ```bash
   cat "${CLAUDE_PLUGIN_ROOT:-$(dirname "$(dirname "$(find ~/.claude/plugins -path '*/mosaico-claude/browser/linkedin-thread-messages.js' -print -quit)")")}/browser/linkedin-thread-messages.js"
   ```

   then run the printed script with the browser pane's `javascript_tool` on any linkedin.com page, changing
   only the value on its first line to the Lead's public identifier, in quotes. Do not paraphrase, reorder,
   shorten or extend it: the gate refuses anything else.
4. If `signedIn` is false, the pane is not signed in to LinkedIn: stop the step and report it. If `status`
   is not 200 or `state` is `error`, the script could not read the thread: use the by-eye fallback below for
   this Lead.
5. Judge the outcome of the Lead's latest message with **Judge the Lead's latest message** below.
6. Straight away (the capture is refused when it is more than 10 minutes old), call
   `outreach_deposit_conversation` with `threadEvidence` (the script output exactly as returned, `integrity`
   included, `coverage` and `pagesRead` too), `identityEvidence`, `runId`, `personName`, `publicLinkedInUrl`
   (the Lead's profile URL) and `outcome`. Never pass `messages` with it; Mosaico ignores them.
7. Report Mosaico's answer in plain words:
   - stored, with its `threadStatus`, the outcome it recorded and any `draftsDiscarded` (count them for the
     final report);
   - blocked `outcome-required`: the thread holds a message from the Lead and no outcome was given. Nothing
     was stored. Add the outcome and deposit again;
   - skipped `no-conversation`: LinkedIn's primary inbox held no conversation with this person (`coverage`
     was `complete`); nothing is concluded about replies; continue with the next Lead;
   - skipped `thread-not-found-in-window`: the 8 pages did not reach this person's conversation, so nothing
     is concluded. Mosaico marks the Lead's thread as unread, refuses drafts for it (`follow-up-thread-unread`)
     and discards drafts that were waiting. Report the Lead as "thread not found in window" and continue with
     the next Lead. Never call it "no conversation", and do not use the by-eye fallback for it unless the
     person asks;
   - `evidence-altered`: see **Script output goes to Mosaico exactly as returned**; run the script again and
     pass the new output unchanged;
   - any other blocker code: follow the action Mosaico names (run the script again once, or continue with
     the next Lead), and do nothing else.

When the script cannot run (the script file is missing, the gate refuses it, the pane cannot be signed in,
or LinkedIn stops answering it), the by-eye deposit is the fallback for that Lead only: open
`navigation.messageUrl` (the profile and Message when there is none), deposit the complete visible
conversation oldest to newest through `outreach_deposit_conversation` as `messages`, with
`observedLinkedInProfile` or `identityEvidence`, the conversation's URL as `linkedInMessageUrl` and the
`outcome` of the Lead's latest message (the same judgment, under the same checklist), and say
in the final report which Leads were read by eye and why. Mosaico stores such a thread as a reading, not as
evidence. This fallback is for a script that cannot run, not for a Lead whose answer was
`thread-not-found-in-window`.

### Judge the Lead's latest message

Mosaico needs one judgment from you for every thread that holds at least one message from the Lead:
`outcome`, one of `declined`, `interested` or `neutral`. It is your judgment of the Lead's latest message
from the Lead (the newest inbound message in the thread), under this checklist, in whatever language the
Lead writes. Without it the deposit is refused with `outcome-required` and nothing is stored.

- `declined`: the latest message says no in any form: not interested, no thanks, not now or not for us, we
  already have this covered and do not need it, stop, remove me, do not contact me again, or hands the
  matter off with a clear refusal.
- `interested`: the Lead says yes or shows real interest: asks for details, pricing, a call or a demo,
  proposes a time, asks who else to involve, or agrees to talk.
- `neutral`: anything else: thanks, greetings, a polite acknowledgement, an out-of-office, a question
  unrelated to buying, a message that only repeats our own text, or a message that neither refuses nor
  invites.

Judge only the Lead's latest message, never an older one, never our own words and never the Lead's
silence. If it is a refusal in any form, or you doubt whether it is a refusal, choose `declined`: we never
pressure. A no ends the Lead. Never draft a follow-up for a Lead who said no, never ask twice, never try to
change the Lead's mind.

Mosaico stores the outcome with the message it rests on and the time. `declined`: Mosaico moves the Lead
to Drop (reason "declined on <date>"), discards every unsent draft on the Lead and refuses new drafts
(`follow-up-declined`). `interested`: Mosaico marks the Lead Warm. `neutral`: nothing more happens.

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
   is the last segment of the profile URL's path (the part after `/in/`, with no trailing slash or query),
   without quotes. The plugin's gate inserts the approved script; never print, retype, paraphrase, reorder,
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
   `status` is not 200 or `entries` is empty, stop: leave the Lead unverified, list it as skipped and
   continue with the next Lead.
5. Call `outreach_record_connection_evidence` with the script's whole output exactly as returned
   (`status`, `signedIn`, `capturedAt`, `profileIdentifier`, `entries` and `integrity`), plus `profileUrl`
   (the Lead's `linkedInProfileUrl`), `leadId`, the `runId` and the identity evidence (`identityEvidence`
   from the whoami script, or `observedLinkedInProfile`). Report Mosaico's answer in plain words: connected, invite-pending,
   not-connected, or the blocker it returned. If Mosaico refused or the capture gave it nothing usable,
   leave the Lead unverified, list it as skipped and continue; follow any action Mosaico names, and do
   nothing else.

When the capability is unavailable (the script file is missing, the gate refuses it, or the pane cannot be
signed in), do not work around it. Leave the Lead unverified, note in the report only what the LinkedIn
page visibly shows (a Message, Connect or Pending button) for the person to read, never record that as a
connection state, and continue with the next Lead or stop the step and report it.

## Capture recent connections

Whether an invitation was accepted is a fact in LinkedIn's own list of your connections, newest first,
not on a profile's buttons. This procedure carries that list to Mosaico unchanged; Mosaico matches it to
the owner's own Leads and decides who accepted. Never compare names, never decide who accepted and never
choose where to stop: the script stops by itself.

Run it once per run, before drafting, when the read of `outreach_get_follow_ups` returns the recommended
action `capture_connections`. It is not repeated for each Lead.

The capture is the plugin's connection-evidence capability, for the same reasons and under the same rules
as **Capture connection evidence**: one approved script, shipped at `browser/linkedin-recent-connections.js`
inside the installed plugin, run through a one-line run directive in the signed-in LinkedIn page by the built-in browser pane.
It returns each page's list order plus only the fields Mosaico's matcher reads; names and every other field
are dropped, and no session or CSRF material ever leaves the page.

Run these steps in order:

1. Open LinkedIn's Me page and read the profile URL of the signed-in account. This is
   `observedLinkedInProfile`.
   Or run the approved whoami script, as in **Start the run**, and pass its output exactly as returned as
   `identityEvidence` to `outreach_start_run`. If the script is unavailable, read the Me page.
2. Open any LinkedIn page in the built-in browser pane.
3. Run the script with the browser pane's `javascript_tool` by sending one line as the whole script:
   `// mosaico run linkedin-recent-connections.js STOP_AT=<number>`, where the number is the
   `stopAtCreatedAt` that `connectionsCapture` returned in `outreach_get_follow_ups` (or `0` when it returned
   none), as a plain number. The plugin's gate inserts the approved script; never print, retype, paraphrase,
   reorder, shorten or extend it. The list address inside it is the one known to work today: if LinkedIn
   stops answering it, stop and report that; do not guess another.
   Fallback, only when the gate refuses the directive: print the approved script without changing it,

   ```bash
   cat "${CLAUDE_PLUGIN_ROOT:-$(dirname "$(dirname "$(find ~/.claude/plugins -path '*/mosaico-claude/browser/linkedin-recent-connections.js' -print -quit)")")}/browser/linkedin-recent-connections.js"
   ```

   then run the printed script with the browser pane's `javascript_tool`, changing only the value on its first
   line to that number. Do not paraphrase, reorder, shorten or extend it: the gate refuses anything else.
4. If `signedIn` is false, the pane is not signed in to LinkedIn: stop the capture and report it. If
   `status` is not 200 or `pages` is empty, report that the connections list could not be read and
   continue with the rest of the run. Never guess.
5. Save the script output exactly as returned (for example to a file in a temporary folder), so a page
   can be sent again unchanged. The script still returns every page in one output; Mosaico takes them one
   page per call. Call `outreach_record_connections_snapshot` once per page, in index order, with
   `runId`, `identityEvidence` (or `observedLinkedInProfile`), `capturedAt`, `snapshotId` (the script's
   `capturedAt` string, the same on every call), `pageIndex` (0-based), `pageCount` (`pages.length`)
   and `page` (that one entry of `pages`, exactly one `{elements, entries, integrity}` object, `integrity`
   included, exactly as returned). Mosaico checks each page's own seal. Never merge, trim, reorder, retype
   or edit a page. The identity evidence goes stale: when the whoami output you hold
   is older than 8 minutes, run the whoami script again before the next call and pass the new output.
   The one-call form (`capturedAt` and the whole `pages` list in a single call, every page with its
   `integrity`) is still accepted, but use it only for a short list that fits in one call.
6. Read each answer. `page_recorded` means Mosaico has that page; if it lists `missing` indexes, submit
   exactly those pages next, in index order, from the saved output. The last page ends with
   `connections_recorded`: report in plain words how many Leads Mosaico matched. If Mosaico refused with
   `snapshot-expired`, or with `evidence-altered` for a page, run the script again (step 3) and submit the
   new output from page 0. If it refused
   for any other reason, report the blocker it returned, change nothing more and continue with the rest
   of the run. Then reread `outreach_get_follow_ups`.

If a run stops half-way, Mosaico keeps the pages it already has. When `outreach_get_follow_ups` returns
`connectionsCapture.pending`, it names the half-submitted snapshot (its `snapshotId`, `pageCount` and
missing page indexes). Submit its missing pages first, in index order, from the saved output of that capture
(same `snapshotId`, same `pageCount`). If that output is no longer available, run the script again and
submit the new output as a new snapshot.

When the capability is unavailable, do not work around it: report that the connections list was not
captured, record nothing, continue with the rest of the run and reread `outreach_get_follow_ups`.

## Both

1. Complete **Check for new follow-ups** first.
2. Reread the current Mosaico state. When it recommends `repair_drafts`, do **Repair drafts first**.
3. Complete **Send approved drafts** only for messages that were already human-approved. Never
   approve a newly created draft automatically.

## One pass per thread

The scope for a scheduled daily run: each LinkedIn conversation is opened once, and replies are
handled before anything else is sent.

1. Read `outreach_get_follow_ups` with the `runId`. When the recommended action is
   `capture_connections`, run **Capture recent connections** once, then reread. Work through every
   returned Lead in order. When the recommended action is `verify_connection`, run **Capture connection evidence** for each Lead in
   `unverifiedLeads` first and reread; never guess a connection and never draft for a Lead Mosaico
   still lists as unverified. When it is `repair_drafts`, do **Repair drafts first** and reread.
2. For each Lead, run **Capture the thread** with the Lead's public identifier, in the built-in browser
   pane, and pass the output exactly as returned as `threadEvidence` to `outreach_deposit_conversation`,
   with fresh `identityEvidence` and the `outcome` of the Lead's latest message. If Mosaico reports
   `returnedToDraft`, that Lead's approved follow-up is now a draft because a new reply arrived: do not
   send it. If the Lead's outcome was `declined`, send nothing and draft nothing for it. If the answer is
   `thread-not-found-in-window`, report the Lead as "thread not found in window" and continue with the next
   Lead. Use the by-eye fallback in **Capture the thread** only when the script cannot run, and say so in
   the report.
3. Reread the Lead's state. If Mosaico still lists an approved outbound follow-up for it, open
   `navigation.messageUrl` directly (the profile URL when there is no thread yet). If that URL opens a
   different person's conversation, do not send: call `outreach_update_lead` with
   `linkedInMessageUrl: null` and `reason: wrong-person`, then open the Lead's profile and use
   Message to find the right thread; if it cannot be found, continue with the next Lead.
4. Send the approved follow-up exactly as approved, then confirm it from data: run **Capture the thread**
   steps 1 to 4 again for the Lead and call `outreach_mark_message_sent` with the script's output exactly as
   returned as `threadEvidence` and fresh `identityEvidence`, as in **Send approved drafts**, steps 5 to 7. If Mosaico
   answers `send-not-confirmed`, do not retype: retry the send once, run the script again, and if it is not
   confirmed again call `outreach_record_delivery_block` with `reason: cannot-message`. Never mark a
   message sent from the screen alone unless the script cannot run, and then say so in the report.
5. If the conversation cannot be opened or the person cannot be messaged, call
   `outreach_record_delivery_block` with `reason: cannot-message` and continue with the next Lead.
6. Save every missing follow-up draft Mosaico permits through `outreach_record_message` with
   `sentAt` null. Mosaico decides which Leads are due, including an accepted invitation without a
   reply, and permits a draft only for a Lead it lists as verified. Never approve a draft; never send a
   draft created in this run. If Mosaico refuses a draft (`follow-up-declined`, `follow-up-awaiting-reply`,
   `follow-up-thread-unread`), record what it returned and continue; never work around it.
7. Continue until every Lead has been handled or Mosaico reports a genuine blocker (Mosaico,
   sign-in or LinkedIn failure). One Lead that fails is recorded and skipped, never a halt.
8. Report sends (confirmed from data versus marked by screen), recorded outcomes (declined, interested,
   neutral), drafts written, drafts Mosaico discarded (`draftsDiscarded`, with each Lead and reason), Leads
   whose thread was "thread not found in window", Leads left unverified, and skipped Leads with reasons,
   separately.

For every scope, Mosaico is the workflow authority. Follow its allowed actions and recommended
action. Stop only when the selected scope is complete, Mosaico reports a genuine blocker, or a human
decision is required. Mosaico decides which member a record belongs to from the run; do not try to work that out
yourself. Only Owners and Admins can use Outreach.
