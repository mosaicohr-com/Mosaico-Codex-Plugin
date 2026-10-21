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

Treat the answer as an additional drafting scope, not permission to approve or send those drafts. A scheduled run does not ask these questions: the **Follow-up routine** section at the end of this skill carries its answers.

## While the connector is acting as a member

Outreach runs only as the person themselves and never inside a customer. If an Outreach call is refused with
"Outreach and incident tools are not available while your connector is acting as a member of another
organisation. End the session first.", the connector is acting as a member of a customer's organisation. Stop
there. Report that sentence word for word, the step you reached and anything done that Mosaico did not
record. Do not try the call again, do not use another tool or the browser to get round it, and do not end the
session yourself: ending it is the person's choice, in the Mosaico web console or by asking you. A scheduled
run reports and stops the same way.

If a call is refused with a sentence that begins "Your session as" and says "so the task stopped", the person
ended the acting session while you worked. Stop. Do not repeat the call and do not carry on as yourself.
Report that sentence word for word, the step you reached and anything done that Mosaico did not record. Do
not continue as the operator until the person gives a new instruction. A scheduled run reports and stops the
same way.

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
2. Call `outreach_start_run` with that URL as `observedLinkedInProfile` and the intent: `check_follow_ups` for checking, `send_approved_follow_ups` for sending. When doing both, start a separate run for each scope. The scheduled **Follow-up routine** starts one run with intent `follow_up_pass` instead and works it through **The follow-up queue (intent `follow_up_pass`)**.
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

## Repair is a separate routine

The Follow-up run is daily work and does not clear the backlog. Mosaico caps the verification list at 20
Leads per run, oldest invitation first (`verifyCap` on `outreach_get_follow_ups`); the rest are counted as
`summary.deferredToRepair`, and `repairNeeded` counts what the Repair routine would work, per group and in
total. Work only what `outreach_get_follow_ups` lists, and never go looking for more. When its `notes` hold
`repair-recommended`, do not work the backlog in this run: end the final report with the line "Repair needed:
n items, run the Repair routine", where n is `repairNeeded.total`. In a `follow_up_pass` run the follow-up queue carries the
repairs Mosaico can decide for its own Leads (see **The follow-up queue**), and the Repair routine works only the backlog outside
that queue.

## Missing invitation drafts are not follow-up work

`outreach_get_follow_ups` also returns `draftsToWrite`: the placed Leads of this owner that have no invitation draft,
with the one recommended action that writes them. The follow-up scopes of this skill do not act on it. The Send invitations
routine of the invite-run skill writes those drafts, and a Source leads run never does.

## Check for new follow-ups

1. Work across all dates and read `outreach_get_follow_ups` with the `runId`. When the recommended
   action is `capture_connections`, run **Capture recent connections** once, then reread. When the
   recommended action is `verify_connection`, Mosaico lists the Leads whose connection is unknown or unverified in
   `unverifiedLeads`, each with its profile URL: for each one run **Capture connection evidence**, then
   reread `outreach_get_follow_ups`. The list may name Leads with the reason `colleague-verified-needs-own-check`
   first: a colleague's sourcing run saved them as not connected from its own check, and your own capture comes first.
   Verify them from your own pane like any other unverified Lead. When it is `repair_drafts`,
   do **Repair drafts first**, then reread. Never guess a connection and never skip to drafting for a listed Lead.
2. For each returned Lead, read its thread from LinkedIn's data: run **Capture the thread** with the
   Lead's script identifier and pass the output exactly as returned as `threadEvidence` to
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
   sent message is ours and unanswered, gets no draft (see **No pressure, and what Mosaico refuses**). A Lead
   whose latest message asks to be contacted later is booked for that day instead of drafted for now (see
   **Book a later touch**), and a Lead Mosaico lists as booked for a later day is left alone.
6. If the person opted into connected Leads without replies, also save missing follow-up drafts for
   those Leads when Mosaico permits `draft_follow_up` (Mosaico permits it only for a Lead it lists as
   verified). Use their visible profile, stored conversation
   context and assigned Agent instructions; do not invent a reply from the Lead.
7. Continue drafting when Mosaico permits `draft_follow_up` even if a separate historical
   `message.kind` sorting issue remains.
8. Do not approve or send any message in this scope.
9. In the final report say how many drafts Mosaico discarded (`draftsDiscarded`), for which Leads and
   for which reasons, how many Leads each outcome (declined, interested, neutral) was recorded for,
   which Leads were "thread not found in window", and the bookings made, changed or cleared and the date
   refusals (see **Book a later touch**), each in plain words.

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
one-to-one conversation between the signed-in account and the Lead, first by LinkedIn's own messaging search by the
Lead's name (inbox, spam and archive; up to 3 pages) and, when that finds nothing, by paging LinkedIn's primary-inbox
conversation list with LinkedIn's own paged query (up to 8 pages, about 160 conversations; message requests
and the Other tab are not paged), and returns the participants' member ids and the messages oldest
first, each with only its delivery time, its sender and its text, plus `coverage` (`complete` or
`page-limit`), `lookup` (`search`, `list` or `none`), `pagesRead`, `searchPagesRead` and the `integrity` seal. When the
Lead's stored identifier is out of date (an old vanity, or an id LinkedIn no longer matches), it finds the conversation
by the Lead's name among the search results instead, and says so: `matchBasis` is `identifier` or `name`, with the
matched person's `memberUrn`, `resolvedIdentifier` and `displayName`, and the `requestedName` it was given. Mosaico checks
that match itself. Every other field is dropped. It runs in
Claude's built-in browser pane only: the Chrome extension cannot run it, and Codex cannot either.

Run these steps in order for one Lead:

1. Run the approved whoami script, as in **Start the run**, and keep its output exactly as returned as
   `identityEvidence` for the deposit. It goes stale: when the output you hold is older than 8 minutes,
   run it again.
2. Run the script with the browser pane's `javascript_tool` on any linkedin.com page by sending one line as the
   whole script: `// mosaico run linkedin-thread-messages.js PUBLIC_IDENTIFIER=<public identifier> LEAD_NAME=<the Lead's name>`, where the
   Lead's name is the name Mosaico holds for the Lead, as it reads, without quotes (leave out any double quote or backslash in it), and the identifier is the Lead's `scriptIdentifier` from the Mosaico read when it is present (a member id or a public identifier, whatever Mosaico supplies), otherwise the part of the Lead's `linkedInProfileUrl` after `/in/`, with no trailing slash or query,
   without quotes. This is whatever stands there: a name such as `jane-doe`, or an id that starts with `ACoAA`. Use it as it is; do not look the Lead up or swap one for the other. The plugin's gate inserts the approved script; never print, retype, paraphrase, reorder,
   shorten or extend it. The queries inside it are the ones known to work today: if LinkedIn stops
   answering them, stop and report that; do not guess others.
   Fallback, only when the gate refuses the directive: print the approved script without changing it,

   ```bash
   cat "${CLAUDE_PLUGIN_ROOT:-$(dirname "$(dirname "$(find ~/.claude/plugins -path '*/mosaico-claude/browser/linkedin-thread-messages.js' -print -quit)")")}/browser/linkedin-thread-messages.js"
   ```

   then run the printed script with the browser pane's `javascript_tool` on any linkedin.com page, changing
   only the value on its first line to the same identifier, in quotes, and the value on its second line to the Lead's name, in quotes. Do not paraphrase, reorder,
   shorten or extend it: the gate refuses anything else.
