---
name: mosaico-outreach-schedule-install
description: Install or repair the Mosaico Outreach schedules, Send invitations, Follow-up, Withdraw stale invitations, Source leads (an own lane and a colleagues lane) and Routines report, and publish the person's Routines Board, in the user's local timezone.
---

# Install the Mosaico Outreach schedules

Mosaico owns the routines: their names, texts, default times, steps and report headings. This skill only checks the
machine, saves what `outreach_get_routine_setup` returns as Claude Desktop scheduled tasks (`list_scheduled_tasks`,
`create_scheduled_task`, `update_scheduled_task`, `delete_scheduled_task`), and tells Mosaico what it saved. It
changes no Lead, Message, Agent or run. If a call is refused because the connector is acting as a member of another organisation, or its acting session ended, stop and report Mosaico's sentence word for word. Never end the acting session yourself. This plugin is 0.11.1 and expects routine catalogue `2026-10-27.4` or later.

## Check before installing

If any check fails, install nothing and tell the person what to do.

1. `~/.claude/settings.json` has all three of `mcp__Claude_Browser__javascript_tool`, `mcp__Claude_Browser__computer`
   and `mcp__Claude_Browser__browser_batch` in `permissions.allow`. Scheduled sessions ignore project-level rules. The
   plugin cannot write that file: print the snippet for the person to merge.
2. No folders named `mosaico-outreach-*` in `~/.codex/skills/` or `~/.claude/skills/` (stale copies; ask the person to
   archive them) and no active old Codex automation `daily-approved-outreach-sends` or `mosaico-lead-preparation`.
3. No MCP server for a non-production Mosaico address (`amplifyapp.com`, `stage`, `staging`, `test`, `localhost`) in
   `.mcp.json` or the project and user entries of `~/.claude.json`.
4. A Mosaico connector for `https://app.mosaico.one` is connected in Claude's connectors (not /mcp), shown by the
   `outreach_start_run` tool.

## Install

1. Routines Board: reuse the address on any saved routine text (`routines board: <url>`). Otherwise publish
   `assets/routines-board.html` of this plugin unchanged with the Artifact tool, once per person, title "Outreach Routines
   Board", with these capabilities. Without the Artifact tool, install without the board and say so.

   ```json
   { "db": { "rules": [
     { "path": "runs", "read": "view", "write": "admin" },
     { "path": "actions", "read": "view", "write": "admin" },
     { "path": "issues", "read": "view", "write": "admin" },
     { "path": "improvements", "read": "view", "write": "admin" },
     { "path": "meta", "read": "view", "write": "admin" }
   ] }, "user": {} }
   ```
2. Read `outreach_get_routine_setup` with the person's IANA `timeZone` and `boardUrl`; for another member an Owner or
   Admin adds `ownerUserId`, but each person's tasks are saved on her own machine. If the tool is missing, or the answer
   has no `catalogueVersion`, an older one than above, or a `minimumPluginVersion` newer than 0.11.1, stop and say the
   plugin and the Mosaico server must be updated together. A `blocked` state (for example
   `register_linkedin_identity`) is reported with its blocker's action; install nothing.
   If `standingAnswers.reviewWindow.state` is `missing` (`recommendedAction` `ask_review_window`), ask the person once:
   "When do you usually review and approve drafts?" Take a start and an end in her local time, and read the setup again
   with them as `reviewWindow` (`start`, `end`). If Mosaico refuses them, say its sentence and ask once more. Never ask
   when the state is `given` or `registered`: Mosaico already knows it.
3. For each routine in `routinesToInstall` and `routinesToUpdate`, and for Source leads only if the person asks for it,
   save a task named `taskName`, with `routineText.text` as the prompt exactly as returned, the times of
   `defaultSchedule` exactly as returned (its cron, in the person's local time; when `defaultSchedule.crons` holds more
   than one, one task per cron with the same text and the clock time added to the name), and disabled when
   `defaultSchedule.paused`. An update keeps the task's name and enabled state. Never add, shorten or copy a step into a
   text. If `routineText.complete` is false, ask for the missing standing answer first. Match saved tasks by the routine
   their text names; a task that says "This is the Sync data routine" is retired (disable it), never run.
4. Browser routines must not overlap. Mosaico works out every time to keep them apart: never move, add or drop one yourself.
   Read each line of `readback` to the person word for word. For another time the person wants, read the setup again.
5. Read each saved task back (name, time zone, enabled state, times, text). Then call
   `outreach_record_routine_schedule` once per routine with `routine`, `timeZone`, `days`, `times`, `paused`, the
   plugin's version as `pluginVersion`, the setup's `catalogueVersion` and its `reviewWindowUsed` as `reviewWindow`
   (only when the review window is not `missing`), from what the task actually saved. Never pass
   `ownerUserId` for your own. If Mosaico refuses a value or the tool is missing, the task stays; say which routine was not
   recorded and that running this installer again records it.
6. For each entry in `retiredRoutines` (a routine Mosaico retired that the person still has a task for), offer to
   delete the scheduled task `taskName` (action `remove_retired_routines`) and delete it only after the person agrees.
7. Read `outreach_get_routine_setup` again and report what is installed, current, paused, removed or not recorded.

## Another person

She sets up her own schedules on her own Mac: the plugin, her own Mosaico connector, her own LinkedIn signed in
inside Claude's built-in browser pane, the three allow rules above, and her LinkedIn profile registered in Outreach,
Agent tab. Then run this installer there, with her own Routines Board.

If a tool named here is missing: role or no subscription; with an active subscription, the list is out of date: reconnect.
