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
   A sourcing start must also say who receives the Leads and how many each, or Mosaico issues no run
   (the application never guesses a colleague). Send one of two things with `outreach_start_run`:
   - `quota`: a map from each active owner's member id to the number of accepted Leads that owner
     must reach (a whole number from 1 to 100). It must always include the run owner's own id, for
     example `{"<run owner member id>": 3, "<colleague member id>": 3}`. Naming anyone but the run owner
     needs an Owner or Admin.
   - `colleagueOwnerUserId`: the member id of one active colleague, distinct from the run owner. Mosaico
     then gives the run owner and that colleague 5 each.

   The person's standing answer says who receives Leads and how many; use it as given. Member ids come
   from `get_team_profiles` (each person's "Person ID"); never invent one or take one from memory. If
   neither a quota nor a colleague is known, do not start the run: ask the person who receives the Leads
   and how many each. A scheduled run cannot ask: it stops, quotes Mosaico's code and message verbatim when
   Mosaico gave one, and ends its report with this sentence: "Fix: run /mosaico:mosaico-outreach-schedule-install (Codex: the mosaico-outreach-schedule-install skill), answer who receives the Leads and how many each, and it will put the quota map into this schedule." If
   Mosaico answers `sourcing_participant_required`, the start needs `colleagueOwnerUserId` or `quota`; if it
   answers `sourcing_quota_invalid`, the map is wrong (an id that is not an active member, the run owner
   missing, or a target outside 1 to 100). Mosaico's answer says what to fix: fix exactly that from the
   person's answer and start again once, never with a guessed colleague or number. The quota decides when
   the run is complete. When the person answered those two questions in this run, make the offer in
   **Offer to save the quota into the Source leads schedule**, below.
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
the whoami script, the connection evidence, `sentInvitationEvidence`, `colleagueConnectionEvidence`), pass it exactly as returned: every
field, `integrity` included, never retyped, trimmed, reformatted, translated or "fixed". Mosaico recomputes
the digest and refuses an altered copy with `evidence-altered`: nothing is stored, and the recommended
action is `recapture`. Then run the approved script again and pass the new output unchanged. Never edit
the copy to make it pass.

## Offer to save the quota into the Source leads schedule

Do this only when the person answered who receives the Leads and how many each during this run. It does
not apply when the quota came from a schedule's standing answer. Once you have the answer, ask once,
before you start the run or straight after: "Do you want me to save this into your Source leads schedule,
so the scheduled runs use it too?" The run does not depend on the answer.

- Yes: follow "Update the Source leads quota in place" in the `/mosaico:mosaico-outreach-schedule-install`
  skill, for the Source leads schedule only. Ask nothing else, change nothing else in that schedule, and
  keep its times. Read the saved schedule back and tell the person what it now holds.
- No: use the answer for this run only, and say in the report that the quota was used for this run only and
  the Source leads schedule is unchanged.
- If no Source leads schedule is installed, say so and offer to install one with
  `/mosaico:mosaico-outreach-schedule-install`. Do not skip the offer silently.

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
   starts unknown. For a candidate you save for a colleague, first run **Check a candidate against the
   colleague** when it applies. Then run **Capture connection evidence** for the saved Lead, so Mosaico records connected,
   invite-pending or not-connected before any draft is written. Write the missing outbound Invite draft
   only for a Lead Mosaico lists as verified. Do not approve or send any invitation in this scope.
6. Reread `outreach_get_day` after every saved Lead and draft. Mosaico preserves partial progress and
   owns the 20-Lead completion predicate; a valid partial save is not a completed run.
7. Report a shortfall only when a genuine Mosaico, authentication, LinkedIn or human-decision blocker
   prevents further work. State the exact completed count, remainder and blocker; never report the
   day as complete below 20.
8. Finish with **Report a sourcing run**.

## Source Leads only

Use this scope when the Leads go to the owners named in the run's quota (the person alone, a colleague,
or several members) before any draft is written, so that each owner's drafts are later written under
their own Agent and voice.

1. Same as "Source Leads and prepare drafts", but the target is the quota sent at the start of the run:
   each owner's accepted-Lead target, not the 20 of a prepared day. Mosaico keeps the quota and reports
   what remains for each owner; use its counts, and `workflowStatus.counts.readyLeads` for the ready
   Leads, not the prepared count.
