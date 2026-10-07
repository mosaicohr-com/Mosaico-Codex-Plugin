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

Each scheduled run starts its own Outreach run through the invite-run skill. If Mosaico returns a
blocker, the run stops and reports it; it does not work around it.

Each saved text is a thin routine: it holds only the person's standing answers and names the installed plugin's skill and routine section. The procedure lives in that skill, so every run follows the installed plugin's current procedure and a plugin release never leaves a saved automation stale. Never copy any step of the procedure into an automation text.

**Version stamp.** Each thin text names the minimum plugin version it needs (0.9.6, the first release with the routine sections). A run on an older plugin, or on a plugin that lacks the named section, stops and reports that the plugin needs updating. The Source leads text needs 0.9.8, the first release where the sourcing plan on the Agents drives it. A saved thin text stays valid across later releases: run the installer again only to change an answer or a time.

Fill the placeholders from the person and the current context, never from a fixed value:
`<timezone>` is their local timezone. Ask only if it cannot be found.

The number of Leads per day and who sources them are set on each Agent in Outreach, Agent tab (Leads per day and Sourced by), not in the schedule. A schedule saved with a quota map needs no change, but to drop it follow **Update the standing answers in place** below.

Install **Mosaico Outreach — Source leads** every two hours during business hours, by default 8:00 AM
to 6:00 PM local time, unless the person chose other hours. Its text is:

```text
Use the installed $mosaico:mosaico-outreach-invite-run skill from the mosaico plugin (0.9.8 or later). This is the Source leads routine. Follow that skill's "Source leads routine" section exactly; it is the procedure and it is current for the installed plugin version.

Standing answers for this recurring automation, supplied once by the person: timezone <timezone>; day: the next business day; actions: "source Leads only", then "source Leads and prepare invitation drafts". Proceed without asking which days or which scope.

Use the authenticated LinkedIn browser. A LinkedIn warning or captcha stops the run, which then reports.

If the installed plugin is older than 0.9.8 or has no "Source leads routine" section, stop and report that the plugin needs updating. Report as the skill says.
```

### Update the standing answers in place

Use this when a Source leads automation is already installed and only its standing answers have to be set or changed: its timezone. It also covers an automation saved in the older long form (a text that holds Step 1 and the other steps), which has to become the thin text, and one saved before 0.9.8 that still carries a quota map (the thin text drops it; if it is left, Mosaico ignores the extra standing answer). Another skill may follow these steps; they touch the Source leads automation and nothing else.

1. Ask only for the answer that is missing or changing (the timezone). Ask nothing else. Never ask for a quota: the number of Leads per day and who sources them are set on each Agent in Outreach, Agent tab (Leads per day and Sourced by), not in the schedule.
2. Find the installed "Mosaico Outreach — Source leads" automation, matching by purpose and instructions as under Install. If there is none, say so and offer to install it; do not create one here without being asked.
3. Replace the whole text with the Source leads text above, filled with the saved answers, so the saved text holds only the standing answers. If the saved text is the older long form, read its answers from it: the timezone after "Resolve the current business date and time in"; carry them over unchanged unless the person gave a new one, and drop any quota map. Change nothing else: keep its times, timezone, name, enabled state, working folder and every other saved setting exactly as they are.
4. Read the saved automation back and confirm to the person its name, timezone, enabled state, times (unchanged), that its text is now the thin text, and the standing answers it holds. A write without readback is not completion.

## Keep it apart from Sync data

The two schedules must not overlap. If the person has a Sync data schedule, place every Source leads
time at least 60 minutes before or after the Sync time. The default Sync time is 1:00 PM, which leaves
8:00 AM, 10:00 AM, 12:00 PM, 2:00 PM, 4:00 PM and 6:00 PM. Say in the readback that you did this.

## Install

1. Use the person's local timezone. Inspect existing recurring automations before writing anything.
2. Match existing automations by their Mosaico Outreach purpose and instructions, not name alone. An
   older "Prepare invitations" automation matches Source leads. Do not touch an older "Send approved
   invitations" automation here; tell the person to replace it with Sync data from Claude.
   A saved thin text matches the routine it names ("This is the Source leads routine").
3. If an equivalent schedule already exists, do not duplicate it. Report its name, timezone, enabled
   status and next runs.
4. If a matching schedule exists but differs, update it in place as under **Update the standing answers in
   place**: a text in the older long form is replaced by the thin text, carrying its answers over and keeping
   its times, enabled state, name and every unrelated supported metadata and notification preference.
5. Use the current project or thread context required by the host. Do not ask the person to repeat
   the dates, actions, times or timezone. Ask only when a host-required human decision cannot be
   derived from the current context.
6. Read back the saved automation state and confirm name, local timezone, enabled status, next run
   times and that the saved text is the thin text (it names the skill and its routine section and holds no
   steps). A write attempt without readback is not completion.
