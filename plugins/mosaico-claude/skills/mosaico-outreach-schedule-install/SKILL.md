---
name: mosaico-outreach-schedule-install
description: Install or repair the two Mosaico Outreach schedules, Sync data and Source leads, in the user's local timezone.
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

## Set up a second person

Use this when another person, for example a colleague who sources and delivers for herself, wants her own
schedules. Everything below happens on her own Mac. Go through the steps in order and stop at the first
one that fails.

1. **Claude desktop app and plugin.** The Claude desktop app is installed on her Mac, with the Mosaico
   plugin installed from the marketplace, version 0.6.1 or later.
2. **Her Mosaico account.** The Mosaico connector is signed in as her own Mosaico account, not anyone
   else's. She must be an active member of the organisation. An Owner or Admin can check this in
   Outreach, Agent tab.
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
6. **Run this installer.** It installs her Sync data schedule. Ask once whether she sources Leads
   herself; only if she does, also install her Source leads schedule.

Each person's Sync data schedule runs on that person's own Mac, in that person's own browser pane, and
sends only from that person's account. Nobody's run touches another owner's Leads.

## The two schedules

Install two active persistent local scheduled tasks. Each scheduled run starts its own Outreach run
through the invite-run or follow-up-run skill. If Mosaico returns a blocker, the run stops and reports
it; it does not work around it.

Fill the placeholders from the person and the current context, never from a fixed value:
`<public identifier>` is the last part of the person's LinkedIn profile address (the part after
`/in/`); `<timezone>` is their local timezone. Ask only if one of them cannot be found.

**Mosaico Outreach — Sync data (connections and messaging)** — once a day, at 1:00 PM local time unless
the person chose another time. This is the only schedule that clicks Connect or sends a message. Its
text is:

```text
Use the installed mosaico:mosaico-outreach-follow-up-run and mosaico:mosaico-outreach-invite-run skills (plugin mosaico, 0.8.1 or later). This is the Sync data flow of Mosaico Outreach: connections and messaging. It does not source, transfer or draft invitations; the Source leads schedule does that.

Resolve the current business date and time in <timezone>. The person has supplied standing answers for this recurring automation: proceed without asking which days or which scope.

Do every LinkedIn step in Claude's built-in browser pane, which is signed in to my LinkedIn (<public identifier>). Obtain connection evidence and identity only through the plugin's approved capture scripts, run word for word with only the first line's value changed, exactly as the skills describe. The approved scripts are browser/linkedin-whoami.js, browser/linkedin-connection-evidence.js, browser/linkedin-recent-connections.js, browser/linkedin-thread-messages.js and browser/linkedin-sent-invitations.js; read each from the installed plugin. If the installed plugin has no browser folder, stop and report that the plugin needs updating. Never read, copy, export or reconstruct a LinkedIn cookie, token or session; never write a LinkedIn script of your own; never read a Connect, Message or Pending button as a connection state; never set a connection state yourself. If a capture is unavailable or Mosaico cannot use its result, leave that Lead unverified, list it as skipped, and continue.

Step 1. Open https://www.linkedin.com/feed/ once. Run the approved whoami script and pass its output unchanged as identityEvidence to outreach_start_run (omit observedLinkedInProfile). Only if the whoami script cannot run, open the Me page and report its profile URL as observedLinkedInProfile instead. Start one run per scope and pass its runId on every read and write; before each send-evidence write, run the whoami script again and pass its output as identityEvidence. If Mosaico blocks the start, stop and report the blocker; do not work around it.

Step 2. Run the mosaico:mosaico-outreach-follow-up-run skill across all dates with the selected action "one pass per thread". Follow workflowStatus.recommendedAction from outreach_get_follow_ups. When Mosaico recommends capture_connections, run the approved recent-connections script once, save its output as returned, submit its pages to outreach_record_connections_snapshot one call per page in index order exactly as the follow-up-run skill describes (submit any pages Mosaico lists as missing, and first any pages left over from an earlier capture), then reread. For each Lead Mosaico returns, run the approved thread script with the Lead's public identifier (the part of its linkedInProfileUrl after /in/) as the first-line value and pass its output unchanged as threadEvidence to outreach_deposit_conversation with publicLinkedInUrl and fresh identityEvidence; Mosaico derives direction and times. Every thread deposit carries the outcome of the Lead's latest message (declined, interested or neutral), judged as the follow-up-run skill describes; a no ends the Lead, so never draft or send for a Lead who said no. Pass every script's output exactly as returned, every field including integrity, never retyped or edited: if Mosaico answers evidence-altered, run the script again and pass the new output unchanged. If the answer is no-conversation, continue with the next Lead. If the answer is thread-not-found-in-window, report the Lead as thread not found in the window and continue with the next Lead; do not read it by eye. If Mosaico recommends repair_drafts, visit each Lead in repairSuggestions first, as the follow-up-run skill describes. Only if the script cannot run, open navigation.messageUrl and deposit the visible conversation by eye, and say so in the report. If Mosaico still lists an approved outbound Follow-up for that Lead as deliverable, send it exactly as approved, then run the approved thread script again with the Lead's public identifier as the first-line value and pass its output unchanged as threadEvidence to outreach_mark_message_sent with fresh identityEvidence; Mosaico marks it sent only when the thread shows the approved message. If Mosaico answers send-not-confirmed, do not retype it: retry the send once, run the thread script again, and if it is still not confirmed call outreach_record_delivery_block with reason cannot-message and continue with the next Lead. Never mark a message sent from the screen alone unless the script cannot run, and then say so in the report. If the conversation cannot be opened, call outreach_record_delivery_block with reason cannot-message and continue. Save every missing outbound follow-up draft Mosaico permits with sentAt null. If Mosaico lists a Lead as connection unverified, do not draft or send for it: open its profile, run the approved connection-evidence script, pass the result to outreach_record_connection_evidence, and continue only if Mosaico then lists the Lead as connected. Never approve, rewrite, replace or substitute a message.

Step 3. Run the mosaico:mosaico-outreach-invite-run skill with the selected day today and the selected action "send approved invitations". Work only on today and send only exact outbound Invite messages whose current Mosaico status is already Approved. Before each one, open the Lead's linkedInProfileUrl, wait until the page has loaded, run the approved connection-evidence script, and pass the result unchanged to outreach_record_connection_evidence together with fresh identityEvidence. Mosaico answers connected, invite pending or not connected and records it. Send only when Mosaico answers not connected and still lists the invitation as Approved. If Mosaico answers connected or invite pending, continue with the next invitation; Mosaico has already taken that invitation off the send list. After each send, run the approved sent-invitations script with the Lead's public identifier as the first-line value and pass its output unchanged as sentInvitationEvidence to outreach_mark_message_sent together with fresh identityEvidence; Mosaico marks the invitation sent only when LinkedIn's Sent invitations list shows it, because the profile call cannot show a pending invitation. If Mosaico answers send-not-confirmed, do not retype the note: retry the send once, run the script again, and if it is still not confirmed call outreach_record_delivery_block with reason cannot-message and continue with the next Lead. Never mark an invitation sent from the screen alone unless the script cannot run, and then say so in the report. A recorded or skipped Lead is not a blocker. Reread the day after every write and continue until Mosaico reports completion (no-approved-invitations-remain) or a genuine blocker (Mosaico, sign-in or LinkedIn failure).

Step 4. Report separately, using Mosaico's counts, not memory: how identity was established (whoami evidence or Me page); approved follow-up sends; follow-ups recorded as cannot-message; new follow-up drafts written; drafts Mosaico discarded (draftsDiscarded), each with its Lead and reason; outcomes recorded (declined, interested, neutral); Leads whose thread was not found in the window; whether the connections list was captured and how many Leads it marked connected; today's invitation sends; sends confirmed from data versus by screen; invitations where Mosaico answered connected or invite pending; Leads left unverified; threads read from data versus by eye; skipped Leads with reasons; blockers. Nothing merely drafted may be described as approved or sent. Preserve Mosaico as workflow authority and never modify another owner's records.

Guards: pacing between page loads, the weekly invitation ceiling and run expiry are enforced by Mosaico; a LinkedIn warning or captcha stops the run, which then reports.
```

**Mosaico Outreach — Source leads** — every two hours during business hours, by default 8:00 AM to
6:00 PM local time, unless the person chose other hours. It runs from any linkedin.com page. It never
approves or sends anything. Its text is:

