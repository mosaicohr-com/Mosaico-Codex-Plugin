---
name: mosaico-outreach-schedule-install
description: Install or repair the three Mosaico Outreach schedules, Sync data, Source leads and Repair, in the user's local timezone.
---

# Install the Mosaico Outreach schedules

Use Claude Desktop's supported persistent local scheduled-task mechanism. These workflows require the
person's authenticated LinkedIn browser, so do not substitute a cloud routine that lacks that local
browser session. This action configures personal schedule state; it does not change Mosaico records.

## Check before installing

Do these checks first. If one fails, install nothing and tell the person what to do.

1. **Browser permissions.** Read `~/.claude/settings.json`. All three of
   `"mcp__Claude_Browser__javascript_tool"`, `"mcp__Claude_Browser__computer"` and
   `"mcp__Claude_Browser__browser_batch"` must be in `permissions.allow`. If the file is missing or
   any rule is absent, do not install. Print this snippet for the person to add, merged into any
   existing `permissions.allow` list:

   ```json
   {
     "permissions": {
       "allow": [
         "mcp__Claude_Browser__javascript_tool",
         "mcp__Claude_Browser__computer",
         "mcp__Claude_Browser__browser_batch"
       ]
     }
   }
   ```

   Say in three sentences: scheduled sessions ignore project-level rules, so without these three
   user-level rules every browser step waits for a person who is not there. The browser pane batches a
   click with a wait and a screenshot through the `browser_batch` tool, so without that rule every
   Connect or Send click is blocked. Once the rules exist, the plugin's
   browser-script gate stays the safety net, because it still refuses any script that is not an
   approved capture script. The plugin cannot write that file; the person must edit it. Offer to
   continue once they have.
2. **Stale skill copies.** Look in `~/.codex/skills/` and `~/.claude/skills/` for folders named
   `mosaico-outreach-*`. They are old unqualified copies. A schedule would resolve to the stale copy
   instead of the plugin. If any exist, refuse to install. Tell the person to archive them, using
   today's date, for example:

   ```bash
   mkdir -p ~/.codex/_archived-YYYY-MM-DD && mv ~/.codex/skills/mosaico-outreach-* ~/.codex/_archived-YYYY-MM-DD/
   ```

   Give the same command for `~/.claude/skills/` if copies are there. Check again after they say it is
   done.
3. **Old Codex automations.** Look for `~/.codex/automations/daily-approved-outreach-sends` and
   `~/.codex/automations/mosaico-lead-preparation`. If either exists and its `automation.toml` says
   `status = "ACTIVE"`, tell the person to disable it. Codex cannot run the connection check, and a
   parallel run would send invitations twice. Do not install the Sync data schedule while one is active.
4. **Non-production Mosaico server.** Look for an MCP server that points at a non-production Mosaico
   address, in the project's `.mcp.json` and in the project and user entries of `~/.claude.json`
   (`mcpServers`; the project entry is the one for the folder the schedules run in). An address that
   contains `amplifyapp.com`, `stage`, `staging`, `test` or `localhost` is not production. If one exists,
   refuse to install. Tell the person to remove it before installing: a scheduled run can pick it
   because stage and production share organisation ids, and it would then write to stage. A stage
   server needed on purpose can be added back under a distinct name such as `mosaico-stage`, in a
   session that is not a scheduled run. Check again after they say it is done.
5. **Production Mosaico connector.** The plugin ships no Mosaico server of its own, so every run uses
   the person's own connector. A Mosaico connector pointing at `https://app.mosaico.one` must be
   connected and signed in, in Claude's connectors (not `/mcp`). Confirm it by looking for a Mosaico tool
   such as `outreach_start_run` in the available tools. If there is none, install nothing and tell the
   person to connect it in Claude's connectors, sign in with their own Mosaico account, and run this
   installer again. The `outreach_start_run` answer names the environment (`environmentName`); a run on anything but production stops.

## Set up a second person

Use this when another person, for example a colleague who sources and delivers for herself, wants her own
schedules. Everything below happens on her own Mac. Go through the steps in order and stop at the first
one that fails.

1. **Claude desktop app and plugin.** The Claude desktop app is installed on her Mac, with the Mosaico
   plugin installed from the marketplace, version 0.6.1 or later.
2. **Her Mosaico account.** Her own Claude has a Mosaico connector pointing at `https://app.mosaico.one`,
   connected in Claude's connectors (not `/mcp`) and signed in as her own Mosaico account, not anyone
   else's. The plugin brings no Mosaico server, so nothing works until she connects it. She must be an
   active member of the organisation. An Owner or Admin can check this in Outreach, Agent tab.
3. **Her LinkedIn.** Her LinkedIn is signed in inside Claude's built-in browser pane, not in Chrome or
   any other browser.
