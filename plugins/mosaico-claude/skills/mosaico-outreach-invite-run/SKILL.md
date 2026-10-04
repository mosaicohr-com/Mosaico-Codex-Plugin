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
   Or run the approved whoami script instead: print it without changing it,

   ```bash
   cat "${CLAUDE_PLUGIN_ROOT:-$(dirname "$(dirname "$(find ~/.claude/plugins -path '*/mosaico-claude/browser/linkedin-whoami.js' -print -quit)")")}/browser/linkedin-whoami.js"
   ```

   run it word for word with the browser pane's `javascript_tool`, and pass its output unchanged as
   `identityEvidence` to `outreach_start_run`. Mosaico compares the identifiers from the record. If the
   script is unavailable, read the Me page as above.
2. Call `outreach_start_run` with that URL as `observedLinkedInProfile` and the intent: `source_invitation_leads` for sourcing, `send_approved_invitations` for sending. When doing both, start a separate run for each scope.
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
   Or run the whoami script again and pass its output unchanged as `identityEvidence` on the write.
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

## Source Leads only

Use this scope when the Leads will be shared with a colleague before any draft is written, so that
each owner's drafts are later written under their own Agent and voice.

1. Same as "Source Leads and prepare drafts", but the target is the number of ready Leads the person
   named (for example 40), read from `workflowStatus.counts.readyLeads`, not the prepared count.
2. Save each qualified Lead with its profile details through `outreach_save_lead`, which takes no
   connection state, then run **Capture connection evidence** for it. Do not write any invitation draft
   in this scope, and do not approve or send anything.
3. Reread `outreach_get_day` after every saved Lead and continue until `counts.readyLeads` reaches
   the named number or Mosaico returns a blocker, `human_decision_required` or `stop_run`.
4. Report the exact count of ready Leads and any shortfall with its blocker. A day below the named
   number is not complete.

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
7. Reread the same day after each send, capture or recorded outcome and continue until Mosaico reports
   completion or a genuine blocker (Mosaico, sign-in or LinkedIn failure). One Lead that cannot be
   invited never stops the run.
8. In the final report list recorded outcomes and Leads left unverified separately from sends and
   blockers, each with its Lead and reason.

## Capture connection evidence

Whether you are connected to a Lead is a fact in LinkedIn's own data, not on the page's buttons. This
procedure carries that data to Mosaico unchanged; Mosaico reads it and decides. Never read a Message,
Connect or Pending button as a connection state, never choose a field by what it means and never decide
the relationship yourself.

The capture is the plugin's connection-evidence capability: one approved script, shipped at
`browser/linkedin-connection-evidence.js` inside the installed plugin, run word for word in the signed-in
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
   Or run the approved whoami script, as in **Start the run**, and pass its output unchanged as
   `identityEvidence` to `outreach_start_run`. If the script is unavailable, read the Me page.
2. Open the Lead's `linkedInProfileUrl` in the built-in browser pane. No reload is needed.
3. Print the approved script without changing it:

   ```bash
   cat "${CLAUDE_PLUGIN_ROOT:-$(dirname "$(dirname "$(find ~/.claude/plugins -path '*/mosaico-claude/browser/linkedin-connection-evidence.js' -print -quit)")")}/browser/linkedin-connection-evidence.js"
   ```

   Run the printed script with the browser pane's `javascript_tool`, changing only the value on its first
   line to the last segment of the profile URL's path (the part after `/in/`, with no trailing slash or
   query), in quotes. Do not paraphrase, reorder, shorten or extend it: the gate refuses anything else. The
   query inside it is the one known to work today: if LinkedIn stops answering it, stop and report that; do
   not guess another.
4. If `signedIn` is false, the pane is not signed in to LinkedIn: stop the capture and report it. If
   `status` is not 200 or `entries` is empty, stop: leave the Lead unverified, list it as skipped and
   continue with the next Lead.
5. Call `outreach_record_connection_evidence` with `leadId`, `profileUrl` (the Lead's
   `linkedInProfileUrl`), `capturedAt` and `entries` exactly as the script returned them, the `runId`
   and `observedLinkedInProfile`. Report Mosaico's answer in plain words: connected, invite-pending,
   not-connected, or the blocker it returned. If Mosaico refused or the capture gave it nothing usable,
   leave the Lead unverified, list it as skipped and continue; follow any action Mosaico names, and do
   nothing else.

When the capability is unavailable (the script file is missing, the gate refuses it, or the pane cannot be
signed in), do not work around it. Leave the Lead unverified, note in the report only what the LinkedIn
page visibly shows (a Message, Connect or Pending button) for the person to read, never record that as a
connection state, and continue with the next Lead or stop the step and report it.

## Both

1. Complete **Source Leads and prepare drafts** first and reach 20 Leads on every selected date.
2. Reread the current Mosaico state for those dates.
3. Complete **Send approved invitations** only for messages that were already human-approved. Never
   approve a newly created draft automatically.

For every scope, Mosaico is the workflow authority for stored state, target completion, ownership,
validation, allowed actions and recovery. Stop only when the selected scope is complete, Mosaico
reports a genuine blocker, or a human decision is required. Mosaico decides which member a record belongs to from the run; do not try to work that out yourself.
Only Owners and Admins can use Outreach.