```text
Use the installed mosaico:mosaico-outreach-invite-run skill (plugin mosaico, 0.5.0 or later). This is the Source leads flow of Mosaico Outreach. It only finds Leads and writes invitation drafts. It never approves, sends or messages; the Sync data schedule does that.

Resolve the current business date and time in <timezone>. The person has supplied standing answers for this recurring automation: proceed without asking which days or which scope.

Do every LinkedIn step in Claude's built-in browser pane, from any linkedin.com page, signed in to my LinkedIn (<public identifier>). Obtain connection evidence and identity only through the plugin's approved capture scripts, run word for word with only the first line's value changed, exactly as the skills describe. The approved scripts are browser/linkedin-whoami.js and browser/linkedin-connection-evidence.js; read each from the installed plugin. If the installed plugin has no browser folder, stop and report that the plugin needs updating. Never read, copy, export or reconstruct a LinkedIn cookie, token or session; never write a LinkedIn script of your own; never read a Connect, Message or Pending button as a connection state; never set a connection state yourself. If a capture is unavailable or Mosaico cannot use its result, leave that Lead unverified, list it as skipped, and continue.

Step 1. Open any linkedin.com page once. Run the approved whoami script and pass its output unchanged as identityEvidence to outreach_start_run (omit observedLinkedInProfile). Only if the whoami script cannot run, open the Me page and report its profile URL as observedLinkedInProfile instead. Start one run per scope and pass its runId on every read and write; before each evidence write, run the whoami script again and pass its output as identityEvidence. If Mosaico blocks the start, stop and report the blocker; do not work around it.

Step 2. Run the mosaico:mosaico-outreach-invite-run skill with the selected day the next business day and the selected action "source Leads only", using the quota Mosaico reports. Mosaico assigns the day and keeps the quota. Each Lead is saved directly under the target owner by the run; there is no transfer step. Follow workflowStatus.recommendedAction and reread after every saved Lead.

Step 3. Run the mosaico:mosaico-outreach-invite-run skill again with the same day and the selected action "source Leads and prepare invitation drafts". For each Lead Mosaico lists as connection unverified, open its profile, run the approved connection-evidence script and pass the result unchanged to outreach_record_connection_evidence. Write a missing invitation draft only for a Lead Mosaico lists as verified. Never approve or send an invitation.

Step 4. Stop only when Mosaico says the quota is met, or when Mosaico reports stop_run after the tenth failure. In that case write the sourcing report Mosaico asks for. A skipped candidate or a refused write for one Lead is not a reason to stop.

Step 5. Report separately, using Mosaico's counts, not memory: Leads saved, drafts written, quota remaining, candidates skipped with reasons, Leads left unverified, blockers. Nothing merely drafted may be described as approved or sent. Preserve Mosaico as workflow authority and never modify another owner's records.

Guards: pacing between page loads and run expiry are enforced by Mosaico; a LinkedIn warning or captcha stops the run, which then reports.
```

## Keep the two schedules apart

The schedules must not overlap. Place every Source leads time at least 60 minutes before or after the
Sync data time. With the default 1:00 PM Sync, the default Source leads times are 8:00 AM, 10:00 AM,
12:00 PM, 2:00 PM, 4:00 PM and 6:00 PM. If the person moves the Sync time, move or drop any Source
leads time that falls closer than 60 minutes to it. Say in the readback that you did this.

## Install

1. Use the person's local timezone and current working folder. Inspect existing scheduled tasks
   before writing anything.
2. Match existing tasks by their Mosaico Outreach purpose and instructions, not name alone. An older
   "Prepare invitations" task matches Source leads. An older "Send approved invitations" task matches
   Sync data. Only one task may send, so update the old sending task in place or disable it.
3. If equivalent tasks already exist, do not duplicate them. Report their names, timezone, enabled
   status and next runs.
4. If matching tasks exist but differ, update them in place while preserving unrelated supported
   metadata and permission settings.
5. If the host supports only one persistent local task, install Sync data alone and tell the person
   that Source leads is not installed. Do not merge the two schedules or weaken either.
6. Do not ask the person to repeat the dates, actions, times, folder or timezone. Ask only when a
   host-required human decision cannot be derived from the current context.
7. Read back the saved task state and confirm names, local timezone, enabled status and next run
   times. For Source leads, confirm that every time is at least 60 minutes from the Sync time. A
   write attempt without readback is not completion.
