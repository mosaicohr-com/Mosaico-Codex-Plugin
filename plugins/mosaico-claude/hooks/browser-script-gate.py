#!/usr/bin/env python3
"""Browser-script gate for the Mosaico Outreach skills.

Runs as a PreToolUse hook before every browser script call (the built-in browser pane's and the Chrome
extension's `javascript_tool`, alone or inside a `browser_batch`). It is the enforcement half of the
connection-evidence capability:

* A script that is one of the approved capture scripts under `browser/`, word for word apart from the
  value on its first line, is allowed.
* A one-line directive, `// mosaico run <script>.js [<PLACEHOLDER>=<value>]`, as the whole script is expanded:
  the hook rewrites the call's `text` to the approved script with its first line set, so a long script is
  never retyped. Claude Code's PreToolUse contract: print `hookSpecificOutput` with `hookEventName`
  "PreToolUse", `permissionDecision` "allow" and `updatedInput` (the complete replacement tool input) and
  exit 0. A malformed directive is refused.
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
    "NOOP": ("0", re.compile(r"^0$")),
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


def _canonical(lines: list[str]) -> list[str] | None:
    """`lines` with its first line's value replaced by the placeholder's canonical one, or None.

    None means the first line is not a recognised placeholder or its value is not one a run may put there.
    An approved script is held in this form too, so a template whose first line carries any placeholder
    value (an empty identifier, a stop marker of 0) is the same script as a run's with a real value.
    """
    head = FIRST_LINE.match(lines[0]) if lines else None
    if head is None:
        return None
    placeholder = PLACEHOLDERS.get(head.group("name"))
    if placeholder is None or not placeholder[1].match(head.group("value")):
        return None
    return [f"const {head.group('name')} = {placeholder[0]};", *lines[1:]]


def approved_scripts() -> dict[str, list[str]]:
    """Each approved script, its first line in canonical form."""
    scripts: dict[str, list[str]] = {}
    if APPROVED_DIR.is_dir():
        for path in sorted(APPROVED_DIR.glob("*.js")):
            lines = _normalise(path.read_text(encoding="utf-8"))
            head = FIRST_LINE.match(lines[0]) if lines else None
            placeholder = PLACEHOLDERS.get(head.group("name")) if head else None
            # A template's own first-line value need not satisfy the run-time pattern (the thread script's is empty).
            scripts[path.name] = (
                [f"const {head.group('name')} = {placeholder[0]};", *lines[1:]] if head and placeholder else lines
            )
    return scripts


def matches_approved(script: str, approved: dict[str, list[str]]) -> str | None:
    """Return the approved script's name when `script` is it, apart from a permitted first-line value."""
    canonical = _canonical(_normalise(script))
    if canonical is None:
        return None
    for name, body in approved.items():
        if body == canonical:
            return name
    return None


def script_slots(tool_name: str, tool_input: object) -> list[tuple[int | None, str]] | None:
    """The scripts a call carries as (batch index or None, text), or None when the call is unreadable."""
    if not isinstance(tool_input, dict):
        return None
    if SCRIPT_TOOL.search(tool_name):
        text = tool_input.get("text")
        return [(None, text)] if isinstance(text, str) else None
    if BATCH_TOOL.search(tool_name):
        actions = tool_input.get("actions")
        if not isinstance(actions, list):
            return None
        found: list[tuple[int | None, str]] = []
        for index, action in enumerate(actions):
            if not isinstance(action, dict):
                return None
            name = action.get("name")
            if isinstance(name, str) and SCRIPT_TOOL.search(name):
                inner = action.get("input")
                text = inner.get("text") if isinstance(inner, dict) else None
                if not isinstance(text, str):
                    return None
                found.append((index, text))
        return found
    return []


def scripts_in(tool_name: str, tool_input: object) -> list[str] | None:
    """The scripts a call carries, or None when the call is unreadable."""
    slots = script_slots(tool_name, tool_input)
    return None if slots is None else [text for _, text in slots]


DIRECTIVE_START = re.compile(r"^\s*//\s*mosaico\s+run\b", re.IGNORECASE)
DIRECTIVE = re.compile(r"^// mosaico run (?P<script>[A-Za-z0-9._-]+\.js)(?: (?P<name>[A-Z_]+)=(?P<value>\S+))?$")
IDENTIFIER = re.compile(r"^[A-Za-z0-9._%-]{1,120}$")


def _first_line_name(raw: str) -> str | None:
    head = FIRST_LINE.match(raw.split("\n", 1)[0].rstrip())
    return head.group("name") if head else None


