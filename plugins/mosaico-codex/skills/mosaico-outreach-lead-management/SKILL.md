---
name: mosaico-outreach-lead-management
description: Review, update, or create owned Mosaico Outreach Lead records without changing Agents or Messages.
---

# Manage Mosaico Outreach Leads

At the start of every run, ask whether the person wants to update existing Leads, load a new Lead, load a file of already-sourced Leads or ask for a new draft.
This skill manages Lead records only. Never update, delete, classify, approve or send Messages, and
never update Agent definitions. The one exception is asking for a new draft (`outreach_request_redraft`), which
only returns a Message to Draft.

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
2. Call `outreach_start_run` with that URL as `observedLinkedInProfile` and `intent: manage_leads`.
3. Keep the returned `runId` and pass it on every `outreach_get_day` or `outreach_get_follow_ups`
   read and on every `outreach_save_lead`, `outreach_update_lead`, `outreach_record_message`,
   `outreach_deposit_conversation`, `outreach_mark_message_sent` and `outreach_record_delivery_block`
   call. Never pass `ownerUserId` on
   a write; Mosaico takes the owner from the run.
4. Tell a run-level blocker from a one-Lead outcome. A run-level blocker is about the run itself:
   LinkedIn identity mismatch or not registered, the run expired, unknown or foreign, sign-in lost,
   or Mosaico or LinkedIn failing. Only then stop and tell the person what Mosaico says; do not retry
   with a different profile or work around it. Everything else is about one Lead or one Message:
   a `skipped` result, a `blocked` state, a refused write, a `history-mismatch`, a draft that
   already exists, a conflict, a not-found. Record what Mosaico returned, skip that Lead and
   continue with the next one; Mosaico keeps the Lead for a person in To sort. A scheduled run
   never stops for one Lead.
5. Before `outreach_deposit_conversation`, `outreach_mark_message_sent` and
   `outreach_record_delivery_block`, open the Me page again and
   pass the profile you see then as `observedLinkedInProfile`.
6. If an Owner or Admin asks to run for a colleague, pass that member's id as `onBehalfOfMemberId` on
   `outreach_start_run` only. The LinkedIn account must then be that colleague's.

If `outreach_save_lead` or `outreach_deposit_conversation` reports that the profile already exists
under another owner, stop and show the person the owner, Lead and status. Re-send with
`acknowledgeProfileOnOtherOwner: true` only after the person decides to; never set it yourself.

## Update existing Leads

1. Explain that the available Lead fields are name, company, job title, assigned Agent,
   scheduled date, active or dropped status, LinkedIn profile URL, LinkedIn message URL and next
   contact date (`nextTouchOn`).
2. Ask which fields to update.
3. Read `outreach_get_leads` and `outreach_get_agents`, then show a complete Lead report before asking
   which Leads should receive the selected changes. Include every available Lead field and id.
4. Ask the person to select the exact Leads and provide new values. Never infer a bulk target from a
   partial name match.
5. Summarize the exact per-Lead patches and ask for confirmation immediately before calling
   `outreach_update_lead` once per selected Lead.
6. Preserve every unmentioned field. Reread `outreach_get_leads` and report the saved results.

**Next contact date.** When the person asks to contact a Lead again later ("contact Zoe again in
January"), set `changes.nextTouchOn` through `outreach_update_lead`; Mosaico then holds the Lead's
follow-up until that day. You propose one day, written YYYY-MM-DD, from the person's words (if they
name only a period, say which day you propose), and write it only after the person confirms that day
in step 5. `null` clears the booking, when the person asks to contact the Lead now or to cancel the
request. Never work out today or the allowed days yourself: Mosaico judges the day against its own
today in the owner's time zone. If it refuses the day, nothing is saved: the answer is blocked with
one code, `date-invalid`, `date-not-future` or `date-too-far`. Show the person the `earliestAllowed`
and `latestAllowed` days Mosaico returns and ask for a day; call again only with a day the person
confirms.

This skill never dates a follow-up that is already written: that is `sendNotBefore` on a Message, and
this skill never changes Messages. Point the person to the Follow Up tab ("Follow up on or after") or
to the Follow-up routine instead.