4. If `signedIn` is false, the pane is not signed in to LinkedIn: stop the step and report it. If `status`
   is not 200 or `state` is `error`, the script could not read the thread: its `errorStep` (`me`, `profile`,
   `conversations` or `messages`) and `status` say why, so name them in the report for this Lead, then use the
   by-eye fallback below.
5. Judge the outcome of the Lead's latest message with **Judge the Lead's latest message** below.
6. Straight away (the capture is refused when it is more than 10 minutes old), call
   `outreach_deposit_conversation` with `threadEvidence` (the script output exactly as returned, `integrity`
   included, `coverage`, `pagesRead`, `requestedIdentifier`, `requestedName`, `resolvedIdentifier`, `memberUrn`,
   `matchBasis` and `displayName` too, all unchanged), `identityEvidence`, `runId`, `personName`, `publicLinkedInUrl`
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
   - stored with `linkedDuplicate` and the note `duplicate-linked` (a `follow_up_pass` or `repair` run only): the
     person in the thread is the member id another active Lead of this owner stores, so Mosaico linked the two
     Leads inside the deposit and stored the conversation, the outcome and the reply on the kept Lead. Report the
     link in plain words (`linkedDuplicate`: `keptLeadId`, `aliasLeadId`, `basis` `member-id`, `draftsMoved`,
     `draftsDiscarded`, `declineCarriedOver`) and carry on with the kept Lead: a `delivery` in the same answer is
     about it. A later deposit of the same thread simply lands on the kept Lead. Never call
     `outreach_link_duplicate_leads` yourself (a follow-up pass may not);
   - blocked `thread-person-held-by-other-lead`: the person in the thread is already another Lead of this
     owner (two records of one person) and Mosaico could prove it only by a public identifier, or the run is not
     a `follow_up_pass` or `repair` run, so nothing was linked. The answer names the other Lead (`leadId` and
     `heldBy`: `leadId`, `basis`, `memberId`). Capturing again returns the same answer, so never capture again and
     never work around it. Its only allowed action is `continue_with_next_lead`: record the Lead in the
     report ("held twice; a person or the Repair routine links the two") and go on. Nothing was stored;
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

A message that asks to be contacted at a later time it names ("talk in January", "after the holidays", "next month", a named day)
is not a refusal, even when it begins with "not now": judge it `interested` or `neutral`, and book the day (see **Book a later
touch**). A "not now" with no time, or a "maybe someday", stays `declined`.

Judge only the Lead's latest message, never an older one, never our own words and never the Lead's
silence. If it is a refusal in any form, or you doubt whether it is a refusal, choose `declined`: we never
pressure. A no ends the Lead. Never draft a follow-up for a Lead who said no, never ask twice, never try to
change the Lead's mind.

Mosaico stores the outcome with the message it rests on and the time. `declined`: Mosaico moves the Lead
to Drop (reason "declined on <date>"), discards every unsent draft on the Lead and refuses new drafts
(`follow-up-declined`). `interested`: Mosaico marks the Lead Warm. `neutral`: nothing more happens.

## Book a later touch

Needs the Mosaico server release 20261013c or later. Some conversations ask to be picked up later: "talk in January", "after the
holidays", "next month", a named day. For those, the follow-up is booked for a day instead of being written for now. You propose the
day from the Lead's words; Mosaico owns everything after that. It checks the day against its own today in the owner's time zone,
holds the work until then and offers it first on that day. If Mosaico refuses `sendNotBefore` or `nextTouchOn` as an unknown
argument, the connector's tool list is stale or the release is not live: book nothing and write no draft for that Lead, report it,
and tell the person that Mosaico has to be updated or the Mosaico connector disconnected and connected again.

**A message that asks for a later touch.** Judge the Lead's latest message, never an older one and never our own words, after its
outcome (**Judge the Lead's latest message**), and only when that outcome is `interested` or `neutral`. It asks for a later touch
when it names a time to talk or to be written to that is not now: "talk in January", "after the holidays", "next month", "write to
me on the 14th". A bare "not now" with no time is a no, a Lead who said no is never booked, and if you doubt whether the message is
a no, it is one. If the words give no time you can name, book nothing and report the Lead with the words.

**The day.** Propose one calendar day, written YYYY-MM-DD, from the Lead's words, counted from the day the Lead wrote them (the
message's time in the stored conversation, in the owner's time zone). A named day is that day; for a period such as "January" or
"next month" take its first weekday. Never work out today from a clock: not the machine's, not the page's, and do not run `date`.
Mosaico alone knows today in the owner's time zone, and it returns it as `today` when it refuses a date. A bookable day is after
today and no more than 365 days ahead.

**Book it.** Mosaico's answer to the thread deposit decides which call to make, not your own reading of the Lead's state. This is the
one case in which a `draft` item's `recommendedCall` is not made exactly as given: it gets `sendNotBefore` added, or it is replaced by
the `outreach_update_lead` call below, and only as the deposit answer says:

1. The answer lists `draft_follow_up` among its allowed actions (a follow-up is due now): write the draft as stage `draft`
   describes, written for the day it will be sent, and add `sendNotBefore` with the day to that `outreach_record_message` call. It
   stays a Draft for a person to approve; once approved, Mosaico holds it until the day (reason `follow-up-scheduled`) and offers it
   first from that day.
2. The answer offers no draft, `followUpRuleViolations` holds nothing but `follow-up-awaiting-reply` (our own message is the
   latest), `delivery.state` is `none` and nothing was returned to Draft (`returnedToDraft`): write no draft. Call
   `outreach_update_lead` with the `leadId`, `changes` set to `nextTouchOn` with the day, and the `runId`. Mosaico offers no draft for
   the Lead before that day; from that day it offers it first (reason `next-touch-due`), also when our own message is the latest.
3. Anything else (another no-pressure refusal, a follow-up already written, an approval Mosaico holds or offers): book nothing,
   write nothing new, and report the Lead with the Lead's words. An approved follow-up Mosaico offers (`delivery.state`
   `deliverable`) is sent as approved: booking never holds back or changes a message a person approved.