def valid_directives(raw_scripts: dict[str, str]) -> str:
    """The directives a run may send, for the refusal message."""
    forms = []
    for name, raw in sorted(raw_scripts.items()):
        placeholder = _first_line_name(raw)
        if placeholder == "PUBLIC_IDENTIFIER":
            forms.append(f"// mosaico run {name} PUBLIC_IDENTIFIER=<public identifier>")
        elif placeholder == "STOP_AT":
            forms.append(f"// mosaico run {name} STOP_AT=<whole number>")
        else:
            forms.append(f"// mosaico run {name}")
    return "; ".join(forms) or "none installed"


def raw_approved_scripts() -> dict[str, str]:
    if not APPROVED_DIR.is_dir():
        return {}
    return {path.name: path.read_text(encoding="utf-8") for path in sorted(APPROVED_DIR.glob("*.js"))}


def expand_directive(script: str, raw_scripts: dict[str, str]) -> str | None:
    """The approved script a valid directive stands for, its first line set; None when the directive is not valid."""
    lines = script.replace("\r\n", "\n").strip("\n").split("\n")
    match = DIRECTIVE.match(lines[0].rstrip()) if len(lines) == 1 else None
    if match is None:
        return None
    raw = raw_scripts.get(match.group("script"))
    if raw is None:
        return None
    placeholder = _first_line_name(raw)
    if placeholder is None or placeholder not in PLACEHOLDERS:
        return None
    assigned, value = match.group("name"), match.group("value")
    if assigned is None:
        head = FIRST_LINE.match(raw.split("\n", 1)[0].rstrip())
        # No value: only a script whose own first line is a value a run may use (not an empty identifier).
        if head is None or not PLACEHOLDERS[placeholder][1].match(head.group("value")):
            return None
        return raw
    if assigned != placeholder or placeholder == "NOOP":
        return None
    if placeholder == "PUBLIC_IDENTIFIER":
        bare = value[1:-1] if len(value) >= 2 and value[0] == value[-1] == '"' else value
        if not IDENTIFIER.match(bare):
            return None
        literal = f'"{bare}"'
    else:
        if not PLACEHOLDERS[placeholder][1].match(value):
            return None
        literal = value
    rest = raw.split("\n", 1)[1] if "\n" in raw else ""
    return f"const {placeholder} = {literal};\n{rest}" if "\n" in raw else f"const {placeholder} = {literal};"


def evaluate(payload: object) -> tuple[bool, str, dict | None]:
    """(allowed, reason, updatedInput or None). The reason never contains any part of the submitted script."""
    if not isinstance(payload, dict) or not isinstance(payload.get("tool_name"), str):
        return False, "Browser-script gate: the call could not be read, so it was refused.", None
    tool_name, tool_input = payload["tool_name"], payload.get("tool_input")
    slots = script_slots(tool_name, tool_input)
    if slots is None:
        return False, "Browser-script gate: the script call could not be read, so it was refused.", None
    approved = approved_scripts()
    names = ", ".join(sorted(approved)) or "none installed"
    raw_scripts = raw_approved_scripts()
    expansions: dict[int | None, str] = {}
    for slot, script in slots:
        if DIRECTIVE_START.match(script):
            expanded = expand_directive(script, raw_scripts)
            if expanded is None:
                return False, (
                    "Browser-script gate: refused. The run directive is not valid. It must be the whole script, "
                    f"one line, exactly one of: {valid_directives(raw_scripts)}. "
                    "Send one of those lines, or run an approved script word for word."
                ), None
            expansions[slot] = expanded
            continue
        if matches_approved(script, approved):
            continue
        if RESTRICTED.search(script):
            return False, (
                "Browser-script gate: refused. LinkedIn requests and credential stores may only be touched "
                f"by an approved capture script, run word for word with only its first line changed ({names}), "
                f"or by sending one of its run directives ({valid_directives(raw_scripts)}). "
                "Do not read cookies, storage, profile files, DevTools data or the keychain. "
                "Use what the LinkedIn page visibly shows, or stop this step and report it."
            ), None
    if not expansions:
        return True, "", None
    updated = json.loads(json.dumps(tool_input))
    if None in expansions:
        updated["text"] = expansions[None]
    else:
        for index, text in expansions.items():
            updated["actions"][index]["input"]["text"] = text
    return True, "", updated


def decide(payload: object) -> tuple[bool, str]:
    """(allowed, reason). The reason never contains any part of the submitted script."""
    allowed, reason, _ = evaluate(payload)
    return allowed, reason


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:  # noqa: BLE001 - fail closed on any unreadable input
        print("Browser-script gate: the call could not be read, so it was refused.", file=sys.stderr)
        return 2
    allowed, reason, updated = evaluate(payload)
    if allowed:
        if updated is not None:
            print(json.dumps({"hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow",
                "permissionDecisionReason": "Browser-script gate: run directive expanded to the approved script.",
                "updatedInput": updated,
            }}))
        return 0
    print(reason, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
