---
name: mosaico
description: Read or manage Mosaico organization data through the connected production MCP service.
---

# Mosaico

Use Mosaico tools as the authority for organization data, permissions, validation and completion.
For writes, follow the tool's preview and execute contract. For multi-step workflows, read status,
perform only an allowed transition and reread status after every transition. Never reconstruct
workflow state from conversation memory or claim a write succeeded when Mosaico reports otherwise.

## Changes need a subscription

A change made through the connector needs the organisation to have an active Mosaico subscription with AI
allowance left. Without a subscription I cannot change anything for the person. Reading does not need it,
and neither do the few tools that only stop or carry on a run Mosaico already started, or end an acting
session. If Mosaico refuses a change for this reason, tell the person plainly, in Mosaico's own words,
that nothing was changed:

- "This organization needs an active Mosaico subscription before the MCP connector can run this tool."
- "This organization has no remaining AI allowance for this period."
- "Another tool call is settling this organization’s AI allowance. Retry this call shortly." Wait a
  moment and call again; if it is still busy, tell the person.

Do not try another tool to make the same change.

## Acting as a member of a customer

A reseller operator can make their own Claude connector act as a member of one of their customer
organisations. There is no timer: the session ends only when the person ends it or signs out. Only the operator's own click in the Mosaico web console starts it
(Customers, the customer, Members, the member, then "my connected Claude"). No tool starts it, so never
try to start it or offer to: if the person wants it, tell them where to click.

While it lasts, every call runs as that member in that customer, with that member's role and the
customer's rules. Working as a member copies that member's permissions exactly and adds nothing: billing is
reachable only when working as the Owner, and Mosaico refuses the reseller tools while you work as a member.
Progress in the member's name is allowed as the member could do it, and Mosaico logs it under both names.
Every result ends with one line that says who, for example "Working as <member> (<role>) in <customer> since
<time> UTC; signed in as <operator>." Tell the person who they are working as before you change anything in
the customer and in your final report. Do not assume the session is still on; ask Mosaico.

- `get_acting_status` takes no arguments and always works. It returns `phase` (`not-acting`, `acting` or
  `ended`), the `operator`, `connector.reference` (the short reference the web console lists beside each
  connected Claude, so the person can tell several apart), while acting the `member`, the `customer`,
  `startedAt`, and `blockers`, `allowedActions` and one `recommendedAction`. Do what `recommendedAction`
  says. A `human` action is a step for the person. For an ended session its one recommended action is
  `tell_the_person_the_task_stopped`: tell the person and wait. Reading it after a session ended also clears
  the one-time refusal described below.
- `stop_acting` takes no arguments, needs no confirmation and always works. It ends the session now, and
  the next call runs as the person in their own organisation. Call it when the person asks to stop acting
  or to leave the customer, never to get round a refusal.
- Outreach and incident tools do not run while acting. Mosaico says: "Outreach and incident tools are not
  available while your connector is acting as a member of another organisation. End the session first."
  Report that sentence and stop. Do not end the session yourself to get past it.
- Mosaico refuses the reseller tools while you work as a member: "Reseller tools are not available while your
  connector is working as a member of a customer, because the member is not a reseller. End the session
  first." Report that sentence; do not end the session yourself to get past it.
- When the person ends the session (End in the web console, or sign-out), Mosaico refuses the next call once.
  The sentence begins "Your session as" and ends "so the task stopped and this call did not run: tell the
  person, and do not carry on as yourself." Do not repeat the call and do not carry on the task. Tell the
  person that the session as <member> ended and the task stopped, then wait for their new instruction. Do not
  continue as the operator until they give one. `ping`, `get_acting_status` and `stop_acting` still run and
  clear the refusal.
- If Mosaico says it could not confirm whether the connector is still acting, call `get_acting_status`, or
  `stop_acting` if the person wants to go back to their own organisation.

## Teams, positions and flow assignments

Each of these shows a preview first and writes only after the host's single approval; do not ask again in
the chat. Take ids from Mosaico, never from memory: `get_team_profiles` for people, `list_positions`,
`list_teams`, `list_processes`, and `get_flow_definition` for a flow's steps.