2. Save each qualified Lead with its profile details through `outreach_save_lead`, which takes no
   connection state (for a candidate you save for a colleague, first run **Check a candidate against the
   colleague** when it applies), then run **Capture connection evidence** for it. Do not write any invitation draft
   in this scope, and do not approve or send anything.
3. Reread `outreach_get_day` after every saved Lead and continue until Mosaico says the quota is met or
   returns a blocker, `human_decision_required` or `stop_run`.
4. Finish with **Report a sourcing run**. A run below its quota is not complete.

## Check a candidate against the colleague

This applies in **Source Leads and prepare drafts** and **Source Leads only**, to a candidate you are about to
save for a colleague (an owner other than the run owner). Whether the candidate is already connected to that
colleague is a fact in LinkedIn's Sales Navigator, not something to judge. This procedure carries it to
Mosaico unchanged; Mosaico reads it and decides. Never decide it from the screen, from a result list or from
a name, and never use it as a connection state: it sets none.

Mosaico tells you when it is needed. When `outreach_get_day` (with `intent: source_invitation_leads` and the
`runId`) lists the colleague in `workflowStatus.colleagueChecks` with `allowed: true`, run the check for every
candidate you will save for that colleague, once, right before `outreach_save_lead`. When there is no such
entry, or `allowed` is false (the entry says why), save as usual with no evidence. A Lead for the run owner
never needs it. Mosaico supplies the colleague's identifier in that entry; you never choose or retype it.

1. Take the candidate's public identifier: the part of the profile URL you are about to save after `/in/`, with
   no trailing slash or query, or the opaque id when that is what the URL holds (it starts with `ACoAA`). Use it as it is.
2. The entry's `directive` is the line to run, with `<candidate>` left for you to fill. Replace only
   `<candidate>` with that identifier; leave the colleague's identifier exactly as Mosaico wrote it. Send the
   result as the whole script with the browser pane's `javascript_tool` from a Sales Navigator page (any
   `https://www.linkedin.com/sales/` page; open `https://www.linkedin.com/sales/home` first when the pane is
   elsewhere): `// mosaico run linkedin-salesnav-colleague-connection.js PUBLIC_IDENTIFIER=<candidate> COLLEAGUE_IDENTIFIER=<the colleague's identifier from Mosaico>`.
   The plugin's gate inserts the approved script; never print, retype, paraphrase, reorder, shorten or
   extend it. It sends LinkedIn's own session and CSRF material to LinkedIn only, never returns it, and
   returns only ids: no name, headline or result row leaves the page.
   Fallback, only when the gate refuses the directive: print the approved script without changing it,

   ```bash
   cat "${CLAUDE_PLUGIN_ROOT:-$(dirname "$(dirname "$(find ~/.claude/plugins -path '*/mosaico-claude/browser/linkedin-salesnav-colleague-connection.js' -print -quit)")")}/browser/linkedin-salesnav-colleague-connection.js"
   ```

   then run the printed script with the browser pane's `javascript_tool`, changing only the values on its
   first two lines (the candidate's identifier on the first, the colleague's on the second), in quotes. The
   gate refuses anything else.
3. Pass the script's whole output exactly as returned (every field, `integrity` included) as
   `colleagueConnectionEvidence` on the `outreach_save_lead` call for this candidate and this colleague, with
   everything else you pass for a save. Do this whatever its `state` is (`ok`, `colleague-not-resolved`,
   `candidate-not-resolved` or `error`), and also when `signedIn` is false: Mosaico reads it and decides.
   Never trim, retype or "fix" it, and never leave a field out.
4. Mosaico's answer is final:
   - `skipped` with code `already-connected-to-colleague` (recommended action `continue_sourcing`): the
     candidate is already connected to the colleague. Nothing was saved. This is not a failure and does not
     count toward the target. Source the next candidate and keep going.
   - `blocked` with code `colleague-check-required` (recommended action `run_colleague_check`): nothing was
     saved and the check was missing or unusable. Its `reason` says which: `evidence-missing`,
     `evidence-altered`, `colleague-evidence-malformed`, `colleague-evidence-inconsistent`,
     `observation-stale` (older than ten minutes: run it again just before the save),
     `observation-time-invalid`, `colleague-mismatch` (it was run for another colleague: use the identifier in
     Mosaico's directive), `candidate-mismatch` (it was run for another person: run it for this candidate) or
     `candidate-is-colleague`. Run the script again with the directive Mosaico returned and send the new output
     unchanged; never retype or edit the old one. Do this once per candidate. If Mosaico still blocks it, list
     the candidate as skipped with Mosaico's code and reason and continue. For `candidate-is-colleague`
     running again cannot help: the candidate is the colleague herself, so do not save it, list it as skipped
     and continue.
   - Saved, with a note: `colleague-check-negative-unproven` means the candidate was not found in the
     colleague's connections, or could not be looked up. That is **not** proof that they are not connected
     (she may hide her connections): the Lead is saved with its connection unknown, so never write "not
     connected" about it. `colleague-check-unavailable` means the check cannot work for this colleague (the page was signed out,
     LinkedIn refused it, or she could not be found in Sales Navigator): the candidate was saved without it, and
     Mosaico asks for no more checks for that colleague in this run, so save her next candidates without
     evidence. `colleague-check-cap-reached` means this run has used all its checks: save the rest without evidence.