**A date Mosaico refuses.** A day Mosaico does not accept writes nothing: the answer is blocked with one code, `date-invalid`,
`date-not-future`, `date-too-far` or `date-not-applicable` (the Message cannot carry a date), with `field`, `today`,
`earliestAllowed` and `latestAllowed`, the allowed actions `retry_with_valid_date` and `continue_with_next_lead`, and the
recommended action `retry_with_valid_date`. Follow `recommendedAction`: retry once, with a day the Lead's words still name that lies
between `earliestAllowed` and `latestAllowed`, worked out from the returned `today`. If their words name no such day (the day they
meant has passed, or is more than a year away), or the retry is refused too, or the code is `date-not-applicable`, take
`continue_with_next_lead`: write nothing more for this Lead and report the refusal with the Lead, the `field`, the code, the day
tried and the Lead's words. Never choose a day only to get past a refusal, never leave the date out to write the draft anyway, and
never try a third time.

**Booked work waits.** Mosaico lists work booked for a later day last in stage `held`, with `nextStep` `wait_for_scheduled_day`,
`notBefore` and `scheduledReason` `scheduled` (a dated approval, reason `follow-up-scheduled`) or `next-touch-scheduled` (a booked
Lead). It is not due and needs no person: never open, read, draft or send for it, and report it from `counts.scheduled`. A draft
written for a Lead booked for a later day is skipped with `next-touch-scheduled` (with `notBefore`), and a dated approval answers
`draft-already-exists` with the recommended action `continue_with_next_lead` and `existingMessage.sendNotBefore`: both mean the Lead
is already booked, so record it, write nothing and go on. On its day (`scheduledReason` `scheduled-due` or `next-touch-due`) the
item is first in its stage and is worked like any other, with no date, because the follow-up is due now. Do not book it again from
the same message, only from something newer the Lead has written.

**A new reply on a booked Lead.** A reply before the booked day does not clear the booking; you decide whether it still stands.
When a thread deposit shows a Lead with a booking (the note `next-touch-scheduled` with `notBefore`), judge the Lead's latest
message once more against the booked day. If it names another time ("make it March"), move the booking: `outreach_update_lead` with
the new `nextTouchOn`. If it asks for contact now or takes the request back, clear it: `nextTouchOn` `null`. If it says anything
else, or the same time again, leave the booking as it is. A no is `declined`: Mosaico drops the Lead, so leave the date. The same
date rules apply, and a refusal is handled as above. The day of a follow-up that is already written is a person's to move (Outreach,
the Follow Up card, "Follow up on or after"): a new reply returns an approved one to Draft, so report the Lead with the reply's
words and do not record the message again. A booking ends when a person or a run clears it, or when a follow-up is recorded as sent
on or after the booked day, which Mosaico clears in the same write; never clear it yourself after a send.

**The report** lists the bookings made (each Lead, the day and the Lead's words that asked for it), the bookings changed or cleared
(Lead, old and new day, why), the booked items waiting (`counts.scheduled`) and the date refusals (Lead, `field`, code, the day
tried, what was done).

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

Redirects (0.9.16). When LinkedIn has moved a person to a new public identifier, the page you opened follows the
redirect while the first profile query still fails (a 404, or an answer with no usable profile). The script then
asks once more with the identifier the page itself shows, only when that differs from the one it was given, and
never more than once. It never swaps identifiers silently: `requestedIdentifier` stays the value you gave it,
`resolvedIdentifier` is the identifier LinkedIn's answer names, and the two being different is expected after a
redirect. Pass both on exactly as returned; Mosaico keeps the old identifier as an alias of the Lead. Do not retry
the script yourself.

Gone profiles (0.9.17). When LinkedIn says the profile is not there, the script reports `status` 404 (410 when LinkedIn
says 410): also when its profile data call answered 200 with no profile on a page that is LinkedIn's own not-found page,
and a redirect retry never replaces a first 404 or 410. Mosaico gives up on a Lead at once on a 404 or 410, and counts a
200 with no profile only as a first failure. Pass the output exactly as returned; never correct `status`, never retry
the script and never decide yourself that a profile is gone.

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
   `status` is not 200, `state` is `error` or `entries` is empty, the script could not read the profile: still
   do step 5 with its output exactly as returned, so Mosaico records the failure against the Lead (it stops
   handing a Lead out after the same failure twice). Then leave the Lead unverified, list it as skipped with
   the script's `errorStep` and `status` (they say why) and continue with the next Lead.
5. Call `outreach_record_connection_evidence` with the script's whole output exactly as returned
   (`status`, `signedIn`, `capturedAt`, `state`, `errorStep`, `profileIdentifier`, `requestedIdentifier`,
   `resolvedIdentifier`, `memberUrn`, `entries` and `integrity`; none of them changed), plus `profileUrl`
   (the Lead's `linkedInProfileUrl`), `leadId`, the `runId` and the identity evidence (`identityEvidence`
   from the whoami script, or `observedLinkedInProfile`). Report Mosaico's answer in plain words: connected, invite-pending,
   not-connected, or the blocker it returned. If Mosaico refused or the capture gave it nothing usable,
   leave the Lead unverified, list it as skipped and continue; follow any action Mosaico names, and do
   nothing else.
6. A capture that could not read the profile is answered `blocked` with code `profile-capture-failed`, the
   action `continue_with_next_lead` and three extra fields: `profileCaptureFailures` (`count`, `lastAt`,
   `lastStatus`, `lastStep`), `givenUp` and `inToSort`. That is a record, not a stop: Mosaico has remembered the
   failure on the Lead (a 404 or 410 gives up at once, a 200 with no profile on the second failure, and a Lead
   given up is flagged in To sort and leaves the queue). Report the Lead with those fields in plain words,
   never capture the same Lead again in the same run, and continue with the next Lead.

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
2. For each Lead, run **Capture the thread** with the Lead's script identifier, in the built-in browser
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
   `follow-up-thread-unread`), record what it returned and continue; never work around it. A Lead whose
   latest message asks to be contacted later is booked for that day instead of drafted for now (see
   **Book a later touch**), and a Lead Mosaico lists as booked for a later day is left alone.
7. Continue until every Lead has been handled or Mosaico reports a genuine blocker (Mosaico,
   sign-in or LinkedIn failure). One Lead that fails is recorded and skipped, never a halt.
8. Report sends (confirmed from data versus marked by screen), recorded outcomes (declined, interested,
   neutral), drafts written, drafts Mosaico discarded (`draftsDiscarded`, with each Lead and reason), Leads
   whose thread was "thread not found in window", Leads left unverified, bookings made, changed or cleared,
   date refusals, and skipped Leads with reasons, separately.

For every scope, Mosaico is the workflow authority. Follow its allowed actions and recommended
action. Stop only when the selected scope is complete, Mosaico reports a genuine blocker, or a human
decision is required. Mosaico decides which member a record belongs to from the run; do not try to work that out
yourself. Only Owners and Admins can use Outreach.

## The follow-up queue (intent `follow_up_pass`)

Needs the Mosaico server release 20261013a or later. If `outreach_get_follow_up_queue` is missing from the connector's tools, or
`outreach_start_run` refuses the intent `follow_up_pass`, stop and report that Mosaico has to be updated or the Mosaico connector
disconnected and connected again in Claude's connector settings (Claude keeps its old tool list until then, so a new tool does not
appear before that). Booking a later touch and leaving booked work alone need 20261013c or later (see **Book a later
touch**).

