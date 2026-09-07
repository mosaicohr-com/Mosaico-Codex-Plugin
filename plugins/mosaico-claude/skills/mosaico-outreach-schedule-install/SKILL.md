---
name: mosaico-outreach-schedule-install
description: Install or repair daily Mosaico Outreach invitation preparation and approved-delivery schedules in the user's local timezone.
---

# Install the daily Mosaico Outreach schedule

Use Claude Desktop's supported persistent local scheduled-task mechanism. These workflows require the
person's authenticated LinkedIn browser, so do not substitute a cloud routine that lacks that local
browser session. This action configures personal schedule state; it does not change Mosaico records.

1. Use the person's local timezone and current working folder. Inspect existing scheduled tasks
   before writing anything.
2. Match existing tasks by their Mosaico Outreach purpose and instructions, not name alone.
3. If equivalent tasks already exist, do not duplicate them. Report their names, timezone, enabled
   status and next runs.
4. If matching tasks exist but differ, update them in place while preserving unrelated supported
   metadata and permission settings.
5. Prefer two active persistent local scheduled tasks:
   - **Mosaico Outreach — Prepare invitations** — Every day at 8:00 AM local time. Work on today's
     Outreach day. Use `/mosaico:mosaico-outreach-invite-run` with the already-resolved scope
     **source Leads and prepare invitation drafts**. Reach exactly 20 qualified invitation Leads
     counting existing ready Leads, and save missing personalized drafts. Never approve or send.
     Preserve partial progress and report exact counts and genuine blockers.
   - **Mosaico Outreach — Send approved invitations** — Every day at 8:00 PM local time. Work only
     on today's Outreach day. Use `/mosaico:mosaico-outreach-invite-run` with the already-resolved
     scope **send approved invitations**. Send only exact invitation messages whose current Mosaico
     status is already Approved. Never approve, rewrite, replace or alter an invitation. Send through
     the authenticated LinkedIn browser, verify each result and mark it sent in Mosaico only after
     successful verification. If nothing is approved, send nothing and report that outcome.
6. If the host supports only one persistent local task, create one with both daily times and explicit
   time-based morning and evening behavior. Do not weaken either scope.
7. Do not ask the person to repeat the dates, actions, times, folder or timezone. Ask only when a
   host-required human decision cannot be derived from the current context.
8. Read back the saved task state and confirm names, local timezone, enabled status and next run
   times. A write attempt without readback is not completion.
