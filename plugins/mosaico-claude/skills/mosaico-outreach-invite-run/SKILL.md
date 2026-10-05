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
   Or run the whoami script again and pass its output exactly as returned as `identityEvidence` on the write.
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

## Script output goes to Mosaico exactly as returned

Every approved script returns an `integrity` field, `{ algorithm: "fnv1a32", digest }`, computed in the
page over everything else it returns. Wherever a script's output goes to Mosaico (`identityEvidence` from
the whoami script, the connection evidence, `sentInvitationEvidence`), pass it exactly as returned: every
field, `integrity` included, never retyped, trimmed, reformatted, translated or "fixed". Mosaico recomputes
the digest and refuses an altered copy with `evidence-altered`: nothing is stored, and the recommended
action is `recapture`. Then run the approved script again and pass the new output unchanged. Never edit
the copy to make it pass.

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
4. Send through the authenticated LinkedIn browser: click Connect and type the approved note. Do not
   judge from the screen whether it worked; LinkedIn's data says so, in the next step.
5. **Confirm the send from data.** LinkedIn's profile data cannot show a pending invitation; only its
   Sent invitations list can. Straight away, run the approved sent-invitations script with the Lead's
   public identifier after the send and pass its output exactly as returned as `sentInvitationEvidence`
   (**Capture the sent invitation**) to `outreach_mark_message_sent`, with the exact Lead and Message identities, the exact
   send time when LinkedIn exposes it, otherwise null, fresh `identityEvidence` (run the whoami script
   again) and the `runId`. Mosaico reads the capture: it accepts the mark only when the Lead is on the
   list with a send time after your check before the send, and records the send time as the proof. Report
   its answer in plain words. Never call `outreach_record_connection_evidence` for this capture. Do not
   pass `sendEvidence`: it is the connection-evidence script's output and proves only that the person
   accepted at once, so for anything else Mosaico answers `send-evidence-cannot-prove` and writes nothing.
6. If Mosaico answers `send-not-confirmed`, LinkedIn's Sent invitations list does not show the invitation:
   it did not go out. Do not retype the note and do not mark it sent. Retry the send once, run the script
   again and pass its output again as `sentInvitationEvidence`. If Mosaico answers `send-not-confirmed`
   again, call `outreach_record_delivery_block` with `reason: cannot-message` and continue with the next
   invitation. For `send-evidence-stale`, `send-evidence-before-send` or `send-evidence-malformed`, the
   capture was unusable: run the script again once and pass it again; if it is still refused, leave the
   invitation Approved, list it as skipped with the code and continue (the next run checks the Lead
   before sending, so an invitation that did go out is never sent twice). For `send-evidence-lead-mismatch`,
   the capture was for another profile: run the script for this Lead's own public identifier. For
   `send-evidence-cannot-prove`, run the sent-invitations script and pass its output as
   `sentInvitationEvidence`.
7. Never mark an invitation sent from the screen alone. Only when the script cannot run (the script file
   is missing, the gate refuses it, or LinkedIn stops answering it), and the Connect click and note
   visibly went through, call `outreach_mark_message_sent` without `sentInvitationEvidence`: Mosaico
   records it as a reading of the screen and answers `send-proof-missing`. Say so in the final report,
   with each Lead.
8. Reread the same day after each send, capture or recorded outcome and continue until Mosaico reports
   completion or a genuine blocker (Mosaico, sign-in or LinkedIn failure). One Lead that cannot be
   invited never stops the run.
9. In the final report list recorded outcomes and Leads left unverified separately from sends and
   blockers, each with its Lead and reason, and count the sends confirmed from data separately from
   any marked by screen.

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

## Capture the sent invitation

Whether an invitation went out is a fact in LinkedIn's own Sent invitations list. This procedure carries
that data to Mosaico unchanged; Mosaico reads it and decides. Never judge from the screen whether a send
worked.

The capture is the plugin's sent-invitations script: one approved script, shipped at
`browser/linkedin-sent-invitations.js` inside the installed plugin, run through a one-line run directive in the signed-in
LinkedIn page by the built-in browser pane. It sends LinkedIn's own session and CSRF material to LinkedIn
only and never returns it; it looks for the one Lead on the Sent invitations list (up to five pages of a
hundred) and returns only whether it was found, when it was sent and the two URNs. The endpoint it calls
has not been validated against a live account yet: if it stops answering, stop and report that, and do not
guess another. The plugin's browser-script gate refuses any other script that touches LinkedIn or a
credential store, and the capture does not work through the Chrome extension.

Run these steps right after the send, for the Lead you just sent to:

1. Run the script with the browser pane's `javascript_tool` from any linkedin.com page by sending one line as the
   whole script: `// mosaico run linkedin-sent-invitations.js PUBLIC_IDENTIFIER=<public identifier>`, where the
   identifier is the Lead's public identifier (the last segment of the profile URL's path, the part after
   `/in/`, with no trailing slash or query), without quotes. The plugin's gate inserts the approved script;
   never print, retype, paraphrase, reorder, shorten or extend it.
   Fallback, only when the gate refuses the directive: print the approved script without changing it,

   ```bash
   cat "${CLAUDE_PLUGIN_ROOT:-$(dirname "$(dirname "$(find ~/.claude/plugins -path '*/mosaico-claude/browser/linkedin-sent-invitations.js' -print -quit)")")}/browser/linkedin-sent-invitations.js"
   ```

   then run the printed script with the browser pane's `javascript_tool` from any linkedin.com page, changing
   only the value on its first line to the Lead's public identifier, in quotes. Do not paraphrase, reorder,
   shorten or extend it: the gate refuses anything else.
2. If `signedIn` is false, the pane is not signed in to LinkedIn: stop and report it. If `state` is
   `error`, pass it anyway: Mosaico answers `send-evidence-malformed` and tells you to run it again.
3. Pass the script's whole output exactly as returned (every field, `integrity` included) as
   `sentInvitationEvidence` to `outreach_mark_message_sent`. If Mosaico answers `evidence-altered`, run the
   script again and pass the new output unchanged.

When the script is unavailable, do not work around it: see step 7 of **Send approved invitations**.

## Both

1. Complete **Source Leads and prepare drafts** first and reach 20 Leads on every selected date.
2. Reread the current Mosaico state for those dates.
3. Complete **Send approved invitations** only for messages that were already human-approved. Never
   approve a newly created draft automatically.

For every scope, Mosaico is the workflow authority for stored state, target completion, ownership,
validation, allowed actions and recovery. Stop only when the selected scope is complete, Mosaico
reports a genuine blocker, or a human decision is required. Mosaico decides which member a record belongs to from the run; do not try to work that out yourself.
Only Owners and Admins can use Outreach.
