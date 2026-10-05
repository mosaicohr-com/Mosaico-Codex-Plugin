#!/usr/bin/env python3
"""The browser-script gate allows only the approved capture scripts to touch LinkedIn or a credential store."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "mosaico-claude"
GATE = PLUGIN / "hooks" / "browser-script-gate.py"
BROWSER = PLUGIN / "browser"

spec = importlib.util.spec_from_file_location("gate", GATE)
gate = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(gate)

EVIDENCE = (BROWSER / "linkedin-connection-evidence.js").read_text(encoding="utf-8")
CONNECTIONS = (BROWSER / "linkedin-recent-connections.js").read_text(encoding="utf-8")
WHOAMI = (BROWSER / "linkedin-whoami.js").read_text(encoding="utf-8")
THREAD = (BROWSER / "linkedin-thread-messages.js").read_text(encoding="utf-8")
SENT = (BROWSER / "linkedin-sent-invitations.js").read_text(encoding="utf-8")
TOOL = "mcp__Claude_Browser__javascript_tool"
CHROME_TOOL = "mcp__claude-in-chrome__javascript_tool"


def call(tool_name: str, tool_input: object) -> tuple[bool, str]:
    return gate.decide({"tool_name": tool_name, "tool_input": tool_input})


def substituted(script: str, value: str) -> str:
    first, rest = script.split("\n", 1)
    name = first.split(" ")[1]
    return f"const {name} = {value};\n{rest}"


def check(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL: {message}")


def edited(script: str, old: str, new: str) -> str:
    """`script` with `old` replaced by `new`; fails when `old` is absent, so an edit check can never pass vacuously."""
    check(old in script, f"the text {old!r} is no longer in the script, so this edit check would prove nothing")
    return script.replace(old, new)


def main() -> None:
    # Approved scripts pass, with and without a substituted first line, on either browser.
    check(call(TOOL, {"text": EVIDENCE})[0], "approved evidence script refused")
    check(call(TOOL, {"text": substituted(EVIDENCE, '"jane-doe_42"')})[0], "evidence script with identifier refused")
    check(call(CHROME_TOOL, {"text": substituted(CONNECTIONS, "1759400000000")})[0], "connections script with stop marker refused")
    check(call(TOOL, {"text": substituted(CONNECTIONS, "0") + "\n"})[0], "trailing newline changed the verdict")

    # The whoami script takes no variable: it passes word for word, and nothing else in its place does.
    check(call(TOOL, {"text": WHOAMI})[0], "approved whoami script refused")
    check(call(CHROME_TOOL, {"text": WHOAMI + "\n"})[0], "whoami script with trailing newline refused")
    check(not call(TOOL, {"text": edited(WHOAMI, "plainId, entries };", "plainId, entries, csrf };")})[0], "edited whoami body passed")
    check(not call(TOOL, {"text": edited(WHOAMI, "/voyager/api/me", "/voyager/api/mex")})[0], "one-character change to whoami passed")
    check(not call(TOOL, {"text": substituted(WHOAMI, "1")})[0], "whoami with NOOP other than 0 passed")
    check(not call(TOOL, {"text": substituted(WHOAMI, '"0"')})[0], "whoami with quoted NOOP passed")
    check(not call(TOOL, {"text": substituted(WHOAMI, "00")})[0], "whoami with NOOP 00 passed")
    check(not call(TOOL, {"text": WHOAMI + "\nconsole.log(document.cookie)"})[0], "whoami with appended line passed")

    # The thread script takes the Lead's public identifier on its first line, like the evidence script.
    check(THREAD.split("\n", 1)[0] == 'const PUBLIC_IDENTIFIER = "";', "thread script's first line changed")
    check(call(TOOL, {"text": substituted(THREAD, '"jane-doe_42"')})[0], "thread script with identifier refused")
    check(call(CHROME_TOOL, {"text": substituted(THREAD, '"Jane-Doe%C3%A9"') + "\n"})[0], "thread script with encoded identifier or trailing newline refused")
    check(call("mcp__Claude_Browser__browser_batch", {"actions": [{"name": "javascript_tool", "input": {"action": "javascript_exec", "text": substituted(THREAD, '"x"')}}]})[0], "thread script in a batch refused")
    check(not call(TOOL, {"text": THREAD})[0], "thread script with an empty identifier passed")
    check(not call(TOOL, {"text": substituted(THREAD, '"a\\" + document.cookie + \\""')})[0], "thread script with unsafe identifier passed")
    check(not call(TOOL, {"text": substituted(THREAD, "1")})[0], "thread script with a number on its first line passed")
    check(not call(TOOL, {"text": edited(THREAD, "MAX_MESSAGES = 98", "MAX_MESSAGES = 9800")})[0], "edited thread script body passed")
    check(not call(TOOL, {"text": edited(THREAD, "messengerMessages.5846eeb71c981f11e0134cb6626cc314", "messengerMessages.00000000000000000000000000000000")})[0], "thread script with another query passed")
    check(not call(TOOL, {"text": THREAD + "\nconsole.log(document.cookie)"})[0], "thread script with appended line passed")
    check(not call(TOOL, {"text": "\n".join(THREAD.split("\n")[1:])})[0], "thread script without its first line passed")
    check(not call(TOOL, {"text": "const STOP_AT = 0;\n" + THREAD.split("\n", 1)[1]})[0], "thread script under another placeholder passed")
    # The thread script returns only what the application reads: never the token, and no key is named for it.
    returned = THREAD.rstrip("\n").split("\n")[-1]
    check(returned.startswith("({") and returned.endswith("})") and "csrf:" not in returned and "csrf," not in returned,
          "thread script's last line returns something other than the evidence record")
    # Only LinkedIn's own Voyager API is called.
    check(THREAD.count("https://") == 1 and 'const API = "https://www.linkedin.com/voyager/api";' in THREAD, "thread script names another address")

    # The sent-invitations script reuses the thread script's PUBLIC_IDENTIFIER placeholder and nothing else.
    check(SENT.split("\n", 1)[0] == 'const PUBLIC_IDENTIFIER = "";', "sent-invitations script's first line changed")
    check("linkedin-sent-invitations.js" in gate.approved_scripts(), "the gate does not enumerate the sent-invitations script")
    check(sorted(gate.approved_scripts()) == sorted(path.name for path in BROWSER.glob("*.js")), "the gate's approved scripts are not the browser folder")
    check(call(TOOL, {"text": substituted(SENT, '"jane-doe_42"')})[0], "sent-invitations script with identifier refused")
    check(call(CHROME_TOOL, {"text": substituted(SENT, '"Jane-Doe%C3%A9"') + "\n"})[0], "sent-invitations script with encoded identifier or trailing newline refused")
    check(call("mcp__Claude_Browser__browser_batch", {"actions": [{"name": "javascript_tool", "input": {"action": "javascript_exec", "text": substituted(SENT, '"x"')}}]})[0], "sent-invitations script in a batch refused")
    check(not call(TOOL, {"text": SENT})[0], "sent-invitations script with an empty identifier passed")
    check(not call(TOOL, {"text": substituted(SENT, '"a\\" + document.cookie + \\""')})[0], "sent-invitations script with unsafe identifier passed")
    check(not call(TOOL, {"text": edited(SENT, "MAX_PAGES = 5", "MAX_PAGES = 500")})[0], "edited sent-invitations script body passed")
    check(not call(TOOL, {"text": edited(SENT, "sentInvitationViewsV2", "invitationViews")})[0], "sent-invitations script with another endpoint passed")
    check(not call(TOOL, {"text": SENT + "\nconsole.log(document.cookie)"})[0], "sent-invitations script with appended line passed")
    check(not call(TOOL, {"text": THREAD.split("\n", 1)[0] + "\n" + SENT.split("\n", 1)[1]})[0], "sent-invitations body under the thread script's name passed")
    returned = SENT.rstrip("\n").split("\n")[-1]
    check(returned.startswith("({") and returned.endswith("})") and "csrf:" not in returned and "csrf," not in returned,
          "sent-invitations script's last line returns something other than the record")
    check(SENT.count("https://") == 1 and 'const ENDPOINT = "https://www.linkedin.com/voyager/api/relationships/sentInvitationViewsV2";' in SENT, "sent-invitations script names another address")
    check("validated: pending" in SENT, "sent-invitations script does not say its endpoint is not validated")

    # Paging, coverage and the integrity digest are part of the approved text: change one word and the script is refused.
    check("const MAX_CONVERSATION_PAGES = 8;" in THREAD and "lastUpdatedBefore:" in THREAD, "thread script lost its page limit or its cursor")
    check("messengerConversations.9501074288a12f3ae9e3c7ea243bccbf" in THREAD and "(query:(predicateUnions:List((conversationCategoryPredicate:(category:PRIMARY_INBOX)))),count:20,mailboxUrn:" in THREAD
          and "validated: paging call observed 6 Oct 2026" in THREAD, "thread script lost LinkedIn's paged query")
    check(not call(TOOL, {"text": substituted(edited(THREAD, "messengerConversations.9501074288a12f3ae9e3c7ea243bccbf", "messengerConversations.0d5e6781bbee71c3e51c8843c6519f48"), '"x"')})[0], "thread script with another paged query id passed")
    check(not call(TOOL, {"text": substituted(edited(THREAD, "category:PRIMARY_INBOX", "category:OTHER"), '"x"')})[0], "thread script with another category passed")
    check(not call(TOOL, {"text": substituted(edited(THREAD, "MAX_CONVERSATION_PAGES = 8", "MAX_CONVERSATION_PAGES = 800"), '"x"')})[0], "thread script with another page limit passed")
    check(not call(TOOL, {"text": substituted(edited(THREAD, "lastUpdatedBefore:", "lastUpdatedAfter:"), '"x"')})[0], "thread script with another cursor name passed")
    check(not call(TOOL, {"text": substituted(edited(THREAD, 'coverage = best !== null || exhausted ? "complete" : "page-limit";', 'coverage = "complete";'), '"x"')})[0], "thread script that always claims complete coverage passed")
    for label, script, first in (("whoami", WHOAMI, None), ("evidence", EVIDENCE, '"x"'), ("connections", CONNECTIONS, "1"), ("thread", THREAD, '"x"'), ("sent", SENT, '"x"')):
        body = script if first is None else substituted(script, first)
        check(call(TOOL, {"text": body})[0], f"{label} script with the integrity digest refused")
        check(call(CHROME_TOOL, {"text": body + "\n"})[0], f"{label} script with trailing newline refused")
        check("const canonical = " in script and "const fnv1a32 = " in script, f"{label} script has no digest helpers")
        check(not call(TOOL, {"text": edited(body, "0x01000193", "0x01000194")})[0], f"{label} script with an altered digest constant passed")
        check(not call(TOOL, {"text": edited(body, ".sort()", ".reverse()")})[0], f"{label} script with an altered canonical form passed")
        check(not call(TOOL, {"text": edited(body, '"fnv1a32", digest', '"fnv1a32", digest: "00000000", x')})[0], f"{label} script with a forged digest passed")
        last = script.rstrip("\n").split("\n")[-1]
        check(last.startswith("({") and last.endswith("})") and "csrf" not in last, f"{label} script's last line is not a single record expression without the token")
        check(last == '({ ...payload, integrity: { algorithm: "fnv1a32", digest: fnv1a32(canonical(payload)) } })', f"{label} script's last line is not the sealed payload")
        check(script.count("https://") == 1, f"{label} script names more than one address")
    check(call(TOOL, {"text": substituted(CONNECTIONS, "0")})[0] and "pages.push(sealed({ elements, entries }));" in CONNECTIONS, "connections script does not seal each page")
    check(not call(TOOL, {"text": edited(CONNECTIONS, "pages.push(sealed({ elements, entries }));", "pages.push({ elements, entries });")})[0], "connections script without page seals passed")
    check(sorted(gate.approved_scripts()) == sorted(path.name for path in BROWSER.glob("*.js")) and len(gate.approved_scripts()) == 5, "the gate's approved scripts are not the five scripts in the browser folder")
    check(not call(TOOL, {"text": EVIDENCE + "\nfetch('https://www.linkedin.com/voyager/api/me')"})[0], "evidence script with a second LinkedIn call passed")

    # A changed body, an unsafe first-line value or a stray line is not the approved script.
    check(not call(TOOL, {"text": edited(EVIDENCE, "entries };", "entries, csrf };")})[0], "edited body passed")
    check(not call(TOOL, {"text": substituted(EVIDENCE, '"a\\" + document.cookie + \\""')})[0], "unsafe identifier passed")
    check(not call(TOOL, {"text": substituted(CONNECTIONS, "-1")})[0], "negative stop marker passed")
    check(not call(TOOL, {"text": EVIDENCE + "\nconsole.log(document.cookie)"})[0], "appended line passed")
    check(not call(TOOL, {"text": "\n".join(EVIDENCE.split("\n")[1:])})[0], "script without its first line passed")

    # Any other script that reaches for LinkedIn or a credential store is refused.
    for script in (
        "document.cookie",
        "fetch('https://www.linkedin.com/voyager/api/me')",
        "window.localStorage.getItem('x')",
        "indexedDB.databases()",
        "navigator.credentials.get()",
        "chrome.cookies.getAll({})",
        "const t = (document.cookie.match(/JSESSIONID=\"?([^;\"]+)/) || [])[1]",
    ):
        allowed, reason = call(TOOL, {"text": script})
        check(not allowed, f"restricted script passed: {script}")
        check(script not in reason and "cookie" in reason, "refusal echoed the script or lost its guidance")

    # Scripts about anything else are not this gate's business.
    check(call(TOOL, {"text": "document.title"})[0], "harmless script refused")
    check(call(TOOL, {"text": "getComputedStyle(document.body).color"})[0], "style read refused")

    # A batch is judged item by item; one bad item refuses the whole batch.
    batch_ok = {"actions": [{"name": "navigate", "input": {"url": "https://www.linkedin.com/in/x"}},
                            {"name": "javascript_tool", "input": {"action": "javascript_exec", "text": substituted(EVIDENCE, '"x"')}}]}
    batch_bad = {"actions": [{"name": "javascript_tool", "input": {"action": "javascript_exec", "text": "document.cookie"}}]}
    check(call("mcp__Claude_Browser__browser_batch", batch_ok)[0], "approved batch refused")
    check(not call("mcp__Claude_Browser__browser_batch", batch_bad)[0], "batch with cookie read passed")

    # Unreadable calls fail closed.
    check(not call(TOOL, {})[0], "script call without text passed")
    check(not gate.decide({"tool_input": {"text": "1"}})[0], "call without a tool name passed")
    check(not call("mcp__Claude_Browser__browser_batch", {"actions": "nope"})[0], "unreadable batch passed")

    # The hook itself: stdin in, exit code out, nothing on stdout.
    env = {"PATH": "/usr/bin:/bin:/usr/local/bin"}
    ok = subprocess.run([sys.executable, str(GATE)], input=json.dumps({"tool_name": TOOL, "tool_input": {"text": EVIDENCE}}),
                        capture_output=True, text=True, env=env, check=False)
    check(ok.returncode == 0 and ok.stdout == "", "hook did not allow the approved script silently")
    bad = subprocess.run([sys.executable, str(GATE)], input=json.dumps({"tool_name": TOOL, "tool_input": {"text": "document.cookie"}}),
                         capture_output=True, text=True, env=env, check=False)
    check(bad.returncode == 2 and "refused" in bad.stderr and "document.cookie" not in bad.stderr, "hook did not refuse cleanly")
    broken = subprocess.run([sys.executable, str(GATE)], input="not json", capture_output=True, text=True, env=env, check=False)
    check(broken.returncode == 2, "hook did not fail closed on unreadable input")

    hooks = json.loads((PLUGIN / "hooks" / "hooks.json").read_text(encoding="utf-8"))
    matcher = hooks["hooks"]["PreToolUse"][0]["matcher"]
    import re
    for name in (TOOL, CHROME_TOOL, "mcp__Claude_Browser__browser_batch", "mcp__claude-in-chrome__browser_batch"):
        check(re.fullmatch(matcher, name) is not None, f"hook matcher misses {name}")
    print("PASS: browser-script gate allows only the approved capture scripts to touch LinkedIn or credentials.")


if __name__ == "__main__":
    main()
