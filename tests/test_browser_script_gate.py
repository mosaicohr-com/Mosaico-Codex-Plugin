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
    check(SENT.count("https://") == 2 and 'const ENDPOINT = "https://www.linkedin.com/voyager/api/relationships/sentInvitationViewsV2";' in SENT
          and 'const PROFILE_ENDPOINT = "https://www.linkedin.com/voyager/api/graphql";' in SENT, "sent-invitations script names another address")
    check("validated: pending" in SENT, "sent-invitations script does not say its endpoint is not validated")

    # Paging, coverage and the integrity digest are part of the approved text: change one word and the script is refused.
    check("const MAX_CONVERSATION_PAGES = 8;" in THREAD and "lastUpdatedBefore:" in THREAD, "thread script lost its page limit or its cursor")
    check("messengerConversations.9501074288a12f3ae9e3c7ea243bccbf" in THREAD and "(query:(predicateUnions:List((conversationCategoryPredicate:(category:PRIMARY_INBOX)))),count:20,mailboxUrn:" in THREAD
          and "validated: paging call observed 6 Oct 2026" in THREAD, "thread script lost LinkedIn's paged query")
    check(not call(TOOL, {"text": substituted(edited(THREAD, "messengerConversations.9501074288a12f3ae9e3c7ea243bccbf", "messengerConversations.0d5e6781bbee71c3e51c8843c6519f48"), '"x"')})[0], "thread script with another paged query id passed")
    check(not call(TOOL, {"text": substituted(edited(THREAD, "category:PRIMARY_INBOX", "category:OTHER"), '"x"')})[0], "thread script with another category passed")
    check(not call(TOOL, {"text": substituted(edited(THREAD, "MAX_CONVERSATION_PAGES = 8", "MAX_CONVERSATION_PAGES = 800"), '"x"')})[0], "thread script with another page limit passed")
    check(not call(TOOL, {"text": substituted(edited(THREAD, "lastUpdatedBefore:", "lastUpdatedAfter:"), '"x"')})[0], "thread script with another cursor name passed")
    check(not call(TOOL, {"text": substituted(edited(THREAD, 'coverage = best !== null || (searchOk && exhausted) ? "complete" : "page-limit";', 'coverage = "complete";'), '"x"')})[0], "thread script that always claims complete coverage passed")
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
        # The sent-invitations script names LinkedIn's list and (for a vanity) LinkedIn's profile query; every other script names one address.
        check(script.count("https://") == (2 if label == "sent" else 1), f"{label} script names more than one address")
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

    # An opaque member id (ACoAA..., 0.8.6) is an identifier like any other: word for word and through the directive, for the three identifier scripts.
    for label, script in (("evidence", EVIDENCE), ("thread", THREAD), ("sent", SENT)):
        check(call(TOOL, {"text": substituted(script, '"ACoAAB1x_y-Z"')})[0], f"{label} script with an opaque member id refused")
        check(not call(TOOL, {"text": edited(substituted(script, '"ACoAAB1x_y-Z"'), "ACoAA[A-Za-z0-9_-]+", "ACoAA[A-Za-z0-9_-]*")})[0], f"{label} script with an edited opaque id pattern passed")
        check("const OPAQUE_ID = /^ACoAA[A-Za-z0-9_-]+$/;" in script, f"{label} script lost the opaque member id pattern")

    # The run directive: one line stands for an approved script, and the hook rewrites the call to it.
    def expand(tool_name: str, tool_input: object) -> tuple[bool, str, object]:
        return gate.evaluate({"tool_name": tool_name, "tool_input": tool_input})

    def replaced(script: str, first: str) -> str:
        return first + "\n" + script.split("\n", 1)[1]

    directives = (
        ("linkedin-whoami.js", "// mosaico run linkedin-whoami.js", WHOAMI),
        ("linkedin-connection-evidence.js", "// mosaico run linkedin-connection-evidence.js", EVIDENCE),
        ("linkedin-connection-evidence.js", "// mosaico run linkedin-connection-evidence.js PUBLIC_IDENTIFIER=jane-doe_42",
         replaced(EVIDENCE, 'const PUBLIC_IDENTIFIER = "jane-doe_42";')),
        ("linkedin-recent-connections.js", "// mosaico run linkedin-recent-connections.js", CONNECTIONS),
        ("linkedin-recent-connections.js", "// mosaico run linkedin-recent-connections.js STOP_AT=1759400000000",
         replaced(CONNECTIONS, "const STOP_AT = 1759400000000;")),
        ("linkedin-thread-messages.js", "// mosaico run linkedin-thread-messages.js PUBLIC_IDENTIFIER=Jane-Doe%C3%A9",
         replaced(THREAD, 'const PUBLIC_IDENTIFIER = "Jane-Doe%C3%A9";')),
        ("linkedin-thread-messages.js", '// mosaico run linkedin-thread-messages.js PUBLIC_IDENTIFIER="jane-doe"\n',
         replaced(THREAD, 'const PUBLIC_IDENTIFIER = "jane-doe";')),
        ("linkedin-connection-evidence.js", "// mosaico run linkedin-connection-evidence.js PUBLIC_IDENTIFIER=ACoAAB1x_y-Z",
         replaced(EVIDENCE, 'const PUBLIC_IDENTIFIER = "ACoAAB1x_y-Z";')),
        ("linkedin-thread-messages.js", "// mosaico run linkedin-thread-messages.js PUBLIC_IDENTIFIER=ACoAAB1x_y-Z",
         replaced(THREAD, 'const PUBLIC_IDENTIFIER = "ACoAAB1x_y-Z";')),
        ("linkedin-sent-invitations.js", "// mosaico run linkedin-sent-invitations.js PUBLIC_IDENTIFIER=ACoAAB1x_y-Z",
         replaced(SENT, 'const PUBLIC_IDENTIFIER = "ACoAAB1x_y-Z";')),
        ("linkedin-sent-invitations.js", "// mosaico run linkedin-sent-invitations.js PUBLIC_IDENTIFIER=jane-doe",
         replaced(SENT, 'const PUBLIC_IDENTIFIER = "jane-doe";')),
    )
    check({name for name, _, _ in directives} == set(gate.approved_scripts()), "the directive checks do not cover every approved script")
    for name, directive, expected in directives:
        for tool in (TOOL, CHROME_TOOL):
            allowed, reason, updated = expand(tool, {"action": "javascript_exec", "text": directive, "tabId": 7})
            check(allowed and reason == "", f"directive refused: {directive}")
            check(updated == {"action": "javascript_exec", "text": expected, "tabId": 7}, f"directive did not expand to the approved script with every other field kept: {directive}")
            check(call(tool, {"text": updated["text"]})[0], f"the expanded script is not itself approved: {directive}")
        batch = {"actions": [{"name": "navigate", "input": {"url": "https://www.linkedin.com/in/x"}},
                             {"name": "javascript_tool", "input": {"action": "javascript_exec", "text": directive}},
                             {"name": "javascript_tool", "input": {"action": "javascript_exec", "text": "document.title"}}], "other": 1}
        allowed, _, updated = expand("mcp__Claude_Browser__browser_batch", batch)
        check(allowed and updated is not None, f"directive in a batch refused: {directive}")
        check(updated["actions"][1]["input"] == {"action": "javascript_exec", "text": expected}
              and updated["actions"][0] == batch["actions"][0] and updated["actions"][2] == batch["actions"][2] and updated["other"] == 1,
              f"batch directive expanded wrongly or touched another item: {directive}")
        check(batch["actions"][1]["input"]["text"] == directive, "the submitted call was modified in place")
    # Word for word stays allowed and is not rewritten.
    for script in (EVIDENCE, WHOAMI, substituted(THREAD, '"x"')):
        allowed, _, updated = expand(TOOL, {"text": script})
        check(allowed and updated is None, "a word-for-word script was rewritten or refused")

    # An invalid directive is refused, naming the valid directives and never echoing what was sent.
    invalid = (
        "// mosaico run linkedin-unknown.js",
        "// mosaico run ../browser/linkedin-whoami.js",
        "// mosaico run linkedin-whoami.js NOOP=0",
        "// mosaico run linkedin-whoami.js PUBLIC_IDENTIFIER=x",
        "// mosaico run linkedin-connection-evidence.js STOP_AT=1",
        "// mosaico run linkedin-recent-connections.js PUBLIC_IDENTIFIER=x",
        "// mosaico run linkedin-recent-connections.js STOP_AT=-1",
        "// mosaico run linkedin-recent-connections.js STOP_AT=abc",
        "// mosaico run linkedin-thread-messages.js",
        "// mosaico run linkedin-thread-messages.js PUBLIC_IDENTIFIER=a\"+document.cookie+\"",
        "// mosaico run linkedin-thread-messages.js PUBLIC_IDENTIFIER=",
        "// mosaico run linkedin-thread-messages.js PUBLIC_IDENTIFIER=a b",
        "// mosaico run linkedin-sent-invitations.js PUBLIC_IDENTIFIER=" + "a" * 121,
        "// mosaico run linkedin-thread-messages.js PUBLIC_IDENTIFIER=x\nconsole.log(document.cookie)",
        "// mosaico run linkedin-thread-messages.js PUBLIC_IDENTIFIER=x; fetch('https://www.linkedin.com/voyager/api/me')",
        "// mosaico run",
        "//mosaico run linkedin-whoami.js",
    )
    for directive in invalid:
        for tool_input, tool in (({"text": directive}, TOOL),
                                 ({"actions": [{"name": "javascript_tool", "input": {"text": directive}}]}, "mcp__Claude_Browser__browser_batch")):
            allowed, reason, updated = expand(tool, tool_input)
            check(not allowed and updated is None, f"invalid directive passed: {directive!r}")
            check("// mosaico run linkedin-whoami.js" in reason and "PUBLIC_IDENTIFIER=<public identifier>" in reason and "STOP_AT=<whole number>" in reason,
                  "the refusal does not name the valid directives")
            check("unknown" not in reason and "cookie" not in reason.replace("credential", "") and "fetch" not in reason, "the refusal echoed the submitted directive")
    # One bad directive refuses a whole batch, and a directive plus another script is judged item by item.
    mixed = {"actions": [{"name": "javascript_tool", "input": {"text": "// mosaico run linkedin-whoami.js"}},
                         {"name": "javascript_tool", "input": {"text": "document.cookie"}}]}
    check(not call("mcp__Claude_Browser__browser_batch", mixed)[0], "batch with a directive and a cookie read passed")
    # Retyped with a change is still refused.
    check(not call(TOOL, {"text": edited(substituted(THREAD, '"x"'), "MAX_MESSAGES = 98", "MAX_MESSAGES = 99")})[0], "a retyped script with one changed line passed")

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
    directive = subprocess.run([sys.executable, str(GATE)], input=json.dumps({"tool_name": TOOL, "tool_input": {"action": "javascript_exec", "text": "// mosaico run linkedin-thread-messages.js PUBLIC_IDENTIFIER=jane-doe", "tabId": 3}}),
                               capture_output=True, text=True, env=env, check=False)
    out = json.loads(directive.stdout) if directive.returncode == 0 else {}
    specific = out.get("hookSpecificOutput", {})
    check(directive.returncode == 0 and set(out) == {"hookSpecificOutput"} and specific.get("hookEventName") == "PreToolUse"
          and specific.get("permissionDecision") == "allow"
          and specific.get("updatedInput") == {"action": "javascript_exec", "text": substituted(THREAD, '"jane-doe"'), "tabId": 3},
          "hook did not print the PreToolUse allow decision with updatedInput for a directive")
    refused = subprocess.run([sys.executable, str(GATE)], input=json.dumps({"tool_name": TOOL, "tool_input": {"text": "// mosaico run linkedin-whoami.js X=1"}}),
                             capture_output=True, text=True, env=env, check=False)
    check(refused.returncode == 2 and refused.stdout == "" and "X=1" not in refused.stderr and "linkedin-thread-messages.js" in refused.stderr, "hook did not refuse an invalid directive cleanly")
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
