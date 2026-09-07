---
name: mosaico-outreach-lead-management
description: Review, update, or create owned Mosaico Outreach Lead records without changing Agents or Messages.
---

# Manage Mosaico Outreach Leads

At the start of every run, ask whether the person wants to update existing Leads or load a new Lead.
This skill manages Lead records only. Never update, delete, classify, approve or send Messages, and
never update Agent definitions.

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
   visible conversation now. If yes, invoke `/mosaico:mosaico-outreach-follow-up-run` and let that
   skill deposit the conversation and prepare any follow-up draft.

Never modify another owner's Lead. Mosaico owns validation, Agent assignment checks, persistence and
authorization.
