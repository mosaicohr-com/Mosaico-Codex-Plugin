---
name: mosaico-outreach-schedule-install
description: Check the Mosaico Outreach routine setup from Codex. The routines are installed from Claude, because Codex cannot run the LinkedIn captures.
---

# Mosaico Outreach schedules in Codex

Mosaico owns the routines: their names, texts, default times and steps. Every routine needs the approved LinkedIn
captures, which only Claude's built-in browser pane can run, so this plugin installs no routine from Codex. Tell the
person to install them from Claude with its schedule skill. If a call is refused because the connector is acting as a member of another organisation, or its acting session ended, stop and report Mosaico's sentence word for word. Never end the acting session yourself. This plugin is 0.11.2 and expects routine catalogue
`2026-10-27.4` or later.

1. Check, and install nothing if one fails: no folders named `mosaico-outreach-*` in `~/.codex/skills/` or
   `~/.claude/skills/` (stale copies; ask the person to archive them), and no active old Codex automation
   `daily-approved-outreach-sends` or `mosaico-lead-preparation` (it would send twice).
2. Read `outreach_get_routine_setup` and tell the person which routines are installed, current or outdated, the
   blockers and Mosaico's `recommendedAction`. If the tool is missing, or the `catalogueVersion` is older than above,
   say the plugin and the Mosaico server must be updated together.
3. For each entry in `retiredRoutines` (action `remove_retired_routines`), offer to delete the matching Codex automation
   and delete it only after the person agrees.