4. **The three allow rules.** The three rules are in her own `~/.claude/settings.json`. Run the
   **Browser permissions** check above on her Mac and, if a rule is missing, print the snippet for her:

   ```json
   {
     "permissions": {
       "allow": [
         "mcp__Claude_Browser__javascript_tool",
         "mcp__Claude_Browser__computer",
         "mcp__Claude_Browser__browser_batch"
       ]
     }
   }
   ```

5. **Her LinkedIn profile is registered in Mosaico.** It must be registered in Mosaico Outreach, Agent
   tab, "LinkedIn profile". Check it yourself: open LinkedIn's Me page in the pane, read her public
   identifier, and call `outreach_start_run` with intent `inspect_day` and that identifier. If Mosaico
   answers `linkedin_identity_not_registered`, tell her to register the profile there, or to ask an
   Owner to do it, and check again after she says it is done. Do not install anything until the check
   passes.
6. **Run this installer.** It installs her Sync data schedule and her Repair schedule. Ask once whether
   she sources Leads herself; only if she does, also install her Source leads schedule. Her Source leads schedule needs no
   quota: she sets Leads per day and Leads per run on her Agent in Outreach (Agent tab) and may name a colleague as "Sourced by".

Each person's Sync data schedule runs on that person's own Mac, in that person's own browser pane, and
sends only from that person's account. Her Repair schedule works only her own backlog and never sends.
Nobody's run touches another owner's Leads.

## The three schedules

Install three active persistent local scheduled tasks. Each scheduled run starts its own Outreach run
through the invite-run, follow-up-run or repair-run skill. If Mosaico returns a blocker, the run stops and
reports it; it does not work around it.

Each saved text is a thin routine: it holds only the person's standing answers and names the installed plugin's skill and routine section. The procedure lives in that skill, so every run follows the installed plugin's current procedure and a plugin release never leaves a saved schedule stale. Never copy any step of the procedure into a schedule text.

**Version stamp.** Each thin text names the minimum plugin version it needs (0.9.6, the first release with the routine sections). A run on an older plugin, or on a plugin that lacks the named section, stops and reports that the plugin needs updating. The Source leads text needs 0.9.9, the first release where Leads per run and the application's day placement drive it. A saved thin text stays valid across later releases: run the installer again only to change an answer or a time.

Fill the placeholders from the person and the current context, never from a fixed value:
`<public identifier>` is the last part of the person's LinkedIn profile address (the part after
`/in/`); `<timezone>` is their local timezone. Ask only if one of them cannot be found.

Leads per day and Leads per run are set on each Agent in Outreach, Agent tab; an Agent is sourced only when it is on and both are set. Who sources an Agent (Sourced by) is set there too, and Mosaico files the Leads into days itself, so none of it is in the schedule. A schedule saved with a quota map or a day needs no change, but to drop it follow **Update the standing answers in place** below.

**Mosaico Outreach — Sync data (connections and messaging)** — once a day, at 1:00 PM local time unless
the person chose another time. This is the only schedule that clicks Connect or sends a message. Its
text is:

```text
Use the installed mosaico:mosaico-outreach-follow-up-run skill from the mosaico plugin (0.9.6 or later). This is the Sync data routine. Follow that skill's "Sync data routine" section exactly; it is the procedure (it chains the mosaico:mosaico-outreach-invite-run skill for the approved invitations) and it is current for the installed plugin version.

Standing answers for this recurring automation, supplied once by the person: timezone <timezone>; LinkedIn public identifier <public identifier>; scope: follow-ups across all dates with the action "one pass per thread", then invitations for today with the action "send approved invitations". Proceed without asking which days or which scope.

Do every LinkedIn step in Claude's built-in browser pane, signed in to my LinkedIn (<public identifier>). A LinkedIn warning or captcha stops the run, which then reports.

If the installed plugin is older than 0.9.6 or has no "Sync data routine" section, stop and report that the plugin needs updating. Report as the skill says.
```

**Mosaico Outreach — Source leads** — every two hours during business hours, by default 8:00 AM to
6:00 PM local time, unless the person chose other hours. It runs from any linkedin.com page. It never
approves or sends anything. Its text is:

```text
Use the installed mosaico:mosaico-outreach-invite-run skill from the mosaico plugin (0.9.9 or later). This is the Source leads routine. Follow that skill's "Source leads routine" section exactly; it is the procedure and it is current for the installed plugin version.

Standing answers for this recurring automation, supplied once by the person: timezone <timezone>; LinkedIn public identifier <public identifier>; actions: "source Leads only", then "source Leads and prepare invitation drafts". Proceed without asking which days or which scope.

Do every LinkedIn step in Claude's built-in browser pane, from any linkedin.com page, signed in to my LinkedIn (<public identifier>). A LinkedIn warning or captcha stops the run, which then reports.

If the installed plugin is older than 0.9.9 or has no "Source leads routine" section, stop and report that the plugin needs updating. Report as the skill says.
```

### Update the standing answers in place