5. A saved Lead then goes through **Capture connection evidence** as before. The colleague check is never
   passed to `outreach_record_connection_evidence`.

When the script file is missing or the gate refuses it, do not work around it: do not save the candidate for
the colleague, list it as skipped with the reason, and continue.

## Report a sourcing run

Report in plain words, using Mosaico's counts, not memory: for each owner in the quota, the Leads saved
and the quota remaining (name the owner and the member id), the candidates skipped as already connected
to that owner ("skipped as already connected to <owner>: N", from `workflowStatus.colleagueSkips` or the
`colleagueSkips` Mosaico returns with `outreach_get_run`; its entries name the owner), and any shortfall with
its blocker. Those skips are never failures. Also say, from Mosaico's notes, any colleague whose check was
unavailable and why, and that a candidate saved after "not found" has its connection unknown, not "not
connected". A run
that saved nothing is a failed run: report it as failed with Mosaico's code and message (for example
`sourcing_participant_required`, `sourcing_quota_invalid` or the blocker that stopped it), including a run
Mosaico refused at the start. Never report such a run as successful, and never describe a partly filled
quota as complete. If the person answered the quota questions in this run, say whether the quota was saved into the
Source leads schedule or used for this run only.

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
   script identifier after the send and pass its output exactly as returned as `sentInvitationEvidence`
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
   the capture was for another profile: run the script for this Lead's own script identifier. For
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
   `status` is not 200, `state` is `error` or `entries` is empty, stop: leave the Lead unverified, list it as
   skipped with the script's `errorStep` and `status` (they say why) and continue with the next Lead.
5. Call `outreach_record_connection_evidence` with the script's whole output exactly as returned
   (`status`, `signedIn`, `capturedAt`, `state`, `errorStep`, `profileIdentifier`, `requestedIdentifier`,
   `resolvedIdentifier`, `memberUrn`, `entries` and `integrity`; none of them changed), plus `profileUrl`
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
   identifier is the Lead's `scriptIdentifier` from the Mosaico read when it is present (a member id or a public identifier, whatever Mosaico supplies), otherwise the part of the Lead's `linkedInProfileUrl` after `/in/`, with no trailing slash or query, without quotes. This is whatever stands there: a name such as `jane-doe`, or an id that starts with `ACoAA`. Use it as it is; do not look the Lead up or swap one for the other. The plugin's gate inserts the approved script;
   never print, retype, paraphrase, reorder, shorten or extend it.
   Fallback, only when the gate refuses the directive: print the approved script without changing it,

   ```bash
   cat "${CLAUDE_PLUGIN_ROOT:-$(dirname "$(dirname "$(find ~/.claude/plugins -path '*/mosaico-claude/browser/linkedin-sent-invitations.js' -print -quit)")")}/browser/linkedin-sent-invitations.js"
   ```

   then run the printed script with the browser pane's `javascript_tool` from any linkedin.com page, changing
   only the value on its first line to the same identifier, in quotes. Do not paraphrase, reorder,
   shorten or extend it: the gate refuses anything else.
2. If `signedIn` is false, the pane is not signed in to LinkedIn: stop and report it. If `state` is
   `error`, pass it anyway: Mosaico answers `send-evidence-malformed` and tells you to run it again. Its
   `errorStep` (`profile` or `sent-invitations`) and `status` say why; name them in the report.
3. Pass the script's whole output exactly as returned (every field, `integrity` included, and so
   `requestedIdentifier`, `resolvedIdentifier` and `memberUrn` too) as
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