## Load a new Lead

1. Read `outreach_get_agents` and show the available active owned Agents.
2. Ask which Agent should own the Lead, then ask for every required Lead value: Lead id, name, company
   or null, job title or null, LinkedIn profile URL or null, LinkedIn message URL or null and
   scheduled date. Do not ask for a connection state: Mosaico records it from LinkedIn evidence.
3. Summarize the complete Lead and ask for confirmation immediately before calling
   `outreach_save_lead`.
4. After saving, do not load or edit Messages in this skill. Ask whether the person wants to load the
   visible conversation now. If yes, invoke `$mosaico:mosaico-outreach-follow-up-run` and let that
   skill deposit the conversation and prepare any follow-up draft.

## Load already-sourced Leads from a file

When the person gives a CSV, a sheet or a list of Leads they already sourced and names the Agent, load them with
`outreach_load_leads`. No run is needed: do not call `outreach_start_run` for this.

1. Read `outreach_get_agents` and confirm the Agent the person named. Mosaico takes the owner from the Agent; pass
   `ownerUserId` only if the person names the owner to check against.
2. Read the file and map its columns to `name`, `linkedInProfileUrl`, `company`, `jobTitle` and `notes`. Show the person
   the mapping and the number of rows, and ask for confirmation before the first call. Leave a field out when the file
   has no column for it.
3. Send pages of at most 200 rows. Mosaico checks every row itself (a name; a full personal LinkedIn profile address,
   `linkedin.com/in/`; field lengths): do not add rules of your own, do not drop or fix rows, and do not choose days.
   Mosaico chooses the days. `notes` are accepted but not stored, and Mosaico says so.
4. After each page, report what Mosaico returned, row by row and in its own words, with the totals:
   - placed, with the day Mosaico gave each row;
   - skipped: `duplicate-own`, `duplicate-in-batch` or `held-by-other-owner` (with who holds it). A skipped row is not a failure;
   - rejected: `invalid-row`, `invalid-url`, `agent-days-full`, `agent-not-sourceable` or `write-failed`.
5. Follow `nextAction`. `load_more`: send the next page. `review_skipped`: stop and show the person the skipped and
   rejected rows. `none`: stop and report the totals. Sending a page again is safe: rows already placed come back as
   `duplicate-own`.
6. Never send a rejected row again with changed data without asking the person first. Show the row, the reason and the
   change you would make, and send it again only after the person says yes.

## Ask for a new draft of a Lead's Message

When the person asks for a Lead's draft to be rewritten, call `outreach_request_redraft` with `leadId`, and with `messageId`
when they name one Message. Without `messageId` it covers every unsent outbound Message the Lead holds. Tell the person
what Mosaico does: the Message goes back to Draft with the reason `person-requested` (an approved one loses its approval),
and it is rewritten by the next Send invitations run (an invitation) or the next Follow-up run (a follow-up). This skill
never writes the new body and never rewrites in place. If Mosaico lists a Message under `alreadyWaiting`, it was already
waiting for a rewrite and was left as it is; say so. If the Lead has no unsent draft, Mosaico refuses in a plain sentence
and writes nothing; show it. Call it only for the Lead and Message the person named.

To move a Lead between colleagues (Owner or Admin only), call `outreach_transfer_lead`, show the
person the preview and let them confirm. Pass `toAgentId` explicitly (null if unknown). If Mosaico says
several destination Leads match, ask the person which one and pass it as `mergeIntoLeadId`.

To move several Leads at once (for example a colleague's share of the Leads just sourced), call
`outreach_transfer_leads` with all their `leadIds`, the two members and the colleague's `toAgentId`.
One preview, one confirmation. Mosaico allows at most 20 Leads per scheduled day for the destination
owner and stops before changing anything if a day would go over or a Lead is blocked; show the person
what it says. In a scheduled run with a standing answer for this move, the confirmation is that
standing answer.

Mosaico decides which member a Lead belongs to from the run; do not try to work that out yourself.
Only Owners and Admins can use Outreach. Mosaico owns validation, Agent assignment checks, persistence and
authorization.
