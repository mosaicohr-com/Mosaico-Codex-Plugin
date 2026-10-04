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


def main() -> None:
    # Approved scripts pass, with and without a substituted first line, on either browser.
    check(call(TOOL, {"text": EVIDENCE})[0], "approved evidence script refused")
    check(call(TOOL, {"text": substituted(EVIDENCE, '"jane-doe_42"')})[0], "evidence script with identifier refused")
    check(call(CHROME_TOOL, {"text": substituted(CONNECTIONS, "1759400000000")})[0], "connections script with stop marker refused")
    check(call(TOOL, {"text": substituted(CONNECTIONS, "0") + "\n"})[0], "trailing newline changed the verdict")

    # The whoami script takes no variable: it passes word for word, and nothing else in its place does.
    check(call(TOOL, {"text": WHOAMI})[0], "approved whoami script refused")
    check(call(CHROME_TOOL, {"text": WHOAMI + "\n"})[0], "whoami script with trailing newline refused")
    check(not call(TOOL, {"text": WHOAMI.replace("plainId, entries })", "plainId, entries, csrf })")})[0], "edited whoami body passed")
    check(not call(TOOL, {"text": WHOAMI.replace("/voyager/api/me", "/voyager/api/mex")})[0], "one-character change to whoami passed")
    check(not call(TOOL, {"text": substituted(WHOAMI, "1")})[0], "whoami with NOOP other than 0 passed")
    check(not call(TOOL, {"text": substituted(WHOAMI, '"0"')})[0], "whoami with quoted NOOP passed")
    check(not call(TOOL, {"text": substituted(WHOAMI, "00")})[0], "whoami with NOOP 00 passed")
    check(not call(TOOL, {"text": WHOAMI + "\nconsole.log(document.cookie)"})[0], "whoami with appended line passed")

    # A changed body, an unsafe first-line value or a stray line is not the approved script.
    check(not call(TOOL, {"text": EVIDENCE.replace("entries })", "entries, csrf })")})[0], "edited body passed")
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