The scheduled **Follow-up routine** starts its run with intent `follow_up_pass`: one pass that reads conversations, writes
drafts and sends the follow-ups that are already approved. The intent may deposit conversations, record messages (drafts),
mark a message sent, record delivery blocks, record connection evidence and connections snapshots, update Leads and end the
run. It may not save Leads, link duplicate Leads or withdraw invitations: Mosaico refuses those writes with
`run-intent-not-allowed`, so never attempt them.

**The working read.** Call `outreach_get_follow_up_queue` with the `runId`. It is lean and paged (`limit` 1 to 50, default 25;
`cursor` takes `nextCursor`), and it carries no conversations, no full Lead records and no Agents. It replaces
`outreach_get_follow_ups` as this run's working read: never read `outreach_get_follow_ups` in a `follow_up_pass` run (about
750 KB). Mosaico orders the work; never rebuild the order from other reads, reorder it or skip ahead. The answer holds
`counts`, `unverified`, `items`, `listed`, `skippedThisRun`, `nextCursor`, `next`, `completion`, `cap`, `blockers`,
`allowedActions`, `recommendedAction` and `notes`.

- `next` is the one thing to do now. Do it, then read the queue again. Do not walk `items` or `nextCursor` to decide what to do;
  they are for the report.
- `next.kind` `connections-capture` comes first when the owner's connections list is due: run **Capture recent connections**
  with `STOP_AT` set to `next.script.stopAtCreatedAt` (`0` when it is null) and submit the pages with `next.call`
  (`outreach_record_connections_snapshot`); `next.pending` names a half-submitted capture whose missing pages go first.
  Nothing else is worked before it.
- `next.kind` `lead` is one Lead in its earliest stage. Its fields: `leadId`, `personName`, `publicIdentifier`,
  `scriptIdentifier` (the first-line value of every approved script for this Lead), `profileUrl`, `agentId`, `stage`, `nextStep`,
  `reasons`, `repairGroup`, `messageUrl` with `messageUrlBasis` (`conversation`, `stored` or `profile`) and `messageUrlNote`,
  `recommendedCall` (`tool`, `arguments`, `supplyAlso`), on a draft a `readConversationCall`, and either `approvedMessage`
  (`messageId`, `body`) or `heldReason` (`messageId`, `reasons`). Make `recommendedCall` literally: its `tool` and `arguments`
  unchanged, plus what `supplyAlso` names. Never pick another tool or change an argument.
- `coveredByRun` is false for an item this run's intent cannot do; `next` never points at one, and the note
  `work-for-another-intent` counts them. Leave them for the run that can, and report the count.
- `unverified.state` is `pending-connections-capture` until the connections list is captured, and then `count` is null: report
  "not known until the connections list is captured", never `upperBound` as a number of unverified Leads. State `known` gives
  the real count.
- `repairGroup` says which Repair queue group an item stands in for: `addresses`, `declinedPending`, `mismatches`,
  `repairSuggestions` or `unverified`, and null for follow-up work that is not a repair. The Follow-up run makes every repair
  Mosaico can decide from evidence for the Leads in its own queue, so the Repair routine now works only the backlog outside
  this queue (plus duplicate pairs, which only Repair links): the Repair queue leaves these Leads out and counts them in
  `excludedAsFollowUpWork`. Do not look for repair work anywhere but in this queue.
- `skippedThisRun` lists `{ leadId, personName, code, reason }` for each Lead whose call in this run came back with an answer
  nothing in the run can change (`profile-capture-failed`, `profile-entry-missing`, `profile-mismatch`,
  `evidence-owner-mismatch`, `thread-person-held-by-other-lead`, `thread-owner-not-participant`, `no-conversation`,
  `thread-not-found-in-window`, `lead-not-active`, and `thread-lead-mismatch` the second time); `counts.skippedThisRun` counts
  them. Mosaico leaves those Leads out of `items` and `next` for the rest of the run, and `completion.stopReason` is
  `queue-empty` when only they are left. It is information for the report: never open, capture, deposit or draft for a skipped
  Lead again in this run. A later run offers the Lead again when it is still work.
- `notBefore` and `scheduledReason` are on every item. `notBefore` is the booked day that governs the Lead's follow-up (the
  unsent follow-up's `sendNotBefore`, else the Lead's `nextTouchOn`), null when none; `scheduledReason` is `scheduled`,
  `scheduled-due`, `next-touch-scheduled`, `next-touch-due` or null. Mosaico judges the day against its own today in the owner's
  time zone; never work it out yourself. Work booked for a later day sits last in stage `held` with `nextStep`
  `wait_for_scheduled_day` (reasons `follow-up-scheduled` or `next-touch-scheduled`), earliest day first: it is not due, needs no
  person and is never `next`. `counts.scheduled` counts those Leads for the report. A queue with only them left stops with
  `queue-empty`. On its day a dated item is first in its stage (`scheduledReason` `scheduled-due` or `next-touch-due`). How to book
  a day, and what to do with a new reply on a booked Lead, is in **Book a later touch**.

**The stages**, in the order Mosaico works them:

1. `fix-address` (`nextStep` `fix_address`, `repairGroup` `addresses`): the stored address is one LinkedIn has since redirected.
   Nothing on LinkedIn: make `recommendedCall` (`outreach_update_lead` with the new `linkedInProfileUrl`) with the `runId`. It
   comes before the profile is opened.
2. `drop-declined` (`drop_lead`, `declinedPending`): the Lead's recorded no is not applied yet. Nothing on LinkedIn: make
   `recommendedCall` (`outreach_update_lead` with `status: dropped`) with the `runId`, and do nothing else for this Lead: no
   thread read, no draft, no send.
3. `verify-connection` (`nextStep` `verify_connection`): open `profileUrl` and run **Capture connection evidence** with the
   Lead's `scriptIdentifier`; the call is `outreach_record_connection_evidence`. The profile checks Mosaico carries from its
   Repair queue for a listed Lead (`repairGroup` `addresses` or `unverified`) are in this stage. A `profile-capture-failed`
   answer is recorded and the run moves on (see that section, step 6); the Lead is never captured again in this run.
4. `read-thread` (`read_thread`): the Lead holds unsent drafts that break a rule or rest on a reply nobody judged (`repairGroup`
   `repairSuggestions`), or carries a history mismatch (`mismatches`). Run **Capture the thread**, judge the outcome with
   **Judge the Lead's latest message**, and make the deposit call. The deposit decides what is kept and reports
   `draftsDiscarded`. A decline found in a thread is recorded with `outcome: declined`, also for a Lead flagged
   `history-mismatch`: Mosaico accepts it there. Anything else on a flagged Lead is skipped by Mosaico and stays for a person
   in To sort; report it as skipped.
5. `send-approved` (`send_approved_follow_up`): send `approvedMessage.body` exactly as approved with **Send one approved
   follow-up** below, then mark it sent with the call in `recommendedCall`.
