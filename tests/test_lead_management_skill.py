#!/usr/bin/env python3
"""The interactive Lead-management skills let a person book or clear a Lead's next contact date (`nextTouchOn`).

Mosaico owns the date (ADR-0005): it judges today in the owner's time zone, the allowed range and the refusal codes, stores the booking
and holds the Lead's follow-up until the day. The skills only let the model propose one day from the person's words, confirm it with the
person, and show Mosaico's own `earliestAllowed` and `latestAllowed` on a refusal. These checks pin that both packages say so, say that
`null` clears the booking, name the three refusal codes, point a dated follow-up that is already written at the Follow Up tab and the
Follow-up routine (it is `sendNotBefore` on a Message, which this skill never changes), and carry no date logic of their own.

Pass --app-repo (or set MOSAICO_APP_REPO) to also check the application: a run of the intent this skill starts (`manage_leads`) may call
`outreach_update_lead`, which takes `nextTouchOn` and answers a refused day with the three codes (server release 20261013c).
"""

from __future__ import annotations

import argparse
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLAUDE = ROOT / "plugins" / "mosaico-claude"
CODEX = ROOT / "plugins" / "mosaico-codex"
SKILL = "mosaico-outreach-lead-management"
DATE_CODES = ("date-invalid", "date-not-future", "date-too-far")


def check(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL: {message}")


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def flat(text: str) -> str:
    return " ".join(text.replace("`", "").split())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--app-repo", type=Path, default=Path(os.environ["MOSAICO_APP_REPO"]) if os.environ.get("MOSAICO_APP_REPO") else None)
    args = parser.parse_args()

    raw = {package: read(root / "skills" / SKILL / "SKILL.md") for package, root in (("Claude", CLAUDE), ("Codex", CODEX))}

    for package, text in raw.items():
        text = flat(text)
        for needle in (
            # The field is listed among the fields a person can update, and is set through the update call.
            "next contact date (nextTouchOn)",
            'When the person asks to contact a Lead again later ("contact Zoe again in January"), set changes.nextTouchOn through outreach_update_lead',
            "Mosaico then holds the Lead's follow-up until that day",
            # The model proposes one day; the person confirms it before anything is written.
            "You propose one day, written YYYY-MM-DD, from the person's words",
            "write it only after the person confirms that day in step 5",
            # null clears.
            "null clears the booking",
            # Mosaico judges the day; the skill works out nothing.
            "Never work out today or the allowed days yourself: Mosaico judges the day against its own today in the owner's time zone",
            # A refusal writes nothing; Mosaico's own range is shown and the person decides.
            "If it refuses the day, nothing is saved: the answer is blocked with one code, date-invalid, date-not-future or date-too-far",
            "Show the person the earliestAllowed and latestAllowed days Mosaico returns and ask for a day; call again only with a day the person confirms",
            # A written follow-up is not this skill's: it is a Message.
            "This skill never dates a follow-up that is already written: that is sendNotBefore on a Message, and this skill never changes Messages",
            'Point the person to the Follow Up tab ("Follow up on or after") or to the Follow-up routine instead',
            # The existing promise stays.
            "Never update, delete, classify, approve or send Messages",
            "intent: manage_leads",
            # 0.9.25: loading already-sourced Leads and asking for a new draft.
            "outreach_load_leads", "No run is needed", "pages of at most 200 rows", "Mosaico chooses the days", "duplicate-own", "duplicate-in-batch", "held-by-other-owner",
            "invalid-row", "invalid-url", "agent-days-full", "agent-not-sourceable", "write-failed", "load_more", "review_skipped",
            "Never send a rejected row again with changed data without asking the person first",
            "outreach_request_redraft", "person-requested", "never rewrites in place",
        ):
            check(needle in text, f"{package} lead-management skill lacks: {needle}")
        for code in DATE_CODES:
            check(f"`{code}`" in raw[package], f"{package} lead-management skill does not name `{code}` in code style")
        check("`nextTouchOn`" in raw[package] and "`null`" in raw[package], f"{package} lead-management skill does not name `nextTouchOn` and `null` in code style")

        # No date logic of its own: no range, no clock, no business-day arithmetic, no retry loop, none of the queue's holding rules.
        lowered = text.lower()
        for gone in ("365", "business day", "weekday", "run `date`", "run date", "machine's clock", "retry once", "retry_with_valid_date", "try a third time",
                     "next-touch-scheduled", "next-touch-due", "wait_for_scheduled_day", "date-not-applicable", "scheduledreason"):
            check(gone not in lowered, f"{package} lead-management skill carries date logic of its own: {gone}")

    # The two packages differ only in how a skill is invoked.
    claude_as_codex = raw["Claude"].replace("`/mosaico:", "`$mosaico:")
    check(claude_as_codex == raw["Codex"], "the Claude and Codex lead-management skills differ by more than the skill invocation prefix")

    if args.app_repo is not None:
        app = args.app_repo.resolve()
        registry = read(app / "features/outreach/server/outreach-mcp-registry.ts")
        gate = read(app / "features/outreach/server/outreach-run-gate.ts")
        dates = read(app / "features/outreach/shared/outreach-follow-up-dates.ts")
        run = read(app / "features/outreach/server/outreach-run.ts")
        update_row = re.search(r"outreach_update_lead:\s*\[(?P<intents>[^\]]*)\]", gate)
        check(update_row is not None and "'manage_leads'" in update_row.group("intents"), "the application's run gate does not let a manage_leads run call outreach_update_lead")
        check("'manage_leads'" in run, "the application does not know the run intent manage_leads")
        check(re.search(r"nextTouchOn:\s*z\.string\(\)[^;]*\.nullable\(\)", registry) is not None, "outreach_update_lead's changes do not accept a nullable nextTouchOn in the application")
        check("typeof changes.nextTouchOn === 'string'" in registry and "businessDayForRead" in registry, "outreach_update_lead does not judge a booked day against the application's own today")
        for code in DATE_CODES:
            check(f"'{code}'" in dates, f"the application's follow-up date module lacks {code}")
        for needle in ("retry_with_valid_date", "earliestAllowed", "latestAllowed", "problem.today"):
            check(needle in registry, f"the application's date refusal lacks {needle}")
        check("OUTREACH_FOLLOW_UP_DATE_MAX_DAYS_AHEAD = 365" in dates, "the application's date range changed: re-read the lead-management skill's refusal wording")

    suffix = f" and the application at {args.app_repo.resolve()} lets a manage_leads run book it" if args.app_repo is not None else " (pass --app-repo to check the application too)"
    print(
        "PASS: both lead-management skills list nextTouchOn among the fields a person can set, propose one day that the person confirms, "
        "clear it with null, name the three refusal codes and show Mosaico's earliestAllowed and latestAllowed, keep no date logic of their own, "
        "and point a dated, already written follow-up at the Follow Up tab and the Follow-up routine" + suffix + "."
    )


if __name__ == "__main__":
    main()
