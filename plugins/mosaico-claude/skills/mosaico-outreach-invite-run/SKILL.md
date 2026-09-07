---
name: mosaico-outreach-invite-run
description: Source 20 qualified Mosaico Outreach Leads per selected day and prepare drafts, send already-approved invitations, or perform both workflows safely.
---

# Mosaico Outreach Invitation Run

Before using any Outreach or browser tool, ask these questions in order unless the person already
provided the answer as part of the current invocation:

1. "Which days should this run cover: today, tomorrow, or a specific set of dates?"
2. "For those days, do you want to source Leads and prepare invitation drafts, send approved invitations, or both?"

Resolve today and tomorrow using the person's local business date. Preserve the exact selected dates
throughout the run. Accept one action and run only the selected scope.

## Source Leads and prepare drafts

1. Read the active owned Agents and each selected Outreach day.
2. The required target is exactly 20 qualified invitation Leads per selected day. Count already
   recorded ready invitation Leads and source the remainder needed to reach 20 without duplicating
   existing Leads.
3. A day with fewer than 20 qualified Leads is incomplete. Continue searching, broadening suitable
   searches, checking profiles, saving qualified Leads with their profile details and preparing
   missing invitation drafts until every selected day contains 20.
4. Do not stop because the work is slow, difficult, expensive or because an initial search produced
   only a few Leads. Loading 3 Leads is not completion; if 17 are still missing, continue until all
   17 are found.
5. Save each qualified Lead and its missing outbound Invite draft through the Mosaico tools. Do not
   approve or send any invitation in this scope.
6. Mosaico must preserve valid partial progress and must not reject or roll back a day merely because
   fewer than 20 Leads have been found so far. The 20-Lead completion target governs this skill run,
   not whether each valid Lead may be stored.
7. Report a shortfall only when a genuine Mosaico, authentication, LinkedIn or human-decision blocker
   prevents further work. State the exact completed count, remainder and blocker; never report the
   day as complete below 20.

## Send approved invitations

1. Work only on the selected dates and only on exact outbound Invite messages whose current Mosaico
   status is already Approved.
2. Never approve, rewrite, replace or substitute an invitation. If the approved body does not exactly
   match the body about to be sent, stop for that invitation and report the blocker.
3. Send through the authenticated LinkedIn browser.
4. Verify each invitation against LinkedIn rather than trusting the click.
5. Call `outreach_mark_message_sent` only after successful delivery verification, using the exact
   Lead and Message identities and the exact send time when LinkedIn exposes it, otherwise null.
6. Continue until every approved invitation on every selected date is sent or Mosaico reports a
   genuine blocker.

## Both

1. Complete **Source Leads and prepare drafts** first and reach 20 Leads on every selected date.
2. Reread the current Mosaico state for those dates.
3. Complete **Send approved invitations** only for messages that were already human-approved. Never
   approve a newly created draft automatically.

For every scope, Mosaico is the workflow authority for stored state, ownership, validation, allowed
actions and recovery. This skill owns the instruction to continue sourcing until the 20-Lead target
is reached. Stop only when the selected scope is complete, Mosaico reports a genuine blocker, or a
human decision is required. Never modify another owner's records.
