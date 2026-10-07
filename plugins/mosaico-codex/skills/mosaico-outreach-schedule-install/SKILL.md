---
name: mosaico-outreach-schedule-install
description: Install or repair the Mosaico Outreach Source leads schedule in the user's local timezone. Sync data is installed from Claude.
---

# Install the Mosaico Outreach schedules

Use the supported persistent recurring-automation mechanism in this Codex environment. This action
configures personal automation state; it does not change Mosaico workflow records.

## Three schedules, one installable from Codex

Mosaico Outreach runs on three schedules:

- **Mosaico Outreach — Sync data (connections and messaging)** — once a day. It checks LinkedIn
  connections, handles messages, and sends approved follow-ups and invitations. It is the only
  schedule that clicks Connect or sends a message.
- **Mosaico Outreach — Source leads** — every two hours during business hours. It finds Leads and
  writes invitation drafts. It never approves or sends.
- **Mosaico Outreach — Repair** — once a week (by default Sunday at 10:00 AM local time, cron
  `0 10 * * 0`), and on demand. It works the backlog Mosaico lists in its repair queue: connections to
  verify, threads to read, redirected addresses, duplicate Leads and declines. It never approves or sends.

The Codex package cannot capture connection evidence or LinkedIn identity. Only Claude's built-in
browser pane can. So a Sync data schedule installed from Codex must not send anything, and a Repair
schedule installed from Codex could not verify or read anything. Do not install either here. Tell the
person to install Sync data and Repair from Claude, using the Claude plugin's schedule skill. Offer only
the Source leads schedule from Codex. The Codex package's repair-run skill is read-only: it lists the
queue and what a person should do.

## Check before installing

Do these checks first. If one fails, install nothing and tell the person what to do.

1. **Stale skill copies.** Look in `~/.codex/skills/` and `~/.claude/skills/` for folders named
   `mosaico-outreach-*`. They are old unqualified copies. A schedule would resolve to the stale copy
   instead of the plugin. If any exist, refuse to install. Tell the person to archive them, using
   today's date, for example:

   ```bash
   mkdir -p ~/.codex/_archived-YYYY-MM-DD && mv ~/.codex/skills/mosaico-outreach-* ~/.codex/_archived-YYYY-MM-DD/
   ```

   Give the same command for `~/.claude/skills/` if copies are there. Check again after they say it is
   done.
2. **Old Codex automations.** Look for `~/.codex/automations/daily-approved-outreach-sends` and
   `~/.codex/automations/mosaico-lead-preparation`. If either exists and its `automation.toml` says
   `status = "ACTIVE"`, tell the person to disable it. Codex cannot run the connection check, and a
   parallel run would send invitations twice. Do not install anything while one is active.

## The Source leads schedule

Fill the placeholders from the person and the current context, never from a fixed value:
`<timezone>` is their local timezone. Ask only if it cannot be found.

The schedule also needs `<quota map>`, the quota map of member ids to accepted-Lead targets (1 to 100 each,
always including the run owner). Ask once for it, as described below the schedule text.

Install **Mosaico Outreach — Source leads** every two hours during business hours, by default 8:00 AM
to 6:00 PM local time, unless the person chose other hours. Its text is:

