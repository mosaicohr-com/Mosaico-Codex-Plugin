---
name: mosaico-outreach-schedule-install
description: Install or repair daily Mosaico Outreach invitation preparation and approved-delivery schedules in the user's local timezone.
---

# Install the daily Mosaico Outreach schedule

Use the supported persistent recurring-automation mechanism in this Codex environment. This action
configures personal automation state; it does not change Mosaico workflow records.

1. Use the person's local timezone. Inspect existing recurring automations before writing anything.
2. Match existing automations by their Mosaico Outreach purpose and instructions, not name alone.
3. If equivalent schedules already exist, do not duplicate them. Report their names, timezone,
   enabled status and next runs.
4. If matching schedules exist but differ, update them in place while preserving unrelated supported
   metadata and notification preferences.
5. Prefer two active persistent automations:
   - **Mosaico Outreach — Prepare invitations** — Every day at 8:00 AM local time. Work on today's
     Outreach day. Use the installed `$mosaico:mosaico-outreach-invite-run` skill with the
     already-resolved scope **source Leads and prepare invitation drafts**. Reach exactly 20 qualified invitation
     Leads counting existing ready Leads, and save missing personalized drafts. Never approve or
     send. Preserve partial progress and report exact counts and genuine blockers.
   - **Mosaico Outreach — Send approved invitations** — Every day at 8:00 PM local time. Work only
     on today's Outreach day. Use the installed `$mosaico:mosaico-outreach-invite-run` skill with the
     already-resolved scope **send approved invitations**. Send only exact invitation messages whose
     current Mosaico status is already Approved. Never approve, rewrite, replace or alter an
     invitation. Send through the authenticated LinkedIn browser, verify each result and mark it sent
     in Mosaico only after successful verification. If nothing is approved, send nothing and report
     that outcome.
6. If the host supports only one persistent recurring automation, create one with both daily times
   and explicit time-based morning and evening behavior. Do not weaken either scope.
7. Use the current project or thread context required by the host. Do not ask the person to repeat
   the dates, actions, times or timezone. Ask only when a host-required human decision cannot be
   derived from the current context.
8. Read back the saved automation state and confirm names, local timezone, enabled status and next
   run times. A write attempt without readback is not completion.
