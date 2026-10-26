---
name: mosaico-outreach-schedule-install
description: Install or repair the Mosaico Outreach schedules, Send invitations, Follow-up, Withdraw stale invitations, Source leads (an own lane and a colleagues lane), Routines report and Repair, and publish the person's Routines Board, in the user's local timezone.
---

# Install the Mosaico Outreach schedules

Use Claude Desktop's supported persistent local scheduled-task mechanism. These workflows require the
person's authenticated LinkedIn browser, so do not substitute a cloud routine that lacks that local
browser session. Create and change the tasks with the app's scheduled-tasks tools (`list_scheduled_tasks`,
`create_scheduled_task`, `update_scheduled_task`); a cron is read in the person's local time. This action
configures personal schedule state. The one thing it tells Mosaico is when each schedule runs, so the Routines section of
Outreach, Agent tab can show it (see **Record the schedules in Mosaico**); it changes no Lead, Message, Agent or run.

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
   parallel run would send invitations twice. Do not install the Send invitations, Follow-up or Withdraw stale invitations schedule while one is active.
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
6. **Run this installer.** It installs her Send invitations, Follow-up, Withdraw stale invitations and Routines report schedules, her own Routines Board (a board is per person; never reuse another person's address) and her Repair schedule. If she has the older single Sync data task, the installer retires it once the three new ones exist. Ask once whether
   she sources Leads herself; if she does not, install no Source leads task for her. Only if she does, also install her
   own-lane Source leads schedule, and add the colleagues lane only if she also sources Leads for a colleague (an Agent of
   a colleague that names her in Sourced by). Her Source leads schedules need no quota: she sets Leads per day and Leads
   per run on her Agent in Outreach (Agent tab) and may name a colleague as "Sourced by".

Each person's Send invitations, Follow-up and Withdraw stale invitations schedules run on that person's own Mac, in that person's own browser pane, and
sends only from that person's account. Her Repair schedule works only her own backlog and never sends.
Nobody's run touches another owner's Leads.

## The schedules

Install persistent local scheduled tasks for six routines: Send invitations, Follow-up, Withdraw stale invitations, Source leads, Routines report and Repair. Source
leads is installed as two tasks, one per lane (own and colleagues), so there are up to seven tasks. All are active except Withdraw stale invitations, which is installed paused (see its entry). The older single "Sync data (connections and messaging)" task is superseded by Send invitations, Follow-up and Withdraw stale invitations and is retired (see Install). Each scheduled run
starts its own Outreach run through the invite-run, follow-up-run or repair-run skill. If Mosaico returns a blocker, the run stops and
reports it; it does not work around it.

Each saved text is a thin routine: it holds only the person's standing answers and names the installed plugin's skill and routine section. The procedure lives in that skill, so every run follows the installed plugin's current procedure and a plugin release never leaves a saved schedule stale. Never copy any step of the procedure into a schedule text.

**Version stamp.** Each thin text names the minimum plugin version it needs (0.9.6, the first release with the routine sections). A run on an older plugin, or on a plugin that lacks the named section, stops and reports that the plugin needs updating. From 0.9.24 it is 0.9.24 for the Send invitations, Follow-up, Withdraw stale invitations, Source leads (both lanes) and Routines report texts: 0.9.24 is the first release whose Send invitations and Follow-up routines rewrite the drafts an Agent change returned to Draft (the application's rewrite step and `rewrite-draft` stage) and whose routines record the run on the Routines Board, and the first release with the "Routines report routine" section. Install the 0.9.24 texts only after the Mosaico release that ships PRs 2053, 2057 and 2058 is live and promoted (the plugin's changelog for 0.9.24 names it). Earlier stamps stay valid history: 0.9.13 stopped Source leads writing drafts and added the `sourcing scope` line, 0.9.15 split the old Sync data routine into Send invitations and Withdraw stale invitations (a saved Sync data text is retired, never moved to a new stamp), and 0.9.18 added dated follow-ups to Follow-up. The Repair text stays at 0.9.6 and valid across later releases. Run the installer again to move a saved text from an earlier stamp to 0.9.24, to change an answer or a time, or to add the board line.

**The Routines Board line.** After the standing answers, every routine text (all of them except Repair) carries one more paragraph of its own, the single line `routines board: <board url>`, the address of the person's board (see **The Routines Board** below). It keeps the texts thin: the routine skills read the address from that line and write their run to the board as their last step; a text with no such line skips that step silently.

Fill the placeholders from the person and the current context, never from a fixed value:
`<public identifier>` is the last part of the person's LinkedIn profile address (the part after
`/in/`); `<timezone>` is their local timezone. Ask only if one of them cannot be found.