6. `rewrite-draft` (`nextStep` `rewrite_follow_up_draft`): an unsent follow-up draft that an Agent change returned to Draft
   (reasons `checklist-changed` or `instructions-changed`, or a draft never approved whose stored review no longer holds). It comes
   between `send-approved` and `draft`, before any new draft. The item carries `rewriteDraft` (`messageId`, `kind`, `body`, `reason`,
   `basis`, `returnedAt`, `sendNotBefore`), a `recommendedCall` that names the existing `messageId`, and a `readConversationCall`.
   Make `readConversationCall` first, the thread deposit as in stage 4, so the rewrite rests on the thread as it stands: the
   invitation actually sent is in it. Then call `outreach_get_agents` with no arguments once per run and use the Agent whose id is
   the item's `agentId`, and rewrite `rewriteDraft.body` into the first message to the person, written from that Agent's current
   `messageInstructions` and enabled `messagingChecklist`, from the Lead's stored profile and the conversation, without repeating the
   words of the invitation that was sent. Record it with `recommendedCall` (`outreach_record_message` with the existing `messageId`),
   plus the new `body`, a `checklistReview` with one pass or fail result for every enabled rule of the Agent's checklist, and the
   `runId`. Mosaico replaces the body and keeps the kind, the day and `sendNotBefore`, clears the returned flag and leaves the status
   Draft; it never creates a second unsent draft. Never approve or send it. If the thread shows the Lead declined, or a new reply
   arrived, the deposit decides what is kept; record what Mosaico returned and continue. `counts.rewrite` counts these items.
7. `draft` (`draft_follow_up`): replies first. Make `readConversationCall` (the same thread deposit as stage 4; its answer
   returns the stored conversation to write from), then write the draft with `outreach_record_message` as `recommendedCall`
   gives it. Call `outreach_get_agents` with no arguments once per run and use the Agent whose id is the item's `agentId`: write
   the `body` from that Agent's `messageInstructions`, the Lead's stored profile and the conversation, give a new
   `messageId` and a `checklistReview` with one pass or fail result for every enabled rule of the Agent's `messagingChecklist`,
   `sentAt` null and the `runId`. If Mosaico refuses the draft (`follow-up-declined`, `follow-up-awaiting-reply`,
   `follow-up-thread-unread`, `draft-already-exists`), record what it returned and continue; never work around it. Never
   approve a draft, and never send a draft written in this run. When the Lead's latest message asks to be contacted later, add
   `sendNotBefore` to the draft or book the Lead instead, as **Book a later touch** says. An item whose `scheduledReason` is
   `next-touch-due` is a booked touch whose day has come: write its draft as above, without a date.
8. `held` (`sort_in_application`): an approved follow-up this run cannot release. It is never `next`. Report it with its
   `heldReason`; a person sorts it in Outreach. Work booked for a later day is in this stage too, last, with `nextStep`
   `wait_for_scheduled_day`: it needs no person and nothing is done for it in this run (see **Book a later touch**).

**After a thread deposit, send in the same step.** The deposit answer carries `delivery { state, messageId, body, messageUrl,
reasons }`, judged by the same rule the queue uses. When `delivery.state` is `deliverable` and the recommended action is
`send_approved_follow_up`, send that approved follow-up right now with **Send one approved follow-up**, using
`delivery.messageId`, `delivery.body` and `delivery.messageUrl`. Do not reread the queue first and do not read
`outreach_get_follow_ups`; the thread was just read, so do not read it again before the send. When `delivery.state` is `held`,
send nothing and report its `reasons`. When it is `none`, there is nothing to send (a new reply returned the approval to
Draft, or a rule discarded it). A declined Lead gets nothing.

**A deposit that links two Leads.** In this run Mosaico links two Leads itself when the thread proves, by member id, that they
are one person: the deposit answer then carries `linkedDuplicate { keptLeadId, aliasLeadId, basis, draftsMoved, draftsDiscarded,
declineCarriedOver }` and the note `duplicate-linked`, and the conversation, the outcome and the reply are stored on the kept
Lead. Report the link and go on with the kept Lead (`keptLeadId`): its `delivery` is the one to act on, and the alias is not
worked again. Never call `outreach_link_duplicate_leads`; this intent may not. A thread whose person another Lead holds only
by an identifier is still refused with `thread-person-held-by-other-lead` (see **Capture the thread**): record it and continue.

**Send one approved follow-up.**

1. The text to send is `approvedMessage.body` or `delivery.body`, and the Message is the one with that `messageId`. Never
   approve, rewrite or substitute it. If it does not exactly match what you are about to type, stop for that message and
   report the blocker.
2. Open the item's `messageUrl` (after a deposit, `delivery.messageUrl`). When `messageUrlBasis` is `conversation` or `stored`
   it opens the full messaging page of that conversation. When it is `profile` (or the deposit's `messageUrl` is null and you
   opened the profile), no conversation is known: use the profile's Message button, and read `messageUrlNote`. LinkedIn's
   message window stays open over the profile page, so close any open message window before you navigate to the next profile
   and again after each send. If the URL opens a different person's conversation, send nothing: call `outreach_update_lead`
   with `linkedInMessageUrl: null` and `reason: wrong-person`, then use the Lead's profile and Message button; if that cannot
   reach the right thread, continue with the next item. If the conversation cannot be opened or the person cannot be messaged,
   call `outreach_record_delivery_block` with `reason: cannot-message` and continue.
3. Type the body and send it. Do not judge from the screen whether the typed text is complete or whether it went out: the
   typed text is proved by the post-send thread capture, not by sight. (A script that reads the compose box is deferred; this
   release has none, so do not look for one.)
4. Confirm it from data: run **Capture the thread** steps 1 to 4 again for the same Lead and call
   `outreach_mark_message_sent` as **Send approved drafts**, steps 5 to 7, describe (`threadEvidence` exactly as returned,
   fresh `identityEvidence`, the `runId`). Mosaico marks it sent only when the newest message from you in the thread is the
   approved message. `send-not-confirmed` is handled as those steps say: retry the send once, capture again, and if it is
   still not confirmed call `outreach_record_delivery_block` with `reason: cannot-message`.

**Stopping.** The run goes on while `completion.mustContinue` is true. When it is false, `completion.stopReason` says why:
`queue-empty` (nothing is left; also when only work booked for a later day, or skipped Leads, is left), `needs-a-person` (only
held items that need a person are left), `needs-another-intent` (what is left needs a run of another intent) or `blocked` (the run
cannot work the queue; read `blockers`). Stop on the first three by ending the run
with reason `complete`; on `blocked`, and on any run-level blocker (see **Start the run**, step 4), end it with reason
`blocked`, the `blockerCode` Mosaico gave and a note. One Lead that fails is recorded and skipped, never a halt; a Lead
whose call came back with an answer nothing in the run can change is left out of the queue and named in `skippedThisRun`, so do
not try it again in this run.

One pass per thread still holds: read each Lead's thread once in a run. The only second capture of a thread is the single one
that confirms a send.

