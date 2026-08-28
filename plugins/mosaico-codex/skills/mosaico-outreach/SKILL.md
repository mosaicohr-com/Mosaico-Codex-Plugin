---
name: mosaico-outreach
description: Run, resume, or inspect a Mosaico Outreach day through the connected Mosaico MCP server and an authenticated browser.
---

# Mosaico Outreach

Mosaico is the workflow authority and system of record. The model operates the workflow; it does not
reconstruct workflow state from conversation memory, draft lists, batch history or browser state.

## Start or resume

1. Resolve the person's explicit intent and calendar date and preserve that date throughout the run.
2. Call `outreach_get_work_options` with that intent and `runDate`. Present choices only when intent
   is genuinely ambiguous.
3. Follow the returned recommended action and reread workflow status after every transition.
4. Continue while the server reports remaining work.
5. Stop only for server-declared completion, a typed external blocker or a human decision.

## Qualification and writing

Call `outreach_get_skill` when the workflow asks for qualification or message writing. It governs
judgment and language only; it does not determine workflow order, dates, recovery or authorization.

## Approval and delivery

Human approval applies to the exact current message body. LinkedIn delivery requires an authenticated
browser. Perform the authorized browser action, verify the result against LinkedIn, report the
accepted evidence through the named Mosaico tool, and reread workflow status.

Nothing is recorded merely because it happened in the browser. Never claim delivery without evidence
accepted by Mosaico.

## Incidents

If a tool returns contradictory or unusable workflow state, record the evidence with the dedicated
MCP incident tool. Do not change dates, duplicate leads, bypass approval or substitute prompt memory
for server state.