```text
Use the installed $mosaico:mosaico-outreach-invite-run skill (plugin mosaico, 0.9.3 or later). This is the Source leads flow of Mosaico Outreach. It only finds Leads and writes invitation drafts. It never approves, sends or messages; the Sync data schedule, installed from Claude, does that.

Resolve the current business date and time in <timezone>. The person has supplied standing answers for this recurring automation: proceed without asking which days or which scope.

Use the authenticated LinkedIn browser. Never read, copy, export or reconstruct a LinkedIn cookie, token or session; never write a LinkedIn script of your own; never read a Connect, Message or Pending button as a connection state; never set a connection state yourself.

Step 1. Open LinkedIn's Me page once and read the profile URL of the signed-in account. Report it as observedLinkedInProfile to outreach_start_run, together with the quota <quota map> as quota. Start one run per scope, each with the same quota <quota map>, and pass its runId on every read and write. If Mosaico blocks the start, stop and report the blocker; do not work around it. If it answers sourcing_participant_required or sourcing_quota_invalid, stop and report that code and what Mosaico says to fix; never start a run without the quota, and never name a colleague that is not in the quota above.

Step 2. Run the $mosaico:mosaico-outreach-invite-run skill with the selected day the next business day and the selected action "source Leads only", using the quota sent at the start. Mosaico assigns the day and keeps the quota. Each Lead is saved directly under the target owner by the run; there is no transfer step. Follow workflowStatus.recommendedAction and reread after every saved Lead.

Step 3. Run the $mosaico:mosaico-outreach-invite-run skill again with the same day and the selected action "source Leads and prepare invitation drafts". This package cannot capture connection evidence. Do not draft for a Lead Mosaico lists as connection unverified; leave it unverified and list it as skipped. Write a missing invitation draft only for a Lead Mosaico lists as verified. Never approve or send an invitation.

Step 4. Stop only when Mosaico says the quota is met, or when Mosaico reports stop_run after the tenth failure. In that case write the sourcing report Mosaico asks for. A skipped candidate or a refused write for one Lead is not a reason to stop.

Step 5. Report separately, using Mosaico's counts, not memory: Leads saved and quota remaining for each owner in the quota map (name and member id), drafts written, candidates skipped with reasons, Leads left unverified, blockers. A run that saved nothing is a failed run: report it as failed with Mosaico's code (for example sourcing_participant_required or sourcing_quota_invalid) and message, also when Mosaico refused the start, and never as successful. Nothing merely drafted may be described as approved or sent. Preserve Mosaico as workflow authority and never modify another owner's records.

Guards: pacing between page loads and run expiry are enforced by Mosaico; a LinkedIn warning or captcha stops the run, which then reports.
```

**Who receives the Leads.**
Ask these two questions once at install time, only if you install or update the Source leads schedule,
and keep the answers as the schedule's standing answers:

1. "Who receives the Leads this schedule sources: only you, you and a colleague, or several members?"
2. "How many accepted Leads should each of them reach per run (1 to 100 each)?"

Read the member ids with `get_team_profiles`: each person's "Person ID" is their member id. The run owner
is the person whose LinkedIn this schedule uses, so their own id is always in the map. Build `<quota map>`
from the answers, for example `{"<run owner member id>": 3, "<colleague member id>": 3}`, and write the
real map into the saved text; never leave a placeholder or an id from memory. Only an Owner or Admin can
name anyone but the run owner in the map. If an id is not found among the active members,
ask again. If the person does not say who receives the Leads or how many, do not install Source leads.
Mosaico refuses a sourcing run that carries neither a quota map nor a colleague, and the application never
guesses one. A Source leads schedule saved before 0.9.3 has no quota map: update it in place with these
answers.

Each scheduled run starts its own Outreach run through the invite-run skill. If Mosaico returns a
blocker, the run stops and reports it; it does not work around it.

## Keep it apart from Sync data

The two schedules must not overlap. If the person has a Sync data schedule, place every Source leads
time at least 60 minutes before or after the Sync time. The default Sync time is 1:00 PM, which leaves
8:00 AM, 10:00 AM, 12:00 PM, 2:00 PM, 4:00 PM and 6:00 PM. Say in the readback that you did this.

## Install

1. Use the person's local timezone. Inspect existing recurring automations before writing anything.
2. Match existing automations by their Mosaico Outreach purpose and instructions, not name alone. An
   older "Prepare invitations" automation matches Source leads. Do not touch an older "Send approved
   invitations" automation here; tell the person to replace it with Sync data from Claude.
3. If an equivalent schedule already exists, do not duplicate it. Report its name, timezone, enabled
   status and next runs.
4. If a matching schedule exists but differs, update it in place while preserving unrelated supported
   metadata and notification preferences.
5. Use the current project or thread context required by the host. Do not ask the person to repeat
   the dates, actions, times or timezone. Ask only when a host-required human decision cannot be
   derived from the current context.
6. Read back the saved automation state and confirm name, local timezone, enabled status and next run
   times. A write attempt without readback is not completion.