Use this when a schedule is already installed and only its standing answers have to be set or changed: its timezone or its LinkedIn public identifier. It also covers a schedule saved in the older long form (a text that holds Step 1 and the other steps), which has to become the thin text, and a Source leads schedule saved before 0.9.9 that still carries a quota map or a day (the thin text drops them; if they are left, Mosaico ignores the extra standing answers). Another skill may follow these steps; they touch the one schedule and nothing else.

1. Ask only for the answer that is missing or changing (the timezone or the LinkedIn public identifier). Ask nothing else. Never ask for a quota: Leads per day, Leads per run and who sources them are set on each Agent in Outreach, Agent tab, not in the schedule.
2. Find the installed task, for example "Mosaico Outreach — Source leads", matching by purpose and instructions as under Install. If there is none, say so and offer to install it; do not create one here without being asked.
3. Replace the whole text with the thin text for that routine above, filled with the saved answers, so the saved text holds only the standing answers. If the saved text is the older long form, read its answers from it: the timezone after "Resolve the current business date and time in" and the public identifier in the brackets after "signed in to my LinkedIn"; carry them over unchanged unless the person gave a new one, and drop any quota map. Change nothing else: keep its cron times, timezone, name, enabled state, working folder and every other saved setting exactly as they are.
4. Read the saved task back and confirm to the person its name, timezone, enabled state, times (unchanged), that its text is now the thin text, and the standing answers it holds. A write without readback is not completion.

**Mosaico Outreach — Repair** — once a week, by default Sunday at 10:00 AM local time (cron
`0 10 * * 0`) unless the person chose another day or time, and also whenever the person asks for it. It
works the backlog Mosaico lists in its repair queue, up to the cap Mosaico sets for one run. It never
approves, sends or messages; the Sync data schedule does that. Its text is:

```text
Use the installed mosaico:mosaico-outreach-repair-run skill from the mosaico plugin (0.9.6 or later). This is the Repair routine. Follow that skill's "Repair routine" section exactly; it is the procedure and it is current for the installed plugin version.

Standing answers for this recurring automation, supplied once by the person: timezone <timezone>; LinkedIn public identifier <public identifier>; scope: the whole repair queue, up to the cap Mosaico sets for one run. Proceed without asking which scope.

Do every LinkedIn step in Claude's built-in browser pane, signed in to my LinkedIn (<public identifier>). A LinkedIn warning or captcha stops the run, which then reports.

If the installed plugin is older than 0.9.6 or has no "Repair routine" section, stop and report that the plugin needs updating. Report as the skill says.
```

## Keep the schedules apart

The schedules must not overlap. Place every Source leads time at least 60 minutes before or after the
Sync data time. With the default 1:00 PM Sync, the default Source leads times are 8:00 AM, 10:00 AM,
12:00 PM, 2:00 PM, 4:00 PM and 6:00 PM. If the person moves the Sync time, move or drop any Source
leads time that falls closer than 60 minutes to it. Say in the readback that you did this.

Repair runs once a week, and its default is Sunday at 10:00 AM. On the day Repair runs, keep every Sync
data and Source leads time at least 60 minutes from the Repair time too: if either schedule also runs on
that day and a time falls closer than 60 minutes, move or drop that Sync data or Source leads time, never
the Repair time the person chose, and say so in the readback. Repair never sends, so it never takes the
place of Sync data.

## Install

1. Use the person's local timezone and current working folder. Inspect existing scheduled tasks
   before writing anything.
2. Match existing tasks by their Mosaico Outreach purpose and instructions, not name alone. An older
   "Prepare invitations" task matches Source leads. An older "Send approved invitations" task matches
   Sync data. A task that works the repair queue matches Repair. Only one task may send, so update the old
   sending task in place or disable it.
   A saved thin text matches the routine it names ("This is the Sync data routine").
3. If equivalent tasks already exist, do not duplicate them. Report their names, timezone, enabled
   status and next runs.
4. If matching tasks exist but differ, update them in place as under **Update the standing answers in
   place**: a text in the older long form is replaced by the thin text, carrying its answers over and keeping
   its cron times, enabled state, name and every unrelated supported metadata and permission setting.
5. If the host supports only one persistent local task, install Sync data alone and tell the person
   that Source leads and Repair are not installed. Do not merge the schedules or weaken any of them.
6. Do not ask the person to repeat the dates, actions, times, folder or timezone. Ask only when a
   host-required human decision cannot be derived from the current context.
7. Read back the saved task state and confirm names, local timezone, enabled status, next run
   times and that each saved text is the thin text (it names the skill and its routine section and holds
   no steps). For Source leads, confirm that every time is at least 60 minutes from the Sync time. For Repair,
   confirm the cron `0 10 * * 0` (or the person's own day and time), and that Repair is also available on
   demand through `/mosaico:mosaico-outreach-repair-run`. A write attempt without readback is not
   completion.
