---
name: mosaico-outreach-lead-management
description: Review, update, or create owned Mosaico Outreach Lead records without changing Agents or Messages.
---

# Manage Mosaico Outreach Leads

At the start of every run, ask whether the person wants to update existing Leads or load a new Lead.
This skill manages Lead records only. Never update, delete, classify, approve or send Messages, and
never update Agent definitions.

## Start the run

1. Open LinkedIn's Me page in the authenticated browser and read the profile URL of the signed-in
   account. Report what you see; do not decide or correct it.
2. Call `outreach_start_run` with that URL as `observedLinkedInProfile` and `intent: manage_leads`.
3. Keep the returned `runId` and pass it on every `outreach_get_day` or `outreach_get_follow_ups`
   read and on every `outreach_save_lead`, `outreach_update_lead`, `outreach_record_message`,
   `outreach_deposit_conversation` and `outreach_mark_message_sent` call. Never pass `ownerUserId` on
   a write; Mosaico takes the owner from the run.
4. If Mosaico returns a blocker at any step, stop and tell the person what it says. Do not retry with
   a different profile or work around it. In a scheduled run, a blocker means stop and report.
5. Before `outreach_deposit_conversation` and `outreach_mark_message_sent`, open the Me page again and
   pass the profile you see then as `observedLinkedInProfile`.
6. If an Owner or Admin asks to run for a colleague, pass that member's id as `onBehalfOfMemberId` on
   `outreach_start_run` only. The LinkedIn account must then be that colleague's.

If `outreach_save_lead` or `outreach_deposit_conversation` reports that the profile already exists
under another owner, stop and show the person the owner, Lead and status. Re-send with
`acknowledgeProfileOnOtherOwner: true` only after the person decides to; never set it yourself.

## Update existing Leads

1. Explain that the available Lead fields are name, company, job title, assigned Agent, connected
   state, scheduled date, active or dropped status, LinkedIn profile URL and LinkedIn message URL.
2. Ask which fields to update.
3. Read `outreach_get_leads` and `outreach_get_agents`, then show a complete Lead report before asking
   which Leads should receive the selected changes. Include every available Lead field and id.
4. Ask the person to select the exact Leads and provide new values. Never infer a bulk target from a
   partial name match.
5. Summarize the exact per-Lead patches and ask for confirmation immediately before calling
   `outreach_update_lead` once per selected Lead.
6. Preserve every unmentioned field. Reread `outreach_get_leads` and report the saved results.

## Load a new Lead

1. Read `outreach_get_agents` and show the available active owned Agents.
2. Ask which Agent should own the Lead, then ask for every required Lead value: Lead id, name, company
   or null, job title or null, LinkedIn profile URL or null, LinkedIn message URL or null, connected
   state and scheduled date.
3. Summarize the complete Lead and ask for confirmation immediately before calling
   `outreach_save_lead`.
4. After saving, do not load or edit Messages in this skill. Ask whether the person wants to load the
   visible conversation now. If yes, invoke `$mosaico:mosaico-outreach-follow-up-run` and let that
   skill deposit the conversation and prepare any follow-up draft.

To move a Lead between colleagues (Owner or Admin only), call `outreach_transfer_lead`, show the
person the preview and let them confirm. Pass `toAgentId` explicitly (null if unknown). If Mosaico says
several destination Leads match, ask the person which one and pass it as `mergeIntoLeadId`.

Mosaico decides which member a Lead belongs to from the run; do not try to work that out yourself.
Only Owners and Admins can use Outreach. Mosaico owns validation, Agent assignment checks, persistence and
authorization.
