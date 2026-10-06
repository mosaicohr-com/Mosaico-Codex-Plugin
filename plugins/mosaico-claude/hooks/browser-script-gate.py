#!/usr/bin/env python3
"""Browser-script gate for the Mosaico Outreach skills.

Runs as a PreToolUse hook before every browser script call (the built-in browser pane's and the Chrome
extension's `javascript_tool`, alone or inside a `browser_batch`). It is the enforcement half of the
connection-evidence capability:

* A script that is one of the approved capture scripts under `browser/`, word for word apart from the
  values on its leading placeholder lines (the first line; for the thread script also the second, `LEAD_NAME`),
  is allowed.
* A one-line directive, `// mosaico run <script>.js [<PLACEHOLDER>=<value> ...]`, as the whole script is expanded:
  the hook rewrites the call's `text` to the approved script with its placeholder lines set, so a long script is
  never retyped. The thread script takes two: `PUBLIC_IDENTIFIER=<id> LEAD_NAME=<name>` (the name is the rest of the
  line, so it may hold spaces). Claude Code's PreToolUse contract: print `hookSpecificOutput` with `hookEventName`
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
# A name goes into a double-quoted string literal, so it may hold anything except a quote, a backslash or a control character.
NAME_BODY = r'[^"\\\x00-\x1f\x7f-\x9f\u2028\u2029]'
PLACEHOLDERS: dict[str, tuple[str, re.Pattern[str]]] = {
    "PUBLIC_IDENTIFIER": ('"PUBLIC_IDENTIFIER"', re.compile(r'^"[A-Za-z0-9._%-]{1,120}"$')),
    "LEAD_NAME": ('"LEAD_NAME"', re.compile(r'^"' + NAME_BODY + r'{0,120}"$')),
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


def _leading_placeholders(lines: list[str]) -> list[tuple[str, str]]:
    """The (name, value) of each consecutive leading `const NAME = value;` line whose NAME is a known placeholder."""
    found: list[tuple[str, str]] = []
    for line in lines:
        head = FIRST_LINE.match(line)
        if head is None or head.group("name") not in PLACEHOLDERS:
            break
        found.append((head.group("name"), head.group("value")))
    return found


def _canonical(lines: list[str]) -> list[str] | None:
    """`lines` with each leading placeholder line's value replaced by the placeholder's canonical one, or None.

    None means the first line is not a recognised placeholder or a placeholder value is not one a run may put there.
    An approved script is held in this form too, so a template whose placeholder lines carry any placeholder
    value (an empty identifier, a stop marker of 0) is the same script as a run's with real values.
    """
    leading = _leading_placeholders(lines)
    if not leading:
        return None
    if any(not PLACEHOLDERS[name][1].match(value) for name, value in leading):
        return None
    return [*(f"const {name} = {PLACEHOLDERS[name][0]};" for name, _ in leading), *lines[len(leading):]]


def approved_scripts() -> dict[str, list[str]]:
    """Each approved script, its first line in canonical form."""
    scripts: dict[str, list[str]] = {}
    if APPROVED_DIR.is_dir():
        for path in sorted(APPROVED_DIR.glob("*.js")):
            lines = _normalise(path.read_text(encoding="utf-8"))
            leading = _leading_placeholders(lines)
            # A template's own placeholder values need not satisfy the run-time pattern (the thread script's are empty).
            scripts[path.name] = (
                [*(f"const {name} = {PLACEHOLDERS[name][0]};" for name, _ in leading), *lines[len(leading):]]
                if leading else lines
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
DIRECTIVE = re.compile(r"^// mosaico run (?P<script>[A-Za-z0-9._-]+\.js)(?P<rest>(?: [A-Z_]+=.+)?)$")
ASSIGNMENT = re.compile(r" (?P<name>[A-Z_]+)=")
TOKEN = re.compile(r"\S+")
IDENTIFIER = re.compile(r"^[A-Za-z0-9._%-]{1,120}$")
LEAD_NAME_VALUE = re.compile(r"^" + NAME_BODY + r"{1,120}$")
# The one placeholder whose value may hold spaces: it is the rest of the line, so it comes last.
REST_OF_LINE = "LEAD_NAME"


def _placeholder_names(raw: str) -> list[str]:
    """The placeholders an approved script takes, in order: its consecutive leading placeholder lines."""
    return [name for name, _ in _leading_placeholders(raw.replace("\r\n", "\n").split("\n"))]


def _assignments(rest: str) -> list[tuple[str, str]] | None:
    """`NAME=value` pairs of a directive's tail, or None when it is not made of them. A LEAD_NAME value runs to the line's end."""
    found: list[tuple[str, str]] = []
    while rest:
        head = ASSIGNMENT.match(rest)
        if head is None:
            return None
        rest = rest[head.end():]
        if head.group("name") == REST_OF_LINE:
            value, rest = rest, ""
        else:
            token = TOKEN.match(rest)
            if token is None:
                return None
            value, rest = token.group(0), rest[token.end():]
        found.append((head.group("name"), value))
    return found


def valid_directives(raw_scripts: dict[str, str]) -> str:
    """The directives a run may send, for the refusal message."""
    forms = []
    meaning = {"PUBLIC_IDENTIFIER": "<public identifier>", "LEAD_NAME": "<name>", "STOP_AT": "<whole number>"}
    for name, raw in sorted(raw_scripts.items()):
        given = " ".join(f"{placeholder}={meaning[placeholder]}" for placeholder in _placeholder_names(raw) if placeholder in meaning)
        forms.append(f"// mosaico run {name}" + (f" {given}" if given else ""))
    return "; ".join(forms) or "none installed"


def raw_approved_scripts() -> dict[str, str]:
    if not APPROVED_DIR.is_dir():
        return {}
    return {path.name: path.read_text(encoding="utf-8") for path in sorted(APPROVED_DIR.glob("*.js"))}


def expand_directive(script: str, raw_scripts: dict[str, str]) -> str | None:
    """The approved script a valid directive stands for, its placeholder lines set; None when the directive is not valid."""
    lines = script.replace("\r\n", "\n").strip("\n").split("\n")
    match = DIRECTIVE.match(lines[0].rstrip()) if len(lines) == 1 else None
    if match is None:
        return None
    raw = raw_scripts.get(match.group("script"))
    if raw is None:
        return None
    names = _placeholder_names(raw)
    if not names:
        return None
    given = _assignments(match.group("rest"))
    raw_lines = raw.split("\n")
    if given is None:
        return None
    if not given:
        # No value: only a script whose own placeholder lines are all values a run may use (not an empty identifier).
        leading = _leading_placeholders([line.rstrip() for line in raw_lines])
        if any(not PLACEHOLDERS[name][1].match(value) for name, value in leading):
            return None
        return raw
    # Every placeholder the script takes, in its order, exactly once; a name or a value that is not its own is refused.
    if [name for name, _ in given] != names or "NOOP" in names:
        return None
    literals: list[str] = []
    for placeholder, value in given:
        quoted = len(value) >= 2 and value[0] == value[-1] == '"'
        bare = value[1:-1] if quoted else value
        if placeholder == "PUBLIC_IDENTIFIER":
            if not IDENTIFIER.match(bare):
                return None
        elif placeholder == "LEAD_NAME":
            if not LEAD_NAME_VALUE.match(bare) or bare != bare.strip():
                return None
        elif not PLACEHOLDERS[placeholder][1].match(value):
            return None
        literals.append(f'"{bare}"' if placeholder in ("PUBLIC_IDENTIFIER", "LEAD_NAME") else value)
    head = [f"const {placeholder} = {literal};" for (placeholder, _), literal in zip(given, literals)]
    return "\n".join([*head, *raw_lines[len(names):]])


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
