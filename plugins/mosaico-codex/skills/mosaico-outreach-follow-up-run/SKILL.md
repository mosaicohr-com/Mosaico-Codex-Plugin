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
6. If an Owner or Admin asks to run for a colleague, pass that member's id as `onBehalfOfMemberId` on
   `outreach_start_run` only. The LinkedIn account must then be that colleague's.

If `outreach_save_lead` or `outreach_deposit_conversation` reports that the profile already exists
under another owner, stop and show the person the owner, Lead and status. Re-send with
`acknowledgeProfileOnOtherOwner: true` only after the person decides to; never set it yourself.

## No pressure, and what Mosaico refuses

A no ends the Lead. Never draft a follow-up for a Lead who said no, never ask twice, never try to change
the Lead's mind. Mosaico enforces this, and it also stops us chasing our own silence:

- `follow-up-declined`: the Lead's latest message said no. Mosaico has moved the Lead to Drop and refuses
  new drafts for it.
- `follow-up-awaiting-reply`: the latest message sent on the Lead is ours and it is not the invitation
  note. Our own unanswered message blocks a new one. `outreach_get_follow_ups` gives such a Lead
  `followUpReason` `awaiting-reply` and never lists it as actionable. `connection-accepted-no-reply` now
  means only that the invitation note is the last message, or that nothing has been sent yet.
- `follow-up-thread-unread`: Mosaico has not read this Lead's thread. It refuses drafts for the Lead until
  its thread is read.

When `outreach_record_message` is answered with one of these codes as skipped or blocked, never work around
it: record what Mosaico returned, skip the Lead and continue with the next one. Do not reword the draft,
do not try another kind of message and do not ask the person to override it.

## Repair drafts first

Each time Mosaico stores a thread or an outcome, it checks every unsent draft on that Lead against these
rules and discards the ones that no longer qualify. The deposit answer lists them as
`draftsDiscarded: [{ messageId, reason }]`, where the reason is `follow-up-declined`,
`follow-up-awaiting-reply` or `follow-up-thread-unread`.

When `outreach_get_follow_ups` returns the recommended action `repair_drafts`, it also returns
`repairSuggestions`: the Leads that hold unsent drafts which break the rules given what Mosaico has
stored, each with its reasons. Before drafting anything new, and before sending any approved draft, visit
each Lead in `repairSuggestions` first: read its thread by eye, deposit it with `outcome` (see **Capture
the thread**), then reread `outreach_get_follow_ups`. Report in plain words how many drafts Mosaico
discarded, for which Leads and for which reasons.

## Repair is a separate routine

The Follow-up run is daily work and does not clear the backlog. Mosaico caps the verification list at 20
Leads per run, oldest invitation first (`verifyCap` on `outreach_get_follow_ups`); the rest are counted as
`summary.deferredToRepair`, and `repairNeeded` counts what the Repair routine would work, per group and in
total. Work only what `outreach_get_follow_ups` lists, and never go looking for more. When its `notes` hold
`repair-recommended`, do not work the backlog in this run: end the final report with the line "Repair needed:
n items, run the Repair routine", where n is `repairNeeded.total`.

## The follow-up queue

Mosaico (server release 20261013a or later) also offers `outreach_get_follow_up_queue`: the same follow-up work as a small, paged,
ordered list, one item per Lead with its stage, its next call and a stop reason, and no conversations or full Lead records. A
Codex run may read it with the `runId` of a `check_follow_ups` or `send_approved_follow_ups` run to see the order and the counts,
and then work each item by the rules below; each item's `coveredByRun` says whether this run's intent may do it. Mosaico owns the
order, so do not reorder it. The queue also carries the repairs Mosaico can decide for its own Leads (stages `fix-address` and
`drop-declined`, worked first; a profile check joins `verify-connection` and a history mismatch joins `read-thread`; every item's
`repairGroup` names the Repair queue group it stands in for) and `skippedThisRun`, the Leads this run already tried with an answer
nothing in the run can change, which Mosaico leaves out of `items` and `next` and which are for the report only. The Repair routine
now works only the backlog outside this queue. Dated follow-ups (server release 20261013c or later): every item carries `notBefore`
(the booked day that governs the Lead's follow-up, null when none) and `scheduledReason` (`scheduled`, `scheduled-due`,
`next-touch-scheduled`, `next-touch-due` or null), judged by Mosaico against its own today. Work booked for a later day sits last in
stage `held` with `nextStep` `wait_for_scheduled_day`: it is not due, needs no person and is never worked, and `counts.scheduled`
counts it for the report (a queue left with only that stops with `queue-empty`). See **Book a later touch**. The scheduled Follow-up
routine (run intent `follow_up_pass`) needs the Claude plugin's approved browser scripts, so Codex does not run it: it is installed
from Claude.