Leads per day and Leads per run are set on each Agent in Outreach, Agent tab; an Agent is sourced only when it is on and both are set. Who sources an Agent (Sourced by) is set there too, and Mosaico files the Leads into days itself, so none of it is in the schedule. A schedule saved with a quota map or a day needs no change, but to drop it follow **Update the standing answers in place** below.

**Mosaico Outreach — Send invitations** — once a day, at 6:00 AM local time (`0 6 * * *`) unless the person chose another time. It works the one
ordered list Mosaico keeps for the person's own Leads: it sends the invitations that are already approved, rewrites the invitation
drafts an Agent change returned to Draft (from 0.9.24; the application orders them after the sends, on every scheduled day),
checks the connections of the Leads placed on later days that Mosaico hands out, then writes the missing invitation drafts for those
found not connected; Mosaico sets how many checks and drafts one run gets (`checkLimit` and `draftLimit`; rewrites share the draft
limit and go first). The text below names the routine section of the installed plugin. It sends in the morning what the person
approved the evening before, and drafts the coming days. It never approves a draft and does nothing else: no follow-ups and no
withdrawals. Its text is:

```text
Use the installed mosaico:mosaico-outreach-invite-run skill from the mosaico plugin (0.9.24 or later). This is the Send invitations routine. Follow that skill's "Send invitations routine" section exactly; it is the procedure and it is current for the installed plugin version.

Standing answers for this recurring automation, supplied once by the person: timezone <timezone>; LinkedIn public identifier <public identifier>; scope: invitations for today with the actions "write missing invitation drafts" and "send approved invitations". Proceed without asking which days or which scope.

routines board: <board url>

Do every LinkedIn step in Claude's built-in browser pane, signed in to my LinkedIn (<public identifier>). A LinkedIn warning or captcha stops the run, which then reports.

If the installed plugin is older than 0.9.24 or has no "Send invitations routine" section, stop and report that the plugin needs updating. Report as the skill says.
```