- `list_teams` takes no arguments. It lists every team with its id, name and member count, including teams
  with no members yet.
- `create_team` creates one empty team from a `name` (and an optional `description`). Mosaico refuses a name
  a team already has. The new team has no members: read its id with `list_teams`, then put people in it
  with `batch_assign_teams`.
- `batch_assign_positions` gives people positions: `assignments`, each one `personId` and one `positionId`,
  up to 10 in one call. It only adds. It never removes a position or changes a role or a team.
- `assign_person_to_flow` assigns (`assigned: true`) or removes (`assigned: false`) one person on one flow
  (`processId`, `personId`). It touches nobody else; for a whole team use `assign_team_to_process`, for
  everyone `assign_all_users_to_process`. Removing a person deletes the work they have recorded on the
  flow, and the preview says so: show it and remove only on the person's clear yes.
- `set_person_task_due_date` sets, changes or clears one person's own date on one step: `processId`,
  `personId`, `taskId` and `dueDate` (YYYY-MM-DD, or `null` to clear). The person must already be on the
  flow and hold the step; if not, Mosaico says so, and you assign them first. It does not change the
  step's own deadline rule (`set_task_due_date`) or move everyone's dates (`extend_process_due_dates`).

## Installing a Methodology component

A converted Flow or Domain is a component of a conversion project. It is either a draft (it still has warnings)
or published (it has no warnings). Fixing a component's warnings is what makes it installable;
there is no approve step, no publish step, no Private or Public setting, no hide or show for one customer and
no Examples tab or example library. What a customer sees is what the reseller installed into that customer's
organisation. A customer installs its own published components from the Methodology components tab.

- `install_methodology_component` installs a copy of one published component into one organisation, exactly as
  the Install button does: `projectId`, `componentKind` (`flow` or `domain`), `componentKey` and
  `targetOrganizationId`. Take the first three exactly as `get_methodology_project_status` lists them under
  `components`; the status offers `install_component` with these arguments already filled in. The target is the
  person's own organisation, or, for a reseller Owner or Admin, the organisation id of one of its customers.
- It shows a preview first, then installs when you call it again with `mode: "execute"` and the
  `confirmationToken` from the preview. Read the preview aloud in Mosaico's words: it says whether the install
  makes a new copy or replaces the earlier one, and where. The host asks the person once; do not ask again in
  the chat.
- A second install into the same organisation replaces the earlier copy in place when nobody has progress on
  it. If someone has progress on it, Mosaico makes a new copy and keeps the old one. Say which before the person
  confirms; the preview states it.
- Only an Owner or Admin can install, and it needs an active subscription. Mosaico refuses with a code and one
  sentence: `component_not_published` (a draft, with its warning count: fix the warnings first),
  `analysis_not_complete`, `not_compilable`, `tenant_access_denied` (no reseller access to that customer) and
  `subscription_required`. Give Mosaico's sentence, never your own; nothing was changed.
- While your connector works as a member of a customer, the only target allowed is that member's organisation.
  Any other target is refused with the reseller-tools sentence above.
- `get_methodology_project_status` carries, for every component: `state` (`draft` or `published`), `warnings`
  (a count), `installs` (`organizationId`, `organizationName`, `installedAt`, `by`, `changedSinceInstall`),
  `allowedActions` and one `recommendedAction`. For a component the recommended action is `fix_warnings`,
  `install_component`, `none` (the installed copy is up to date) or, while the analysis is unfinished,
  `finish_analysis` or `resolve_in_app`. Do what it says, and read the status again after each step. Never build or send a flow or
  domain definition yourself, and do not use `create_flow_from_definition` to install a component.

## When a tool is missing

Mosaico lists only the tools this person may use. If a change tool the person needs is not listed, the likely reasons are
their role or that the organisation has no active Mosaico subscription (Claude can change nothing without one). Read
`get_tier_status` and tell the person which applies. Suggest disconnecting and reconnecting the Mosaico connector in Claude's connector
settings only when the whole connector is missing, Mosaico says the session is invalid, or Mosaico refuses an argument as
unknown. Do not look for another way in.
