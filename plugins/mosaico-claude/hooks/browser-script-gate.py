#!/usr/bin/env python3
"""Browser-script gate for the Mosaico Outreach skills.

Runs as a PreToolUse hook before every browser script call (the built-in browser pane's and the Chrome
extension's `javascript_tool`, alone or inside a `browser_batch`). It is the enforcement half of the
connection-evidence capability:

* A script that is one of the approved capture scripts under `browser/`, word for word apart from the
  value on its first line, is allowed.
* Any other script that names LinkedIn, its API, its session or CSRF material, or reads a credential
  store (cookies, web storage, IndexedDB, the credentials API, extension APIs) is refused.
* Every other script is none of this gate's business and passes.

Fail closed: unreadable input is refused. Nothing is logged: the refusal names the approved scripts and
never echoes the submitted script, a header, a cookie or a response.

Exit 0 allows. Exit 2 refuses, with the reason on stderr.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APPROVED_DIR = Path(__file__).resolve().parent.parent / "browser"

# First-line placeholders and the values a run may put in their place.
PLACEHOLDERS: dict[str, tuple[str, re.Pattern[str]]] = {
    "PUBLIC_IDENTIFIER": ('"PUBLIC_IDENTIFIER"', re.compile(r'^"[A-Za-z0-9._%-]{1,120}"$')),
    "STOP_AT": ("0", re.compile(r"^[0-9]{1,16}$")),
}
FIRST_LINE = re.compile(r"^const (?P<name>[A-Z_]+) = (?P<value>.+);$")

SCRIPT_TOOL = re.compile(r"(^|__)javascript_tool$")
BATCH_TOOL = re.compile(r"(^|__)browser_batch$")

RESTRICTED = re.compile(
    r"linkedin|voyager|li_at|jsessionid|csrf"
    r"|\bcookie\b|document\s*\.\s*cookie|cookieStore"
    r"|localStorage|sessionStorage|indexedDB|openDatabase"
    r"|navigator\s*\.\s*credentials|PasswordCredential|FederatedCredential"
    r"|\bchrome\s*\.|\bbrowser\s*\.(cookies|storage|tabs|runtime)",
    re.IGNORECASE,
)


def _normalise(text: str) -> list[str]:
    return [line.rstrip() for line in text.replace("\r\n", "\n").strip("\n").split("\n")]


def approved_scripts() -> dict[str, list[str]]:
    scripts: dict[str, list[str]] = {}
    if APPROVED_DIR.is_dir():
        for path in sorted(APPROVED_DIR.glob("*.js")):
            scripts[path.name] = _normalise(path.read_text(encoding="utf-8"))
    return scripts


def matches_approved(script: str, approved: dict[str, list[str]]) -> str | None:
    """Return the approved script's name when `script` is it, apart from a permitted first-line value."""
    lines = _normalise(script)
    if not lines:
        return None
    head = FIRST_LINE.match(lines[0])
    if head is None:
        return None
    placeholder = PLACEHOLDERS.get(head.group("name"))
    if placeholder is None or not placeholder[1].match(head.group("value")):
        return None
    canonical = [f"const {head.group('name')} = {placeholder[0]};", *lines[1:]]
    for name, body in approved.items():
        if body == canonical:
            return name
    return None


def scripts_in(tool_name: str, tool_input: object) -> list[str] | None:
    """The scripts a call carries, or None when the call is unreadable."""
    if not isinstance(tool_input, dict):
        return None
    if SCRIPT_TOOL.search(tool_name):
        text = tool_input.get("text")
        return [text] if isinstance(text, str) else None
    if BATCH_TOOL.search(tool_name):
        actions = tool_input.get("actions")
        if not isinstance(actions, list):
            return None
        found: list[str] = []
        for action in actions:
            if not isinstance(action, dict):
                return None
            name = action.get("name")
            if isinstance(name, str) and SCRIPT_TOOL.search(name):
                inner = action.get("input")
                text = inner.get("text") if isinstance(inner, dict) else None
                if not isinstance(text, str):
                    return None
                found.append(text)
        return found
    return []


def decide(payload: object) -> tuple[bool, str]:
    """(allowed, reason). The reason never contains any part of the submitted script."""
    if not isinstance(payload, dict) or not isinstance(payload.get("tool_name"), str):
        return False, "Browser-script gate: the call could not be read, so it was refused."
    scripts = scripts_in(payload["tool_name"], payload.get("tool_input"))
    if scripts is None:
        return False, "Browser-script gate: the script call could not be read, so it was refused."
    approved = approved_scripts()
    names = ", ".join(sorted(approved)) or "none installed"
    for script in scripts:
        if matches_approved(script, approved):
            continue
        if RESTRICTED.search(script):
            return False, (
                "Browser-script gate: refused. LinkedIn requests and credential stores may only be touched "
                f"by an approved capture script, run word for word with only its first line changed ({names}). "
                "Do not read cookies, storage, profile files, DevTools data or the keychain. "
                "Use what the LinkedIn page visibly shows, or stop this step and report it."
            )
    return True, ""


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:  # noqa: BLE001 - fail closed on any unreadable input
        print("Browser-script gate: the call could not be read, so it was refused.", file=sys.stderr)
        return 2
    allowed, reason = decide(payload)
    if allowed:
        return 0
    print(reason, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