## Check for new follow-ups

1. Work across all dates and read `outreach_get_follow_ups` with the `runId`. When the recommended
   action is `capture_connections`, run **Capture recent connections** once, then reread. When the
   recommended action is `verify_connection`, Mosaico lists the Leads whose connection is unknown or unverified in
   `unverifiedLeads`, each with its profile URL: for each one run **Capture connection evidence**, then
   reread `outreach_get_follow_ups`. The list may name Leads with the reason `colleague-verified-needs-own-check`
   first (a colleague's sourcing run saved them as not connected): verify them from your own pane like any other
   unverified Lead. Never guess a connection and never skip to drafting for a listed
   Lead.
2. For each returned Lead, open its pages directly: `navigation.messageUrl` (the stored
   conversation) when present, otherwise `navigation.profileUrl`. Do not search LinkedIn lists for
   Leads that carry a URL, and never read a LinkedIn list or button to decide whether a Lead is
   connected.
3. Inspect each relevant currently visible LinkedIn conversation. This is the by-eye form: see
   **Capture the thread** for why Codex cannot read threads from LinkedIn's data.
4. Deposit each complete visible conversation oldest to newest through
   `outreach_deposit_conversation` as `messages`, passing the conversation's URL as `linkedInMessageUrl` so
   the next run opens it directly, and the `outcome` of the Lead's latest message (see **Capture the
   thread**). Do not compare it with stored history or decide which reply is newer;
   Mosaico owns identity matching, chronology, follow-up state, blockers and allowed actions. Say in the
   final report that these threads were read by eye.
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
   for which reasons, how many Leads each outcome (declined, interested, neutral) was recorded for, and the
   bookings made, changed or cleared and the date refusals (see **Book a later touch**).

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
4. Send through the authenticated LinkedIn browser.
5. Verify delivery on LinkedIn rather than trusting the click.
6. Call `outreach_mark_message_sent` only after successful delivery verification, using the exact
   Lead and Message identities and the exact send time when LinkedIn exposes it, otherwise null.
   Codex cannot run the approved thread script, so it cannot pass `threadEvidence`: Mosaico records the
   mark as a reading of the screen and answers `send-proof-missing`. Say so in the final report, with
   each Lead. A Claude run, which runs the thread script again after the send, confirms a send from
   LinkedIn's data. If Mosaico answers `send-not-confirmed` it did not go out: do not retype it and do
   not mark it sent; call `outreach_record_delivery_block` with `reason: cannot-message` and continue.
7. Continue until every currently approved follow-up draft is sent or recorded, or Mosaico reports a
   genuine blocker (Mosaico, sign-in or LinkedIn failure). One Lead that cannot be messaged never
   stops the run.
8. In the final report list recorded outcomes separately from sends and blockers, each with its
   Lead and reason, and name the sends marked by screen.

## Capture the thread

Whether a person replied, when, and who said what, is a fact in LinkedIn's own messaging data. Mosaico
reads a thread from that data only when it is carried by the thread script of the Mosaico plugin for Claude
Code (`linkedin-thread-messages.js`): one approved script, run word for word in the signed-in LinkedIn page
and enforced by that plugin's browser-script gate. That script runs only in Claude's built-in browser pane.
Codex's page-script scope is sandboxed (it has no session cookies and cannot make the page's own requests),
so the Codex package cannot run it, and this run does not capture threads:

1. Never read, copy, export or look for a LinkedIn cookie, token or session: not from the page, browser
   storage, profile files, DevTools data or the keychain. Never write a script that calls LinkedIn.