## Follow-up routine

This is the Follow-up flow of Mosaico Outreach: connections and messaging. It works the follow-up queue Mosaico keeps (intent follow_up_pass): it captures the connections list when it is due, verifies the connections still unknown, reads the threads that need reading (the Leads who replied and the Leads who did not), writes the missing follow-up drafts and sends the follow-ups that are already approved, one pass per thread across all dates. It also makes the repairs Mosaico can decide from evidence for its own Leads: it fixes an address LinkedIn has redirected and drops a Lead who said no. When a conversation asks to be picked up later ("talk in January"), it books that day instead of drafting now (a day on the follow-up draft, or on the Lead when no draft is due yet) and leaves work booked for a later day alone until its day. It does not source, transfer or save Leads, never calls the link tool itself (Mosaico links a pair its thread deposit proves by member id), and does not write invitation drafts, send invitations or withdraw them; the Source leads, Send invitations and Withdraw stale invitations schedules do those. The Repair routine works only the backlog outside this queue. It uses this skill only.

**Mosaico connector.** Use the Mosaico connector that serves production (https://app.mosaico.one), the one the person connected in Claude. The plugin ships no Mosaico server of its own. If no Mosaico connector is connected, stop and tell the person to connect it in Claude's connectors (not /mcp), then rerun. Never use a server whose address contains amplifyapp.com, stage, staging, test or localhost; if that is the only Mosaico server available, stop and report it. Do not choose a server because its organisation id matches; stage and production share ids.

The schedule's text carries only the person's standing answers: the timezone and the LinkedIn public identifier; the scope is follow-ups across all dates with the action "one pass per thread". Take them from there; the schedule supplies the answers to this skill's opening questions, so do not ask them, do not show a menu, and do not ask which days or which scope. If a standing answer is missing, stop and report which one.

Resolve the current business date and time in the timezone from the schedule's standing answers. That date is for the report only: the day a follow-up may be booked for is counted from the day the Lead wrote and judged by Mosaico against its own today, never against a clock you read, and Mosaico returns that today (`today`) when it refuses a date. The person has supplied standing answers for this recurring automation: proceed without asking which days or which scope.

Do every LinkedIn step in Claude's built-in browser pane, which is signed in to the person's LinkedIn (the public identifier from the schedule's standing answers). Obtain connection evidence and identity only through the plugin's approved capture scripts, run by sending the browser javascript tool the one-line directive `// mosaico run <script>.js <PLACEHOLDER>=<value>` (the plugin's gate inserts the approved script; never retype a script), exactly as the skills describe; if the gate refuses the directive, run the approved script word for word with only the first line's value changed (the thread script's second line holds the Lead's name). The first-line value for every per-Lead script is the Lead's scriptIdentifier from the Mosaico read when it is present (a member id or a public identifier, whatever Mosaico supplies), otherwise the part of its linkedInProfileUrl after /in/. The thread script also takes the Lead's name from the Mosaico read, so its directive is `// mosaico run linkedin-thread-messages.js PUBLIC_IDENTIFIER=<scriptIdentifier> LEAD_NAME=<the Lead's name>`. The approved scripts are browser/linkedin-whoami.js, browser/linkedin-connection-evidence.js, browser/linkedin-recent-connections.js and browser/linkedin-thread-messages.js; read each from the installed plugin. Read each script file with the file-reading tool, one file at a time, by its path under the installed plugin's browser folder; do not print them with a shell command. If the installed plugin has no browser folder, stop and report that the plugin needs updating. Never read, copy, export or reconstruct a LinkedIn cookie, token or session; never write a LinkedIn script of your own; never read a Connect, Message or Pending button as a connection state; never set a connection state yourself. If a capture is unavailable or Mosaico cannot use its result, leave that Lead unverified, list it as skipped, and continue.

Step 1. Open https://www.linkedin.com/feed/ once. Run the approved whoami script and pass its output unchanged as identityEvidence to outreach_start_run (omit observedLinkedInProfile). Only if the whoami script cannot run, open the Me page and report its profile URL as observedLinkedInProfile instead. Start one run with intent follow_up_pass and pass its runId on every read and write; before each send-evidence write, run the whoami script again and pass its output as identityEvidence. If Mosaico blocks the start, stop and report the blocker; do not work around it. Read environmentName in the start answer: if it is not production, stop and report it, and begin the report with the line "Mosaico environment: production" (the name the answer gave).

Step 2. Work the follow-up queue with the selected action "one pass per thread", exactly as this skill's section "The follow-up queue (intent follow_up_pass)" describes. Read outreach_get_follow_up_queue with the runId; never read outreach_get_follow_ups as the working read of this run. Do what next says, once, then read the queue again, until completion.mustContinue is false; follow each item's recommendedCall literally (its tool and arguments unchanged, plus what supplyAlso names), and never reorder the items or skip ahead. For a fix-address item, make its recommendedCall (outreach_update_lead with the new linkedInProfileUrl and the runId) without visiting LinkedIn; for a drop-declined item, make its recommendedCall (outreach_update_lead with status dropped and the runId) and do nothing else for that Lead: no thread read, no draft, no send. A Lead named in skippedThisRun is information for the report: never open, capture, deposit or draft for it again in this run (a later run offers it again). When next.kind is connections-capture, run the approved recent-connections script once with STOP_AT set to next.script.stopAtCreatedAt (0 when it is null), save its output as returned, submit its pages to outreach_record_connections_snapshot one call per page in index order exactly as this skill describes (submit any pages Mosaico lists as missing, and first any pages left over from an earlier capture), then reread. For a verify-connection item, open its profileUrl, run the approved connection-evidence script with the Lead's scriptIdentifier as the first-line value and pass the result to outreach_record_connection_evidence; a blocked answer (profile-capture-failed, with profileCaptureFailures, givenUp and inToSort) is a record: report it, never capture that Lead again in this run, and continue. Do not draft or send for a Lead the queue still lists as unverified. The queue may list Leads with the reason colleague-verified-needs-own-check first (a colleague's sourcing run saved them as not connected, and her Leads are yours to verify): verify them from your own pane like any other unverified Lead. For a read-thread item, and for the readConversationCall of a draft item, run the approved thread script with the Lead's script identifier as the first-line value and pass its output unchanged as threadEvidence to outreach_deposit_conversation with publicLinkedInUrl and fresh identityEvidence; Mosaico derives direction and times. Every thread deposit carries the outcome of the Lead's latest message (declined, interested or neutral), judged as this skill describes; a no ends the Lead, so never draft or send for a Lead who said no. Pass every script's output exactly as returned, every field including integrity, never retyped or edited: if Mosaico answers evidence-altered, run the script again and pass the new output unchanged. If the answer is no-conversation, continue with the next Lead. If the answer is thread-not-found-in-window, report the Lead as thread not found in the window and continue with the next Lead; do not read it by eye. If the deposit answer carries linkedDuplicate, Mosaico linked two Leads that the thread proves are one person by member id: report the link and continue with the kept Lead (keptLeadId), whose delivery is the one to act on; never call outreach_link_duplicate_leads. If the answer is blocked thread-person-held-by-other-lead (the person is already another Lead of this owner and only an identifier proves it), record it with the Lead named in heldBy, never capture that thread again and continue with the next Lead (a person or the Repair routine links the two). Only if the script cannot run, open the item's messageUrl and deposit the visible conversation by eye, and say so in the report. When the deposit answer carries delivery.state deliverable and recommends send_approved_follow_up, send that approved follow-up right then, exactly as approved (delivery.body, delivery.messageId, delivery.messageUrl), without rereading the queue; when delivery.state is held or none, send nothing. A send-approved item is sent the same way from its approvedMessage. To send: open the item's messageUrl (the full messaging page when messageUrlBasis is conversation or stored; when it is profile, use the Message button and close any open message window before you navigate to the next profile and after each send), type the approved text and send it. Do not judge from the screen whether the typed text arrived or went out: the typed text is proved by the thread capture after the send, not by sight. Then run the approved thread script again with the Lead's script identifier as the first-line value and pass its output unchanged as threadEvidence to outreach_mark_message_sent with fresh identityEvidence; Mosaico marks it sent only when the thread shows the approved message. If Mosaico answers send-not-confirmed, do not retype it: retry the send once, run the thread script again, and if it is still not confirmed call outreach_record_delivery_block with reason cannot-message and continue with the next Lead. Never mark a message sent from the screen alone unless the script cannot run, and then say so in the report. If the conversation cannot be opened, call outreach_record_delivery_block with reason cannot-message and continue. For a draft item, after its thread deposit, save the missing outbound follow-up draft Mosaico permits with sentAt null, written from the Agent named by the item's agentId (outreach_get_agents, no arguments, once per run). When the Lead's latest message asks to be contacted later ("talk in January", "after the holidays", "next month", a named day) and its outcome is interested or neutral, book it instead of drafting for now, exactly as this skill's section "Book a later touch" describes: when the deposit answer lists draft_follow_up, write the draft with sendNotBefore set to the day you propose (YYYY-MM-DD); when it offers no draft and refuses nothing but follow-up-awaiting-reply, call outreach_update_lead with changes nextTouchOn set to that day and write no draft. Never work out today from a clock (the machine's, the page's; never run date): Mosaico judges every day against its own today in the owner's time zone and returns it as today in a date refusal. If Mosaico refuses a date (date-invalid, date-not-future, date-too-far or date-not-applicable), follow its recommendedAction: retry once with a day the Lead's words still name between earliestAllowed and latestAllowed, otherwise take continue_with_next_lead, write nothing more for that Lead and report the refusal; never pick a day only to get past it and never write the draft undated. A queue item with nextStep wait_for_scheduled_day is booked for a later day: it is not due, so never open, read, draft or send for it; report it from counts.scheduled (a queue left with only those ends with queue-empty). When its day has come (scheduledReason scheduled-due or next-touch-due) work the item like any other, without a date. When a thread deposit shows a new reply for a Lead with a booking (the note next-touch-scheduled), decide whether the booking still stands: if the reply names another time call outreach_update_lead with the new nextTouchOn, if it asks for contact now or takes the request back call it with nextTouchOn null, otherwise leave the booking as it is. Booking is the one case in which a draft item's recommendedCall is not made exactly as given (sendNotBefore is added, or the outreach_update_lead call replaces it), and only as the deposit answer says. For a rewrite-draft item (nextStep rewrite_follow_up_draft, between send-approved and draft), make its readConversationCall first (the thread script and the deposit, as for a read-thread item: the invitation actually sent is in the thread), then write the first message to the person from the Agent named by the item's agentId (outreach_get_agents, no arguments, once per run), following that Agent's current messageInstructions and enabled messagingChecklist and never repeating the words of the invitation, and record it with the item's recommendedCall: outreach_record_message with the existing messageId, plus the new body, a checklistReview with one pass or fail result for every enabled rule, and the runId; Mosaico keeps the kind, the day and sendNotBefore and leaves the status Draft. Never approve a rewritten draft and never send one written in this run. Apart from that rewrite, never approve, rewrite, replace or substitute a message. Continue until completion.mustContinue is false or Mosaico reports a genuine blocker (Mosaico, sign-in or LinkedIn failure). End the run with outreach_end_run: reason complete when completion.stopReason is queue-empty, needs-a-person or needs-another-intent, reason blocked, with the blockerCode Mosaico gave in this run or the linkedInIssue (warning, captcha or restricted) and a note, when completion.stopReason is blocked or a genuine blocker stops it. One Lead that fails is recorded and skipped, never a halt.

Step 3. Report separately, using Mosaico's counts, not memory: the Mosaico environment (the first line) and each run's runOutcome; how identity was established (whoami evidence or Me page); approved follow-up sends; follow-ups recorded as cannot-message; new follow-up drafts written; follow-up drafts rewritten after an Agent change (the count, and each Lead's name with its reason and the day it is booked for, if any; counts.rewrite for those still waiting); drafts Mosaico discarded (draftsDiscarded), each with its Lead and reason; outcomes recorded (declined, interested, neutral); Leads whose thread was not found in the window; whether the connections list was captured and how many Leads it marked connected; the queue's counts and its final completion.stopReason; approved follow-ups the application held (the held items that need a person, not the ones booked for a later day, each with its Lead and heldReason); Leads recorded as held twice (thread-person-held-by-other-lead) and Leads whose profile capture failed (profileCaptureFailures, givenUp, inToSort); sends confirmed from data versus by screen; Leads left unverified; threads read from data versus by eye; skipped Leads with reasons; Leads skipped this run (skippedThisRun), each with its code and reason; links a deposit made (linkedDuplicate: kept and alias Lead, drafts moved or discarded, any decline carried over); addresses fixed; Leads dropped as declined; bookings made (each Lead, the day and the Lead's words that asked for it); bookings changed or cleared (Lead, old and new day, why); booked items waiting (the queue's counts.scheduled); date refusals (Lead, field, code, the day tried and what was done); blockers. Nothing merely drafted may be described as approved or sent. When Mosaico notes repair-recommended on the follow-ups read, do not work the backlog in this run (it is the Repair routine's work) and end the report with the line "Repair needed: n items, run the Repair routine", using Mosaico's repairNeeded total for n. Report unverified Leads from the queue's unverified block: while its state is pending-connections-capture say the count is not known yet, and never present upperBound as a count. Preserve Mosaico as workflow authority and never modify another owner's records.

Step 4. Record the run on the Routines Board, as this skill's section "Record the run on the Routines Board" says, with the routine key `follow-up` and the routine name "Follow-up": if the schedule's text has no `routines board:` line, skip this step silently; otherwise write the run, the actions, the issues and `meta/board` in one batch, after the run is ended and the report is written. A failure is one line in the report, never a halt.

Guards: pacing between page loads and run expiry are enforced by Mosaico; a LinkedIn warning or captcha stops the run, which then reports.

## Record the run on the Routines Board

The last step of the Follow-up routine in this skill is to leave a record of
the run on the person's Routines Board, a page the schedule installer publishes once per person. The record is a courtesy: it
never changes what the run did, and it never holds back the run's own report.

1. **Find the board.** The schedule's text may carry one line, `routines board: https://claude.ai/artifact/<id>`. That address
   is the board. If the text has no such line, skip this whole step silently: write nothing, say nothing.
2. **Load the tool.** Load the `ArtifactData` tool with ToolSearch (`select:ArtifactData`). Every call takes the board address as `url`.
3. **Routine key.** `follow-up`.
4. **Read before you update.** `get` each document you may update (the `act-` and `iss-` documents named below and `meta/board`);
   an existing document has a `version`, and the write that updates it passes that number as `if_version`. Create a document that
   does not exist without one.
5. **Write once, with one `batch`** (all of it, or nothing):
   - `runs`, one document, id = this run's `runId` (when Mosaico issued none, because it refused or the run never started, use
     `follow-up-<startedAt as yyyymmddhhmm>`): `id`, `routine`, `startedAt` and `endedAt` (ISO 8601, UTC), `outcome` (`complete`,
     `blocked`, `nothing-to-do`, `failed` or `refused-busy`: a run Mosaico ended `complete` with nothing to do is `nothing-to-do`; a
     start Mosaico refused because another run was working is `refused-busy`; a run that failed or stopped with work open is `failed`), `headline` (one
     sentence), `counts` (an object of named numbers from Mosaico's counts, for example `sent`, `drafted`, `rewritten`, `bookings`,
     `discarded`, `held`, `skipped`), `notes` (an array of short strings) and `reportText` (this run's final report, plain text, as
     you give it to the person).
   - `actions`, one document for each thing the person must do (a decision, a sign-in, an Agent setting, items Mosaico left in To
     sort): id `act-<slug>-<yyyymmdd>` (the slug is a few lowercase words naming the thing; the date is the run's day), `routine`,
     `createdAt`, `text` (one plain sentence), `status` `open` and `source` (the run's id). If that id exists, leave it alone.
   - `issues`, one document for each defect or blocker the run met (a Mosaico code, a LinkedIn stop, a tool that was missing): id
     `iss-<slug>`, `routine`, `firstSeenAt` (kept as it is when the document exists, otherwise now), `lastSeenAt` (now), `text`,
     `status` `open` (an issue marked `fixed` that comes back becomes `open` again) and `fixRef` (kept as it is, otherwise an empty
     string).
   - `meta/board`: `id` `board`, `lastUpdatedAt` (now) and `lastUpdatedBy` `"<routine name> run"`, for example `"Follow-up run"`. Keep the `states` object when the document has one; never write `improvements`.
6. **A failed write never blocks the report.** If the board cannot be reached or a write is refused, say so in one line of the
   report ("Routines Board not updated: <reason>") and go on. Never retry in a loop and never end the run differently because of it.

## Routines report routine

This is the Routines report flow of Mosaico Outreach: the safety net for the person's Routines Board. It reads what each routine's latest scheduled run said and makes sure the board shows it, including for a routine that could not write to the board itself (it was refused, crashed, or ran on an older plugin). It touches no Mosaico record, opens no LinkedIn page, starts no Outreach run, sends nothing and approves nothing. It uses this skill only and needs no Mosaico connector.

The schedule's text carries one standing answer that matters here: the line `routines board: https://claude.ai/artifact/<id>` (and the timezone, for the report only). If the text has no such line, stop and report "No Routines Board address in this schedule; nothing to do." Load the `ArtifactData` tool with ToolSearch (`select:ArtifactData`) and the scheduled-tasks tools (`list_scheduled_tasks`, `list_task_runs`; load them with ToolSearch too when they are deferred).

Step 1. List the scheduled tasks and keep the Mosaico Outreach routines: match by the routine their saved text names ("This is the Follow-up routine", "This is the Send invitations routine", "This is the Withdraw stale invitations routine", "This is the Source leads routine", one task per lane, own or colleagues, as its saved text names the lane). The routine keys are `follow-up`, `send-invitations`, `withdraw`, `source-own` and `source-colleagues`. Ignore this task itself, the Repair task and any task you cannot match.

Step 2. For each matched task, read its runs with `list_task_runs` and keep the runs that finished since the board last heard of that routine: `list` the board's `runs` collection (use `query` with `where` on `routine` and `order_by` `endedAt` descending, `limit` 20) and take the newest `endedAt` for the routine; a task with no run document yet counts every finished run of the last 24 hours. A scheduled run whose time window (start to end) already holds a `runs` document of that routine (its `startedAt` inside the window) is on the board: skip it, and never write a second document for it.

Step 3. For each scheduled run that is not on the board, read its final report (the run's last message, as the task-runs read gives it) and write one `runs` document: `id` `sched-<routine key>-<start as yyyymmddhhmm in UTC>`, `routine`, `startedAt` and `endedAt` (ISO 8601, UTC), `outcome` (take it from the report: `complete`, `blocked`, `nothing-to-do`, `failed` or `refused-busy`; a run with no report, or one that stopped before it ended, is `failed`), `headline` (one sentence from the report), `counts` (only numbers the report states), `notes` (short strings, among them "recorded by the Routines report") and `reportText` (the report, plain text, unchanged). Add the actions and issues that report names exactly as the section "Record the run on the Routines Board" describes (ids `act-<slug>-<yyyymmdd>` and `iss-<slug>`, read before updating, `firstSeenAt` kept). Invent nothing: a number, an outcome or a problem that the report does not state is not written.

Step 4. Write it all in one `batch`, together with `meta/board` (`id` `board`, `lastUpdatedAt` now, `lastUpdatedBy` "Routines report run", the `states` object kept when there is one), reading each existing document first and passing its `version` as `if_version`. Write nothing at all when every run is already on the board. This routine writes no `runs` document of its own and never writes `improvements`.

Step 5. Report in a few lines: for each routine, the newest run you found and whether it was already on the board or you added it; the actions and issues you added; any routine whose latest run is older than its schedule allows (name it, do not diagnose it); and a failed board write in one line. A failure is never a halt for the rest.

Guards: this routine is read-only everywhere except the Routines Board.

## Sync data routine (superseded)

The Sync data routine no longer exists. It is superseded by three routines, each with its own schedule: the **Follow-up routine** (this skill), the **Send invitations routine** and the **Withdraw stale invitations routine** (both in the mosaico:mosaico-outreach-invite-run skill). A saved schedule that still says "This is the Sync data routine" is the old single schedule. Do not run any part of it: start no Outreach run, open no LinkedIn page and change nothing in Mosaico. Stop and report that this saved schedule is superseded by three schedules and has to be reinstalled with the mosaico:mosaico-outreach-schedule-install skill, which retires it and installs the three new ones.