**Mosaico Outreach — Follow-up** — twice a day, at 6:45 PM and 10:45 PM local time (`45 18,22 * * *`) unless the person chose another review window (see **Ask once about the review window**). The 6:45 PM run drafts for the evening review; the 10:45 PM run sends what the person approved. It works the follow-up
queue Mosaico keeps (a run with intent `follow_up_pass`): it captures the connections list when it is due, verifies the connections
still unknown, reads the threads that need reading (the Leads who replied and the Leads who did not), writes the missing follow-up
drafts and sends the follow-ups that are already approved, one pass per thread across all dates. From 0.9.17 it also makes the
repairs Mosaico can decide from evidence for its own Leads (it fixes an address LinkedIn has redirected and drops a Lead who said
no) and names the Leads it skipped in its report. From 0.9.18 it books a later touch when a conversation asks to be picked up later
("talk in January": a day on the follow-up draft, or on the Lead when no draft is due yet), leaves work booked for a later day alone
until its day and reports the bookings it made, changed or cleared. From 0.9.24 it also rewrites the follow-up drafts an Agent change returned to Draft (stage `rewrite-draft`: it reads the thread first, then writes the first message without repeating the invitation's words, and records it with the existing message id; it never approves). It sends no invitation, saves no Lead, never calls the link tool
itself (Mosaico links a pair its thread deposit proves by member id) and withdraws nothing. Its text is:

```text
Use the installed mosaico:mosaico-outreach-follow-up-run skill from the mosaico plugin (0.9.24 or later). This is the Follow-up routine. Follow that skill's "Follow-up routine" section exactly; it is the procedure and it is current for the installed plugin version.

Standing answers for this recurring automation, supplied once by the person: timezone <timezone>; LinkedIn public identifier <public identifier>; scope: follow-ups across all dates with the action "one pass per thread". Proceed without asking which days or which scope.

routines board: <board url>

Do every LinkedIn step in Claude's built-in browser pane, signed in to my LinkedIn (<public identifier>). A LinkedIn warning or captcha stops the run, which then reports.

If the installed plugin is older than 0.9.24 or has no "Follow-up routine" section, stop and report that the plugin needs updating. Report as the skill says.
```

**Mosaico Outreach — Withdraw stale invitations** — once a day, at 11:30 PM local time (`30 23 * * *`) unless the person chose another time,
installed paused (disabled) until the person has tested it: create it, set it disabled, read it back as disabled, and tell the person
to run it once on demand, read its report, and say when to turn it on; enable it only on their word. It withdraws
the pending invitations Mosaico lists as stale, up to the cap Mosaico sets for one run, and records each one. Mosaico owns the 30-day
rule; the routine never works it out from dates. It never sends anything and never clicks Connect. Its text is:

```text
Use the installed mosaico:mosaico-outreach-invite-run skill from the mosaico plugin (0.9.24 or later). This is the Withdraw stale invitations routine. Follow that skill's "Withdraw stale invitations routine" section exactly; it is the procedure and it is current for the installed plugin version.

Standing answers for this recurring automation, supplied once by the person: timezone <timezone>; LinkedIn public identifier <public identifier>; scope: the whole withdraw queue, up to the cap Mosaico sets for one run. Proceed without asking which scope.

routines board: <board url>

Do every LinkedIn step in Claude's built-in browser pane, signed in to my LinkedIn (<public identifier>). A LinkedIn warning or captcha stops the run, which then reports.

If the installed plugin is older than 0.9.24 or has no "Withdraw stale invitations routine" section, stop and report that the plugin needs updating. Report as the skill says.
```

The daily schedules share the person's one LinkedIn account and one browser pane, so they must not overlap: the defaults sit at least 45 minutes apart, and a person with many invitations to send should space them further apart so one run has finished before the next starts.

**Mosaico Outreach — Source leads (own)** — every day at 12:00 AM and 3:00 AM, at `0 0,3 * * *`
local time (cron, explicit hours), unless the person chose other hours. It works the Agents the person owns. It runs from
any linkedin.com page and never writes invitation drafts, approves or sends anything. Its text is:

```text
Use the installed mosaico:mosaico-outreach-invite-run skill from the mosaico plugin (0.9.24 or later). This is the Source leads routine. Follow that skill's "Source leads routine" section exactly; it is the procedure and it is current for the installed plugin version.

Standing answers for this recurring automation, supplied once by the person: timezone <timezone>; LinkedIn public identifier <public identifier>; sourcing scope: own; action: "source Leads only". Proceed without asking which days or which scope.

routines board: <board url>

Do every LinkedIn step in Claude's built-in browser pane, from any linkedin.com page, signed in to my LinkedIn (<public identifier>). A LinkedIn warning or captcha stops the run, which then reports.

If the installed plugin is older than 0.9.24 or has no "Source leads routine" section, stop and report that the plugin needs updating. Report as the skill says.
```

**Mosaico Outreach — Source leads (colleagues)** — every day at 1:30 AM and 4:30 AM, at `30 1,4 * * *`
local time (cron, explicit hours), unless the person chose other hours. It works the Agents of a colleague that name the
person in Sourced by. Install it only for a person who sources for a colleague. Its text is the own-lane text with only
the scope line (and this task's title) different:

```text
Use the installed mosaico:mosaico-outreach-invite-run skill from the mosaico plugin (0.9.24 or later). This is the Source leads routine. Follow that skill's "Source leads routine" section exactly; it is the procedure and it is current for the installed plugin version.

Standing answers for this recurring automation, supplied once by the person: timezone <timezone>; LinkedIn public identifier <public identifier>; sourcing scope: colleagues; action: "source Leads only". Proceed without asking which days or which scope.

routines board: <board url>

Do every LinkedIn step in Claude's built-in browser pane, from any linkedin.com page, signed in to my LinkedIn (<public identifier>). A LinkedIn warning or captcha stops the run, which then reports.

If the installed plugin is older than 0.9.24 or has no "Source leads routine" section, stop and report that the plugin needs updating. Report as the skill says.
```

The two lanes share the person's one LinkedIn account and one browser pane. Mosaico lets only one of their Source leads runs work at a time, so a lane that starts while the other is still working is told to wait (nothing is lost, and it is not a failure), and the start times below keep that rare.

**Mosaico Outreach — Routines report** — twice a day, at 6:45 AM and 11:45 PM local time (`45 6,23 * * *`) unless the person chose other times. It
reads the latest scheduled run of each Mosaico Outreach routine and makes sure the Routines Board shows it: it is the fallback for a
routine that could not write to the board itself. It opens no LinkedIn page, uses no Mosaico connector and changes no Mosaico record,
so it does not take part in the spacing rules below beyond not starting at the same minute as another task. Its text is:

```text
Use the installed mosaico:mosaico-outreach-follow-up-run skill from the mosaico plugin (0.9.24 or later). This is the Routines report routine. Follow that skill's "Routines report routine" section exactly; it is the procedure and it is current for the installed plugin version.

Standing answers for this recurring automation, supplied once by the person: timezone <timezone>; scope: the latest scheduled run of each Mosaico Outreach routine. Proceed without asking which scope.

routines board: <board url>

If the installed plugin is older than 0.9.24 or has no "Routines report routine" section, stop and report that the plugin needs updating. Report as the skill says.
```

### Update the standing answers in place

Use this when a schedule is already installed and only its standing answers have to be set or changed: its timezone or its LinkedIn public identifier. It also covers a schedule saved in the older long form (a text that holds Step 1 and the other steps), which has to become the thin text, a Source leads schedule saved before 0.9.9 that still carries a quota map or a day (the thin text drops them; if they are left, Mosaico ignores the extra standing answers), a Source leads schedule with no `sourcing scope` line, which becomes the own lane, a Source leads schedule that still names the action "source Leads and prepare invitation drafts" (the thin text names "source Leads only"), a saved routine text with an earlier stamp (Send invitations or Withdraw stale invitations at 0.9.15, Follow-up at 0.9.15, 0.9.16, 0.9.17 or 0.9.18, Source leads at 0.9.13) or without the `routines board:` line, which becomes the 0.9.24 text with the same saved answers, cron, name and enabled state, and the board line, and a saved Sync data task, which is not updated in place but retired (see Install). Another skill may follow these steps; they touch the one schedule and nothing else.

1. Ask only for the answer that is missing or changing (the timezone or the LinkedIn public identifier). Ask nothing else. Never ask for a quota: Leads per day, Leads per run and who sources them are set on each Agent in Outreach, Agent tab, not in the schedule.
2. Find the installed task, for example "Mosaico Outreach — Source leads (own)", matching by purpose, scope and instructions as under Install. If there is none, say so and offer to install it; do not create one here without being asked.
3. Replace the whole text with the thin text for that routine above (for Source leads, the text of its lane, carrying its `sourcing scope` line over; a text with no scope line gets `sourcing scope: own`), filled with the saved answers and the board address (the saved `routines board:` line when there is one, otherwise the person's board, see **The Routines Board**), so the saved text holds only the standing answers. If the saved text is the older long form, read its answers from it: the timezone after "Resolve the current business date and time in" and the public identifier in the brackets after "signed in to my LinkedIn"; carry them over unchanged unless the person gave a new one, and drop any quota map. Change nothing else: keep its cron times, timezone, name, enabled state, working folder and every other saved setting exactly as they are.
4. Read the saved task back and confirm to the person its name, timezone, enabled state, times (unchanged), that its text is now the thin text, and the standing answers it holds. A write without readback is not completion. If the timezone changed, record the routine again (**Record the schedules in Mosaico**).

**Mosaico Outreach — Repair** — once a week, by default Sunday at 10:00 AM local time (cron
`0 10 * * 0`) unless the person chose another day or time, and also whenever the person asks for it. It
works the backlog Mosaico lists in its repair queue, up to the cap Mosaico sets for one run. It never
approves, sends or messages; the Send invitations and Follow-up schedules do that. Its text is:

```text
Use the installed mosaico:mosaico-outreach-repair-run skill from the mosaico plugin (0.9.6 or later). This is the Repair routine. Follow that skill's "Repair routine" section exactly; it is the procedure and it is current for the installed plugin version.

Standing answers for this recurring automation, supplied once by the person: timezone <timezone>; LinkedIn public identifier <public identifier>; scope: the whole repair queue, up to the cap Mosaico sets for one run. Proceed without asking which scope.

Do every LinkedIn step in Claude's built-in browser pane, signed in to my LinkedIn (<public identifier>). A LinkedIn warning or captcha stops the run, which then reports.

If the installed plugin is older than 0.9.6 or has no "Repair routine" section, stop and report that the plugin needs updating. Report as the skill says.
```

## Keep the schedules apart

The defaults are built around the person's evening review: the person reviews and approves drafts between 7:00 PM and 10:30 PM, the 6:45 PM Follow-up drafts for that review, the 10:45 PM Follow-up sends what was approved, Send invitations sends in the morning and drafts the coming days, and Source leads runs overnight.

The schedules that use the LinkedIn browser pane (Send invitations, Follow-up, Withdraw stale invitations, both Source leads lanes and Repair) must not overlap: every start is at least 30 minutes from every other start of these, and the two Source leads lanes sit 90 minutes apart. The Routines report uses no browser and no Mosaico connector, so it only must not start at the same minute as another task. The defaults, every day:

- Source leads (own): `0 0,3 * * *` (12:00 AM and 3:00 AM);
- Source leads (colleagues): `30 1,4 * * *` (1:30 AM and 4:30 AM), 90 minutes from the own lane;
- Send invitations: `0 6 * * *` (6:00 AM);
- Routines report: `45 6,23 * * *` (6:45 AM and 11:45 PM);
- Follow-up: `45 18,22 * * *` (6:45 PM and 10:45 PM);
- Withdraw stale invitations: `30 23 * * *` (11:30 PM), installed paused until the person has tested it;
- Repair: `0 10 * * 0` (Sunday 10:00 AM), unchanged.

### Ask once about the review window

Ask the person once when they review and approve drafts in Outreach (the default is 7:00 PM to 10:30 PM; do not ask again if the saved Follow-up times already match an answer). The first Follow-up time is 15 minutes before the window starts and the second is 15 minutes after it ends. When the answer differs from the default, shift only the two Follow-up times (for a window of 8:00 PM to 11:00 PM: `45 19,23 * * *`) and keep every other default. If a shifted Follow-up time falls closer than 30 minutes to another LinkedIn task, or a shifted second time is not at least 30 minutes before Withdraw stale invitations, move that other task (never the Follow-up time) and say so in the readback. The same rule applies if the person moves any default time: move or drop any other time that falls closer than 30 minutes to it (90 minutes between the two Source leads lanes), and say in the readback that you did this.

On the day Repair runs, keep every other LinkedIn time at least 30 minutes from the Repair time too: move or drop that other time, never the Repair time the person chose, and say so in the readback. Repair never sends, so it never takes the place of Send invitations or Follow-up.

## The Routines Board

The Routines Board is one page per person, "Outreach Routines Board", where every routine leaves its run and the person sees what needs them. The installer publishes it once and writes its address into each routine's text.

1. **Find an existing board.** Read the saved texts of the tasks you matched. If any carries a `routines board: https://claude.ai/artifact/<id>` line, that address is the person's board: reuse it for every text and publish nothing. If texts disagree, use the address on the most tasks and make every text carry it, and say so in the readback.
2. **Otherwise publish it, once.** Read the board page from the installed plugin, `assets/routines-board.html` in the Claude plugin folder, and publish that file unchanged with the Artifact tool (do not edit, restyle or rewrite it): title "Outreach Routines Board", icon `dashboard`, and exactly the capabilities the page's header comment states, the `db` capability with the access rules everyone admitted reads and only Editors and the Owner (admin) write, and `user`:

   ```json
   {
     "db": { "rules": [
       { "path": "runs", "read": "view", "write": "admin" },
       { "path": "actions", "read": "view", "write": "admin" },
       { "path": "issues", "read": "view", "write": "admin" },
       { "path": "improvements", "read": "view", "write": "admin" },
       { "path": "meta", "read": "view", "write": "admin" }
     ] },
     "user": {}
   }
   ```

   Load the `artifact-capabilities` skill first if it is available, and do not publish the page again on a later install. Keep the returned address.
3. **Write the line.** Append the single line `routines board: <url>` as its own paragraph to every routine text, as the texts above show (all of them except Repair), replacing an older `routines board:` line when there is one. Read each saved text back and confirm that it ends with the line and still holds nothing else of the procedure.
4. **No Artifact tool.** If the Artifact tool is not available (for example the person is not signed in to claude.ai), install everything else without the line, say so in the readback and tell the person to run the installer again once it is available. A routine whose text has no board line skips the board silently.

The board page is for Claude only: the Codex package does not carry it and installs no board line.

## Record the schedules in Mosaico

Mosaico stores no schedule of its own. Outreach, Agent tab has a Routines section that shows, for each routine, what it does, when it runs and its last run; Mosaico knows when it runs only because you tell it. After you create, update, pause or resume a scheduled task, and after you have read that task back, call `outreach_record_routine_schedule` once for that routine, with the values the task actually saved, never the defaults:

- `routine`: `source_own` (Source leads, own lane), `source_colleagues` (Source leads, colleagues lane), `send_invitations`, `follow_up`, `withdraw` (Withdraw stale invitations), `routines_report` or `repair`.
- `timeZone`: the IANA zone the task saved with, for example `Pacific/Auckland`; never an abbreviation.
- `days`: the days of the week the saved cron fires on, as `mon`, `tue`, `wed`, `thu`, `fri`, `sat`, `sun`. A `*` day field is all seven days; `0` is `sun`; each day once.
- `times`: every time of day the saved cron fires, as `HH:MM` on the 24-hour clock in that zone, each once: `45 18,22 * * *` is `18:45` and `22:45`; `0 0,3 * * *` is `00:00` and `03:00`.
- `paused`: `true` when the task is saved disabled, `false` when it is enabled. A Withdraw stale invitations task installed paused is recorded `true`; when the person later tells you to turn it on, enable it, read it back and record it again.
- `pluginVersion`: the version of the installed Mosaico plugin, read from the plugin's manifest, for example `0.9.26`.

Do not pass `ownerUserId`: the schedules are the person's own. Record a routine only when its task exists and you have read it back: a person who does not source has no Source leads task, the colleagues lane is optional, and the retired Sync data task is not recorded. One call per routine, after the readback; a second call for the same routine replaces the first. The answer is the stored state (`state` `recorded`, `schedule.text`, `changed`); check that `schedule.text` matches what you saved.

If the tool is not available, or Mosaico refuses a value, the schedule stays installed: do not undo it and do not retry more than once. Say which routines were not recorded and why, and tell the person that running this installer again records them. The tool changes nothing but the report; it starts no run. The readback and the final report say which routines were recorded and which were not.

## Install

1. Use the person's local timezone and current working folder. Inspect existing scheduled tasks
   before writing anything. Then settle the board address (**The Routines Board**) and ask once about the review window (**Ask once about the review window**); both come before the first write, because every text carries the board line and the Follow-up times depend on the window.
2. Match existing tasks by their Mosaico Outreach purpose and instructions, not name alone. An older
   "Prepare invitations" task matches Source leads. An older "Send approved invitations" task matches
   Send invitations. A task that works the repair queue matches Repair. Only one task may send, so update the old
   sending task in place or disable it.
   A task for the older single Sync data routine (its title "Mosaico Outreach — Sync data (connections and messaging)", or a text that says "This is the Sync data routine") matches none of the new tasks: it is retired. Create the Send invitations, Follow-up and Withdraw stale invitations tasks first, then retire the Sync data task with `update_scheduled_task` (disable it) or `delete_scheduled_task`, use the default times of **Keep the schedules apart** for the three new tasks (the old Sync data times are not kept), and say in the readback that it is retired. A reinstall must find and retire it; never leave it enabled beside the three, because it would run the same work twice. A saved thin text matches the routine it names ("This is the Send invitations routine", "This is the Follow-up routine", "This is the Withdraw stale invitations routine", "This is the Routines report routine"). A saved Routines report task is updated in place like the others (the 0.9.24 text, its cron and name kept); if there is none, create it (`45 6,23 * * *`, active) once the board address is known. Match a Source leads task by
   routine and scope: its text holds `sourcing scope: own` (the own lane) or `sourcing scope: colleagues` (the colleagues
   lane). A Source leads task with no scope line is the older whole-plan task: update it in place into the own lane (the
   own text, the own cron, its name and enabled state otherwise kept) and never leave it enabled beside the lanes. If an
   own-lane task already exists as well, disable the scope-less one and say so.
   Ask once whether the person sources Leads herself and, if she does, whether she also sources for a colleague.
   No Source leads task at all is a valid answer (a person who does not source has none, and none is installed); a person
   who sources only her own Agents gets the own lane only; a person who also sources for a colleague gets both lanes.
3. If equivalent tasks already exist, do not duplicate them. Report their names, timezone, enabled
   status and next runs.
4. If matching tasks exist but differ, update them in place as under **Update the standing answers in
   place**: a text in the older long form is replaced by the thin text, carrying its answers over and keeping
   its cron times, enabled state, name and every unrelated supported metadata and permission setting. A saved Follow-up text
   that says "0.9.15 or later" up to "0.9.18 or later", and any saved routine text without the `routines board:` line, is not equivalent to the current one: replace it in place with the 0.9.24 text of its
   routine, under the same rule, and say in the readback that its stamp moved to 0.9.24. A saved Withdraw stale invitations task keeps its enabled state, so a paused one stays paused.
5. If the host supports only one persistent local task, install Send invitations alone and tell the person
   that Follow-up, Withdraw stale invitations, Source leads, Routines report and Repair are not installed. Do not merge the schedules or weaken any of them.
6. Do not ask the person to repeat the dates, actions, times, folder or timezone. Ask only when a
   host-required human decision cannot be derived from the current context.
7. Read back the saved task state and confirm names, local timezone, enabled status, next run
   times and that each saved text is the thin text (it names the skill and its routine section and holds
   no steps). Read both Source leads lanes back and show, for each, its name, cron, enabled state, next run, its
   `sourcing scope` line, and that its text names the Source leads routine section and holds no steps; confirm that no
   Source leads task without a scope line remains enabled. Confirm that every LinkedIn task start is at least 30 minutes from every other, that the two Source leads lanes are 90 minutes apart, and on Sunday that every start is at least 30 minutes from the Repair time. Confirm that Withdraw stale invitations is saved paused (or keeps the enabled state it had), that every routine text except Repair ends with the same `routines board:` line, that the Routines report task exists with the cron `45 6,23 * * *`, and give the person the board address. For Repair,
   confirm the cron `0 10 * * 0` (or the person's own day and time), and that Repair is also available on
   demand through `/mosaico:mosaico-outreach-repair-run`. A write attempt without readback is not
   completion. Also confirm that no Sync data task remains enabled: read the three new tasks back first, and only then say the old one is retired.
8. Record each installed or changed schedule in Mosaico (**Record the schedules in Mosaico**): one `outreach_record_routine_schedule` call per routine, from the readback you just made, after the Sync data task is retired. Say in the report which routines were recorded, with the times Mosaico now shows (`schedule.text`), and which were not and why. Skip the routines whose task you did not touch only when the person says they were already recorded.