2. Do not pass `threadEvidence` to `outreach_deposit_conversation`; it accepts only what the approved
   script returns.
3. Read each thread by eye, as in **Check for new follow-ups** and **One pass per thread**, and deposit it
   through `outreach_deposit_conversation` as `messages`, with the `outcome` of the Lead's latest message
   (see below). Mosaico stores such a thread as a reading, not as evidence.
4. Say in the final report that the threads were read by eye and that the thread script could not run in
   Codex. A run in Claude's built-in browser pane reads them from LinkedIn's data instead.
5. Report Mosaico's answer in plain words: stored (with its `threadStatus`, the outcome it recorded and any
   `draftsDiscarded`), blocked `outcome-required` (the thread holds a message from the Lead and no outcome
   was given; nothing was stored: add the outcome and deposit again), or the blocker code it returned
   (follow the action Mosaico names and do nothing else).

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
message's time in the conversation, in the owner's time zone). A named day is that day; for a period such as "January" or "next
month" take its first weekday. Never work out today from a clock: not the machine's, not the page's, and do not run `date`. Mosaico
alone knows today in the owner's time zone, and it returns it as `today` when it refuses a date. A bookable day is after today and
no more than 365 days ahead.

**Book it.** Mosaico's answer to the thread deposit decides which call to make, not your own reading of the Lead's state. This is the
one case in which a `draft` item's `recommendedCall` is not made exactly as given: it gets `sendNotBefore` added, or it is replaced by
the `outreach_update_lead` call below, and only as the deposit answer says:

1. The answer lists `draft_follow_up` among its allowed actions (a follow-up is due now): write the draft as this scope's draft step
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

## Capture recent connections

Whether an invitation was accepted is a fact in LinkedIn's own list of your connections, newest first,
not on a profile's buttons. Mosaico matches that list to the owner's own Leads only when it is carried by
the connection-evidence capability of the Mosaico plugin for Claude Code, under the same rules as
**Capture connection evidence**. The Codex package has no such capability, so when the read of
`outreach_get_follow_ups` returns the recommended action `capture_connections`:

1. Do not call `outreach_record_connections_snapshot`; it accepts only what the approved script returns,
   one page per call, and Codex cannot run that script.
2. Never compare names or decide who accepted yourself.
3. Report that the connections list was not captured, record nothing, continue with the rest of the run
   and reread `outreach_get_follow_ups`.

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
2. For each Lead, open `navigation.messageUrl` directly (the profile URL when there is no thread
   yet). If that URL opens a different
   person's conversation, do not deposit it: call `outreach_update_lead` with
   `linkedInMessageUrl: null` and `reason: wrong-person`, then open the Lead's profile and use
   Message to find the right thread; if it cannot be found, continue with the next Lead.
3. Deposit the complete visible conversation oldest to newest through
   `outreach_deposit_conversation` as `messages` (the by-eye form; see **Capture the thread**), passing the
   conversation's URL as `linkedInMessageUrl` and the `outcome` of the Lead's latest message. If Mosaico
   reports `returnedToDraft`, that Lead's approved follow-up is now a draft because a new reply arrived: do
   not send it. If the outcome was `declined`, send nothing and draft nothing for that Lead.
4. Reread the Lead's state. If Mosaico still lists an approved outbound follow-up for it, send it
   exactly as approved, verify delivery on LinkedIn and call `outreach_mark_message_sent` only after
   successful verification. Codex cannot run the thread script, so Mosaico records the mark as a reading
   of the screen and answers `send-proof-missing`; say so in the report. If Mosaico answers
   `send-not-confirmed` it did not go out: do not retype it and do not mark it sent.
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
8. Report sends (all marked by screen in Codex), recorded outcomes (declined, interested, neutral), drafts
   written, drafts Mosaico discarded (`draftsDiscarded`, with each Lead and reason), Leads left
   unverified, bookings made, changed or cleared, date refusals, and skipped Leads with reasons, separately.

For every scope, Mosaico is the workflow authority. Follow its allowed actions and recommended
action. Stop only when the selected scope is complete, Mosaico reports a genuine blocker, or a human
decision is required. Mosaico decides which member a record belongs to from the run; do not try to work that out
yourself. Only Owners and Admins can use Outreach.
