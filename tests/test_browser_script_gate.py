#!/usr/bin/env python3
"""The browser-script gate allows only the approved capture scripts to touch LinkedIn or a credential store."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import unicodedata
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
COLLEAGUE = (BROWSER / "linkedin-salesnav-colleague-connection.js").read_text(encoding="utf-8")
TOOL = "mcp__Claude_Browser__javascript_tool"
CHROME_TOOL = "mcp__claude-in-chrome__javascript_tool"


def call(tool_name: str, tool_input: object) -> tuple[bool, str]:
    return gate.decide({"tool_name": tool_name, "tool_input": tool_input})


def substituted(script: str, value: str) -> str:
    first, rest = script.split("\n", 1)
    name = first.split(" ")[1]
    return f"const {name} = {value};\n{rest}"


def named(script: str, value: str) -> str:
    """`script` with its second line (the Lead's name placeholder) set to `value`."""
    lines = script.split("\n")
    assert lines[1].startswith("const LEAD_NAME = "), "the second line is not the LEAD_NAME placeholder"
    lines[1] = f"const LEAD_NAME = {value};"
    return "\n".join(lines)


def check(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL: {message}")


def edited(script: str, old: str, new: str) -> str:
    """`script` with `old` replaced by `new`; fails when `old` is absent, so an edit check can never pass vacuously."""
    check(old in script, f"the text {old!r} is no longer in the script, so this edit check would prove nothing")
    return script.replace(old, new)


def non_ascii_values() -> None:
    """Public identifiers and names with accents, other scripts and apostrophes pass; anything that could change the script's meaning does not."""
    NFD = unicodedata.normalize("NFD", "jos\u00e9-garc\u00eda-1a2b3c")
    identifiers = ("jos\u00e9-garc\u00eda-1a2b3c", NFD, "s\u00f8ren-\u00e5s", "zo\u00eb-o-brien", "\u738b\u5c0f\u660e-123", "\u0430\u043d\u043d\u0430-\u043f\u0435\u0442\u0440\u043e\u0432\u0430",
                   "\u0e2a\u0e21\u0e0a\u0e32\u0e22", "ACoAAB1x_y-Z", "jane.doe_42", "Jane-Doe%C3%A9")
    check(NFD != "jos\u00e9-garc\u00eda-1a2b3c" and any(unicodedata.category(c) == "Mn" for c in NFD), "the decomposed accent test value holds no combining mark")
    names = ("Zo\u00eb O'Brien", "S\u00f8ren \u00c5s", "Ren\u00e9e Dupr\u00e9 - Coach, MBA", "\u738b\u5c0f\u660e", "\u674e \u96f7", "Jos\u00e9 Garc\u00eda Jr.", "Mar\u00eda O\u2019Neil",
             unicodedata.normalize("NFD", "Zo\u00eb"), "Lauren Ross", "A" * 120)
    check(gate.valid_identifier("a") and not gate.valid_identifier("") and not gate.valid_identifier("a" * 121), "identifier length bounds are not 1 to 120")
    check(gate.valid_name("", minimum=0) and not gate.valid_name("", minimum=1) and not gate.valid_name("a" * 121, minimum=1), "name length bounds are not 0 or 1 to 120")

    def run_directive(identifier: str, name: str | None, script: str, tool: str = TOOL) -> tuple[bool, str, object]:
        line = f"// mosaico run {'linkedin-thread-messages.js' if name is not None else 'linkedin-connection-evidence.js'} PUBLIC_IDENTIFIER={identifier}"
        line += f" LEAD_NAME={name}" if name is not None else ""
        return gate.evaluate({"tool_name": tool, "tool_input": {"text": line}})

    # Accepted, in both forms. The expanded script is the approved file with only the value lines changed, as plain text.
    for identifier in identifiers:
        for label, script in (("evidence", EVIDENCE), ("thread", THREAD), ("sent", SENT)):
            check(call(TOOL, {"text": substituted(script, f'"{identifier}"')})[0], f"{label} script with identifier {identifier!r} refused")
        allowed, reason, updated = run_directive(identifier, None, EVIDENCE)
        check(allowed and updated == {"text": substituted(EVIDENCE, f'"{identifier}"')}, f"directive with identifier {identifier!r} was not expanded to the approved script")
        check(updated["text"].split("\n")[1:] == EVIDENCE.split("\n")[1:], "the expanded evidence script differs from the approved file below its first line")
    for name in names:
        for identifier in ("jos\u00e9-garc\u00eda-1a2b3c", "ACoAAB1x_y-Z"):
            check(call(TOOL, {"text": named(substituted(THREAD, f'"{identifier}"'), f'"{name}"')})[0], f"thread script with name {name!r} refused")
            allowed, reason, updated = run_directive(identifier, name, THREAD)
            expected = named(substituted(THREAD, f'"{identifier}"'), f'"{name}"')
            check(allowed and updated == {"text": expected}, f"directive with name {name!r} was not expanded to the approved script")
            check(updated["text"].split("\n")[2:] == THREAD.split("\n")[2:], "the expanded thread script differs from the approved file below its second line")
            check(len(updated["text"].split("\n")) == len(THREAD.split("\n")), "the expanded thread script has another number of lines")
    # Inside a batch, on the other browser's tool.
    allowed, reason, updated = gate.evaluate({"tool_name": "mcp__claude-in-chrome__browser_batch", "tool_input": {"actions": [
        {"name": "navigate", "input": {"url": "https://example.com"}},
        {"name": "javascript_tool", "input": {"text": "// mosaico run linkedin-thread-messages.js PUBLIC_IDENTIFIER=jos\u00e9-garc\u00eda LEAD_NAME=Zo\u00eb O'Brien"}}]}})
    check(allowed and updated["actions"][1]["input"]["text"] == named(substituted(THREAD, '"jos\u00e9-garc\u00eda"'), '"Zo\u00eb O\'Brien"') and updated["actions"][0] == {"name": "navigate", "input": {"url": "https://example.com"}},
          "a batch directive with non-ASCII values was not expanded in place")

    # Refused: each of these could end the string literal, start code, hide text or change what is read.
    bad = {
        "a quote": 'jose"x', "a backslash": "jose\\x", "a newline": "jose\nx", "a carriage return": "jose\rx", "a tab": "jose\tx", "NUL": "jose\x00x",
        "a zero-width space": "jose\u200bx", "a zero-width joiner": "jose\u200dx", "a word joiner": "jose\u2060x", "a byte-order mark": "jose\ufeffx",
        "a right-to-left override": "jose\u202ex", "a left-to-right isolate": "jose\u2066x", "a line separator": "jose\u2028x",
        "a grapheme joiner": "jose\u034fx", "a variation selector": "jose\ufe0fx", "a Hangul filler": "jose\u3164x",
        "a lone surrogate": "jose\ud800x", "a private-use character": "jose\ue000x", "a non-breaking space": "jose\u00a0x", "a space": "jose x",
        "${}": "${x}", "a template": "a${document.title}b", "a backtick": "jose`x", "a dollar": "jose$x", "a semicolon": "jose;x", "a brace": "jose{x", "a parenthesis": "jose(x",
        "an angle bracket": "jose<x", "a slash": "jose/x", "a bare percent": "jose%x", "a short percent": "jose%C", "a non-hex percent": "jose%GZ", "an apostrophe": "jose'x", "an emoji": "jose\U0001f600x",
        "an injected call": 'x"; fetch("https://example.com"); "', "a comment": "x//y", "an equals sign": "x=y", "empty": "", "over-long": "a" * 121,
    }
    for label, identifier in bad.items():
        for script_name, script in (("evidence", EVIDENCE), ("thread", THREAD)):
            check(not call(TOOL, {"text": substituted(script, f'"{identifier}"')})[0], f"{script_name} script passed with an identifier holding {label}")
        if "\n" not in identifier and "\r" not in identifier and identifier != "" and " " not in identifier:
            allowed, reason, updated = run_directive(identifier, None, EVIDENCE)
            check(not allowed and updated is None, f"directive passed with an identifier holding {label}")
    bad_names = {k: v for k, v in bad.items() if k not in ("a space", "an apostrophe", "a non-breaking space") and not k.startswith("over")}
    bad_names.update({"a dollar-brace": "Zo\u00eb ${1}", "a quote after an accent": 'Zo\u00eb"', "a slash": "Zo\u00eb/Ross", "a pipe": "Zo\u00eb | Coach", "empty": "x" * 121})
    for label, name in bad_names.items():
        check(not call(TOOL, {"text": named(substituted(THREAD, '"jose"'), f'"{name}"')})[0], f"thread script passed with a name holding {label}")
        if "\n" not in name and "\r" not in name and name != "":
            allowed, reason, updated = run_directive("jose", name, THREAD)
            check(not allowed and updated is None, f"directive passed with a name holding {label}")
    allowed, _, _ = run_directive("jose", " Zo\u00eb", THREAD)
    check(not allowed, "directive passed with a name that starts with a space")
    allowed, _, updated = run_directive("jose", "Zo\u00eb ", THREAD)  # the line's trailing space is dropped before the name is read
    check(allowed and updated["text"].split("\n")[1] == 'const LEAD_NAME = "Zo\u00eb";', "a trailing space was kept in the name")
    # The refusal never echoes the submitted value.
    allowed, reason, _ = run_directive('x"\u200b\u00e9', None, EVIDENCE)
    check(not allowed and "\u00e9" not in reason and "\u200b" not in reason, "the refusal echoed the submitted identifier")

    # The hook itself, as Claude Desktop runs it: UTF-8 bytes on stdin whatever the locale, and the answer decodes to the same text.
    for label, env in (("C locale", {"PATH": "/usr/bin:/bin", "LC_ALL": "C", "PYTHONCOERCECLOCALE": "0", "PYTHONUTF8": "0"}),
                       ("Latin-1 locale", {"PATH": "/usr/bin:/bin", "LC_ALL": "en_US.ISO8859-1", "PYTHONCOERCECLOCALE": "0", "PYTHONUTF8": "0", "PYTHONIOENCODING": "latin-1"}),
                       ("UTF-8 locale", {"PATH": "/usr/bin:/bin", "LC_ALL": "en_US.UTF-8"})):
        text = "// mosaico run linkedin-thread-messages.js PUBLIC_IDENTIFIER=jos\u00e9-garc\u00eda-1a2b3c LEAD_NAME=Zo\u00eb O'Brien \u738b\u5c0f\u660e"
        run = subprocess.run([sys.executable, str(GATE)], input=json.dumps({"tool_name": TOOL, "tool_input": {"action": "javascript_exec", "text": text, "tabId": 3}}, ensure_ascii=False).encode("utf-8"),
                             capture_output=True, env=env, check=False)
        check(run.returncode == 0, f"hook refused a UTF-8 identifier and name under the {label}: {run.stderr!r}")
        check(run.stdout.isascii(), f"hook printed non-ASCII bytes under the {label}")
        out = json.loads(run.stdout.decode("utf-8"))["hookSpecificOutput"]
        check(out["updatedInput"] == {"action": "javascript_exec", "tabId": 3, "text": named(substituted(THREAD, '"jos\u00e9-garc\u00eda-1a2b3c"'), '"Zo\u00eb O\'Brien \u738b\u5c0f\u660e"')},
              f"the script the hook returned is not the approved script with only the two values changed, under the {label}")
        word = subprocess.run([sys.executable, str(GATE)], input=json.dumps({"tool_name": TOOL, "tool_input": {"text": named(substituted(THREAD, '"jos\u00e9-garc\u00eda"'), '"S\u00f8ren"')}}, ensure_ascii=False).encode("utf-8"),
                              capture_output=True, env=env, check=False)
        check(word.returncode == 0 and word.stdout == b"", f"hook refused the approved script word for word with accented values under the {label}: {word.stderr!r}")
        refused = subprocess.run([sys.executable, str(GATE)], input=json.dumps({"tool_name": TOOL, "tool_input": {"text": substituted(THREAD, '"jos\u00e9\u200b"')}}, ensure_ascii=False).encode("utf-8"),
                                 capture_output=True, env=env, check=False)
        check(refused.returncode == 2 and refused.stdout == b"" and "\u200b".encode("utf-8") not in refused.stderr, f"hook did not refuse a zero-width character cleanly under the {label}")
    garbled = subprocess.run([sys.executable, str(GATE)], input=b'{"tool_name": "x", "tool_input": {"text": "jos\xe9"}}', capture_output=True, check=False)
    check(garbled.returncode == 2, "hook did not refuse input that is not valid UTF-8")


def colleague_values() -> None:
    """0.9.4: the Sales Navigator colleague-connection script takes two identifiers, each checked like any public identifier."""

    def with_values(candidate: str, colleague: str, script: str = COLLEAGUE) -> str:
        lines = script.split("\n")
        assert lines[0].startswith("const PUBLIC_IDENTIFIER = ") and lines[1].startswith("const COLLEAGUE_IDENTIFIER = "), "the first two lines are not the two placeholders"
        lines[0], lines[1] = f"const PUBLIC_IDENTIFIER = {candidate};", f"const COLLEAGUE_IDENTIFIER = {colleague};"
        return "\n".join(lines)

    def directive(candidate: str, colleague: str) -> str:
        return f"// mosaico run linkedin-salesnav-colleague-connection.js PUBLIC_IDENTIFIER={candidate} COLLEAGUE_IDENTIFIER={colleague}"

    def expand(text: str, tool: str = TOOL) -> tuple[bool, str, object]:
        return gate.evaluate({"tool_name": tool, "tool_input": {"action": "javascript_exec", "text": text, "tabId": 5}})

    check(COLLEAGUE.split("\n")[0] == 'const PUBLIC_IDENTIFIER = "";' and COLLEAGUE.split("\n")[1] == 'const COLLEAGUE_IDENTIFIER = "";', "colleague script's first two lines changed")
    check("linkedin-salesnav-colleague-connection.js" in gate.approved_scripts(), "the gate does not enumerate the colleague-connection script")
    check(gate.valid_directives(gate.raw_approved_scripts()).count("COLLEAGUE_IDENTIFIER=<colleague identifier>") == 1
          and "// mosaico run linkedin-salesnav-colleague-connection.js PUBLIC_IDENTIFIER=<public identifier> COLLEAGUE_IDENTIFIER=<colleague identifier>" in gate.valid_directives(gate.raw_approved_scripts()),
          "the refusal text does not name the colleague-connection directive")
    pairs = (("jane-doe", "ewa-betkier"), ("ACoAAB1x_y-Z", "ewa-b"), ("josé-garcía-1a2b3c", "王小明-123"), ("Jane-Doe%C3%A9", "ewa.b_1"),
             ("a", "b"), ("a" * 120, "b" * 120), (unicodedata.normalize("NFD", "zoë"), "søren-ås"))
    for candidate, colleague in pairs:
        expected = with_values(f'"{candidate}"', f'"{colleague}"')
        # Word for word, on either browser, alone or in a batch, with a trailing newline: allowed and not rewritten.
        for tool in (TOOL, CHROME_TOOL):
            check(call(tool, {"text": expected})[0] and call(tool, {"text": expected + "\n"})[0], f"colleague script with {candidate!r} and {colleague!r} refused word for word")
            allowed, _, updated = expand(expected, tool)
            check(allowed and updated is None, "a word-for-word colleague script was rewritten or refused")
        check(call("mcp__Claude_Browser__browser_batch", {"actions": [{"name": "javascript_tool", "input": {"action": "javascript_exec", "text": expected}}]})[0], "colleague script in a batch refused")
        # The directive, bare or quoted: the approved file with only the two value lines changed.
        for line in (directive(candidate, colleague), directive(f'"{candidate}"', f'"{colleague}"'), directive(candidate, colleague) + "\n"):
            for tool in (TOOL, CHROME_TOOL):
                allowed, reason, updated = expand(line, tool)
                check(allowed and reason == "" and updated == {"action": "javascript_exec", "text": expected, "tabId": 5}, f"directive with {candidate!r} and {colleague!r} was not expanded to the approved script")
                check(updated["text"].split("\n")[2:] == COLLEAGUE.split("\n")[2:] and len(updated["text"].split("\n")) == len(COLLEAGUE.split("\n")),
                      "the expanded colleague script differs from the approved file below its second line")
                check(call(tool, {"text": updated["text"]})[0], "the expanded colleague script is not itself approved")
        batch = {"actions": [{"name": "navigate", "input": {"url": "https://www.linkedin.com/sales/home"}}, {"name": "javascript_tool", "input": {"text": directive(candidate, colleague)}}]}
        allowed, _, updated = gate.evaluate({"tool_name": "mcp__claude-in-chrome__browser_batch", "tool_input": batch})
        check(allowed and updated["actions"][1]["input"]["text"] == expected and updated["actions"][0] == batch["actions"][0], "a batch colleague directive was not expanded in place")

    # Refused in either slot, in both forms: each of these could end the string literal, start code, hide text or change what is read.
    bad = {
        "a quote": 'jose"x', "a backslash": "jose\\x", "a newline": "jose\nx", "a carriage return": "jose\rx", "a tab": "jose\tx", "NUL": "jose\x00x",
        "${}": "${x}", "a template": "a${document.title}b", "a backtick": "jose`x", "a dollar": "jose$x", "a semicolon": "jose;x", "a slash": "jose/x", "a bare percent": "jose%x",
        "a zero-width space": "jose​x", "a zero-width joiner": "jose‍x", "a word joiner": "jose⁠x", "a byte-order mark": "jose﻿x",
        "a right-to-left override": "jose‮x", "a lone surrogate": "jose\ud800x", "a private-use character": "josex", "a space": "jose x", "an apostrophe": "jose'x",
        "an emoji": "jose\U0001f600x", "an injected call": 'x"; fetch("https://example.com"); "', "an equals sign": "x=y", "empty": "", "over-long": "a" * 121,
    }
    for label, value in bad.items():
        for candidate, colleague in ((value, "ewa-betkier"), ("jane-doe", value)):
            check(not call(TOOL, {"text": with_values(f'"{candidate}"', f'"{colleague}"')})[0], f"colleague script passed word for word with {label} in a value")
            if not any(c in value for c in "\n\r") and value != "" and " " not in value:
                allowed, reason, updated = expand(directive(candidate, colleague))
                check(not allowed and updated is None, f"colleague directive passed with {label} in a value")
                check(value not in reason, "the refusal echoed the submitted value")
    # The two values are not interchangeable with other placeholders, and the template (empty values) is not something a run may send.
    check(not call(TOOL, {"text": COLLEAGUE})[0], "colleague script with empty values passed")
    check(not call(TOOL, {"text": with_values("1", '"ewa"')})[0] and not call(TOOL, {"text": with_values('"jane"', "0")})[0], "colleague script with a bare number passed")
    check(not call(TOOL, {"text": with_values('"jane-doe"', '"a\\" + document.cookie + \\""')})[0], "colleague script with an unsafe colleague passed")
    lines = with_values('"jane-doe"', '"ewa"').split("\n")
    for label, changed in (
        ("lines in the other order", [lines[1], lines[0], *lines[2:]]),
        ("no second line", [lines[0], *lines[2:]]),
        ("a repeated second line", [lines[0], lines[1], lines[1], *lines[2:]]),
        ("a repeated first line", [lines[0], lines[0], *lines[1:]]),
        ("another placeholder second", [lines[0], 'const LEAD_NAME = "Jane";', *lines[2:]]),
        ("a third placeholder", [*lines[:2], 'const STOP_AT = 0;', *lines[2:]]),
        ("code on the second line", [lines[0], lines[1] + " document.title;", *lines[2:]]),
    ):
        check(not call(TOOL, {"text": "\n".join(changed)})[0], f"colleague script with {label} passed")
    # The directive must carry both placeholders, once each, in order.
    for line in (
        "// mosaico run linkedin-salesnav-colleague-connection.js",
        "// mosaico run linkedin-salesnav-colleague-connection.js PUBLIC_IDENTIFIER=jane-doe",
        "// mosaico run linkedin-salesnav-colleague-connection.js COLLEAGUE_IDENTIFIER=ewa",
        "// mosaico run linkedin-salesnav-colleague-connection.js COLLEAGUE_IDENTIFIER=ewa PUBLIC_IDENTIFIER=jane-doe",
        "// mosaico run linkedin-salesnav-colleague-connection.js PUBLIC_IDENTIFIER=jane-doe PUBLIC_IDENTIFIER=jane-doe",
        "// mosaico run linkedin-salesnav-colleague-connection.js PUBLIC_IDENTIFIER=jane-doe COLLEAGUE_IDENTIFIER=ewa COLLEAGUE_IDENTIFIER=ewa",
        "// mosaico run linkedin-salesnav-colleague-connection.js PUBLIC_IDENTIFIER=jane-doe COLLEAGUE_IDENTIFIER=ewa STOP_AT=1",
        "// mosaico run linkedin-salesnav-colleague-connection.js PUBLIC_IDENTIFIER=jane-doe COLLEAGUE_IDENTIFIER=ewa LEAD_NAME=Jane Doe",
        "// mosaico run linkedin-salesnav-colleague-connection.js PUBLIC_IDENTIFIER=jane-doe LEAD_NAME=Jane Doe",
        "// mosaico run linkedin-salesnav-colleague-connection.js PUBLIC_IDENTIFIER=jane-doe COLLEAGUE_IDENTIFIER=",
        "// mosaico run linkedin-salesnav-colleague-connection.js PUBLIC_IDENTIFIER= COLLEAGUE_IDENTIFIER=ewa",
        "// mosaico run linkedin-salesnav-colleague-connection.js PUBLIC_IDENTIFIER=jane doe COLLEAGUE_IDENTIFIER=ewa",
        "// mosaico run linkedin-salesnav-colleague-connection.js PUBLIC_IDENTIFIER=jane-doe COLLEAGUE_IDENTIFIER=ewa extra",
        "// mosaico run linkedin-salesnav-colleague-connection.js PUBLIC_IDENTIFIER=jane-doe COLLEAGUE_IDENTIFIER=ewa\nconsole.log(document.cookie)",
        "// mosaico run linkedin-salesnav-colleague-connection.js PUBLIC_IDENTIFIER=jane-doe; COLLEAGUE_IDENTIFIER=ewa",
        "// mosaico run linkedin-connection-evidence.js PUBLIC_IDENTIFIER=jane-doe COLLEAGUE_IDENTIFIER=ewa",
        "// mosaico run linkedin-thread-messages.js PUBLIC_IDENTIFIER=jane-doe COLLEAGUE_IDENTIFIER=ewa",
        "// mosaico run linkedin-sent-invitations.js PUBLIC_IDENTIFIER=jane-doe COLLEAGUE_IDENTIFIER=ewa",
        "// mosaico run linkedin-whoami.js COLLEAGUE_IDENTIFIER=ewa",
    ):
        allowed, reason, updated = expand(line)
        check(not allowed and updated is None, f"invalid colleague directive passed: {line!r}")
        check("COLLEAGUE_IDENTIFIER=<colleague identifier>" in reason and "console.log" not in reason, "the refusal does not name the colleague directive, or echoed what was sent")
    # The body is the approved text: any edit, anywhere, is refused.
    body = with_values('"jane-doe"', '"ewa"')
    for old, new in (("MAX_FILTERED_PAGES = 2", "MAX_FILTERED_PAGES = 200"), ("type:CONNECTION_OF", "type:ALL"), ("PAGE_SIZE = 25", "PAGE_SIZE = 250"), ("PAUSE_MS = 500", "PAUSE_MS = 0"),
                     ('found: state === "ok" && found', 'found: found'), ("0x01000193", "0x01000194"), ("sales-api/salesApiLeadSearch", "sales-api/other")):
        check(not call(TOOL, {"text": edited(body, old, new)})[0], f"edited colleague script passed ({old})")
    check(not call(TOOL, {"text": body + "\nconsole.log(document.cookie)"})[0], "colleague script with an appended line passed")


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
    # 0.9.2: the Lead's name is the second placeholder line, a quoted string that cannot hold a quote, a backslash or a control character.
    check(THREAD.split("\n")[1] == 'const LEAD_NAME = "";', "thread script's second line is not the LEAD_NAME placeholder")
    check(call(TOOL, {"text": named(substituted(THREAD, '"x"'), '"Lena Brook"')})[0], "thread script with a name refused")
    check(call(TOOL, {"text": named(substituted(THREAD, '"x"'), '"Ren\u00e9e Dupr\u00e9 - Coach, MBA"') + "\n"})[0], "thread script with a name holding spaces, an accent and a suffix refused")
    check(not call(TOOL, {"text": named(substituted(THREAD, '"x"'), '"a\\" + document.cookie + \\""')})[0], "thread script with an unsafe name passed")
    check(not call(TOOL, {"text": named(substituted(THREAD, '"x"'), '"a\\\\"')})[0], "thread script with a name ending in a backslash passed")
    check(not call(TOOL, {"text": named(substituted(THREAD, '"x"'), '"' + "a" * 121 + '"')})[0], "thread script with an over-long name passed")
    check(not call(TOOL, {"text": named(substituted(THREAD, '"x"'), "1")})[0], "thread script with a number as its name passed")
    check(not call(TOOL, {"text": named(substituted(THREAD, '"x"'), '"x"').replace("const LEAD_NAME", "var LEAD_NAME")})[0], "thread script with its name line changed to var passed")
    check(not call(TOOL, {"text": substituted(THREAD, '"x"').replace('const LEAD_NAME = "";\n', "")})[0], "thread script without its name line passed")
    check(not call(TOOL, {"text": edited(substituted(THREAD, '"x"'), "function namesMatch", "function namesMatch2") if "function namesMatch" in THREAD else edited(substituted(THREAD, '"x"'), "const namesMatch = ", "const namesMatch2 = ")})[0], "thread script with a renamed name rule passed")
    check(not call(TOOL, {"text": edited(substituted(THREAD, '"x"'), 'a.includes(" ") && b.startsWith(a)', 'b.startsWith(a)')})[0], "thread script with a looser name rule passed")
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
    check(not call(TOOL, {"text": EVIDENCE.split("\n", 1)[0].replace('"PUBLIC_IDENTIFIER"', '"x"') + '\nconst LEAD_NAME = "y";\n' + EVIDENCE.split("\n", 1)[1]})[0], "evidence script with an added name line passed")
    check(not call(TOOL, {"text": substituted(THREAD, '"x"').replace('const LEAD_NAME = "";\n', 'const LEAD_NAME = "";\nconst LEAD_NAME = "other";\n')})[0], "thread script with a second name line passed")
    check(not call(TOOL, {"text": substituted(THREAD, '"x"').replace('const LEAD_NAME = "";', 'const LEAD_NAME = "Jane"; document.title;')})[0], "thread script with code after its name passed")
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
    check(sorted(gate.approved_scripts()) == sorted(path.name for path in BROWSER.glob("*.js")) and len(gate.approved_scripts()) == 6, "the gate's approved scripts are not the six scripts in the browser folder")
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
        ("linkedin-thread-messages.js", "// mosaico run linkedin-thread-messages.js PUBLIC_IDENTIFIER=Jane-Doe%C3%A9 LEAD_NAME=Jane Doe",
         named(replaced(THREAD, 'const PUBLIC_IDENTIFIER = "Jane-Doe%C3%A9";'), '"Jane Doe"')),
        ("linkedin-thread-messages.js", '// mosaico run linkedin-thread-messages.js PUBLIC_IDENTIFIER="jane-doe" LEAD_NAME="Jane Doe"\n',
         named(replaced(THREAD, 'const PUBLIC_IDENTIFIER = "jane-doe";'), '"Jane Doe"')),
        ("linkedin-thread-messages.js", "// mosaico run linkedin-thread-messages.js PUBLIC_IDENTIFIER=lena-brook-1 LEAD_NAME=Lena Brook - The Money Coach, Trading Mentor",
         named(replaced(THREAD, 'const PUBLIC_IDENTIFIER = "lena-brook-1";'), '"Lena Brook - The Money Coach, Trading Mentor"')),
        ("linkedin-thread-messages.js", "// mosaico run linkedin-thread-messages.js PUBLIC_IDENTIFIER=nandika LEAD_NAME=Ren\u00e9e Dupr\u00e9 O'Neil",
         named(replaced(THREAD, 'const PUBLIC_IDENTIFIER = "nandika";'), '"Ren\u00e9e Dupr\u00e9 O\'Neil"')),
        ("linkedin-connection-evidence.js", "// mosaico run linkedin-connection-evidence.js PUBLIC_IDENTIFIER=ACoAAB1x_y-Z",
         replaced(EVIDENCE, 'const PUBLIC_IDENTIFIER = "ACoAAB1x_y-Z";')),
        ("linkedin-thread-messages.js", "// mosaico run linkedin-thread-messages.js PUBLIC_IDENTIFIER=ACoAAB1x_y-Z LEAD_NAME=Zara Hill",
         named(replaced(THREAD, 'const PUBLIC_IDENTIFIER = "ACoAAB1x_y-Z";'), '"Zara Hill"')),
        ("linkedin-sent-invitations.js", "// mosaico run linkedin-sent-invitations.js PUBLIC_IDENTIFIER=ACoAAB1x_y-Z",
         replaced(SENT, 'const PUBLIC_IDENTIFIER = "ACoAAB1x_y-Z";')),
        ("linkedin-sent-invitations.js", "// mosaico run linkedin-sent-invitations.js PUBLIC_IDENTIFIER=jane-doe",
         replaced(SENT, 'const PUBLIC_IDENTIFIER = "jane-doe";')),
        ("linkedin-salesnav-colleague-connection.js", "// mosaico run linkedin-salesnav-colleague-connection.js PUBLIC_IDENTIFIER=jane-doe COLLEAGUE_IDENTIFIER=ewa-betkier",
         replaced(replaced(COLLEAGUE, 'const PUBLIC_IDENTIFIER = "jane-doe";').replace('const COLLEAGUE_IDENTIFIER = "";', 'const COLLEAGUE_IDENTIFIER = "ewa-betkier";'), 'const PUBLIC_IDENTIFIER = "jane-doe";')),
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
    for script in (EVIDENCE, WHOAMI, substituted(THREAD, '"x"'), named(substituted(THREAD, '"x"'), '"Jane Doe"')):
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
        # 0.9.2: the thread script takes both values, in this order, and the name is a plain string.
        "// mosaico run linkedin-thread-messages.js PUBLIC_IDENTIFIER=jane-doe",
        "// mosaico run linkedin-thread-messages.js LEAD_NAME=Jane Doe",
        "// mosaico run linkedin-thread-messages.js LEAD_NAME=Jane Doe PUBLIC_IDENTIFIER=jane-doe",
        "// mosaico run linkedin-thread-messages.js PUBLIC_IDENTIFIER=jane-doe LEAD_NAME=",
        "// mosaico run linkedin-thread-messages.js PUBLIC_IDENTIFIER=jane-doe LEAD_NAME= Jane Doe",
        "// mosaico run linkedin-thread-messages.js PUBLIC_IDENTIFIER=jane-doe LEAD_NAME=Jane\" + document.cookie + \"",
        "// mosaico run linkedin-thread-messages.js PUBLIC_IDENTIFIER=jane-doe LEAD_NAME=Jane\\",
        "// mosaico run linkedin-thread-messages.js PUBLIC_IDENTIFIER=jane-doe LEAD_NAME=Jane Doe\nconsole.log(document.cookie)",
        "// mosaico run linkedin-thread-messages.js PUBLIC_IDENTIFIER=jane-doe LEAD_NAME=" + "a" * 121,
        "// mosaico run linkedin-connection-evidence.js PUBLIC_IDENTIFIER=jane-doe LEAD_NAME=Jane Doe",
        "// mosaico run linkedin-sent-invitations.js LEAD_NAME=Jane Doe",
        "// mosaico run linkedin-whoami.js LEAD_NAME=Jane Doe",
        "// mosaico run linkedin-thread-messages.js PUBLIC_IDENTIFIER=a\"+document.cookie+\"",
        "// mosaico run linkedin-thread-messages.js PUBLIC_IDENTIFIER=",
        "// mosaico run linkedin-thread-messages.js PUBLIC_IDENTIFIER=a b",
        "// mosaico run linkedin-sent-invitations.js PUBLIC_IDENTIFIER=" + "a" * 121,
        "// mosaico run linkedin-thread-messages.js PUBLIC_IDENTIFIER=x LEAD_NAME=y\nconsole.log(document.cookie)",
        "// mosaico run linkedin-thread-messages.js PUBLIC_IDENTIFIER=x; fetch('https://www.linkedin.com/voyager/api/me')",
        "// mosaico run",
        "//mosaico run linkedin-whoami.js",
    )
    for directive in invalid:
        for tool_input, tool in (({"text": directive}, TOOL),
                                 ({"actions": [{"name": "javascript_tool", "input": {"text": directive}}]}, "mcp__Claude_Browser__browser_batch")):
            allowed, reason, updated = expand(tool, tool_input)
            check(not allowed and updated is None, f"invalid directive passed: {directive!r}")
            check("// mosaico run linkedin-whoami.js" in reason and "PUBLIC_IDENTIFIER=<public identifier>" in reason and "STOP_AT=<whole number>" in reason
                  and "// mosaico run linkedin-thread-messages.js PUBLIC_IDENTIFIER=<public identifier> LEAD_NAME=<name>" in reason,
                  "the refusal does not name the valid directives")
            check("unknown" not in reason and "cookie" not in reason.replace("credential", "") and "fetch" not in reason, "the refusal echoed the submitted directive")
    # One bad directive refuses a whole batch, and a directive plus another script is judged item by item.
    mixed = {"actions": [{"name": "javascript_tool", "input": {"text": "// mosaico run linkedin-whoami.js"}},
                         {"name": "javascript_tool", "input": {"text": "document.cookie"}}]}
    check(not call("mcp__Claude_Browser__browser_batch", mixed)[0], "batch with a directive and a cookie read passed")
    # Retyped with a change is still refused.
    check(not call(TOOL, {"text": edited(substituted(THREAD, '"x"'), "MAX_MESSAGES = 98", "MAX_MESSAGES = 99")})[0], "a retyped script with one changed line passed")

    non_ascii_values()
    colleague_values()

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
    directive = subprocess.run([sys.executable, str(GATE)], input=json.dumps({"tool_name": TOOL, "tool_input": {"action": "javascript_exec", "text": "// mosaico run linkedin-thread-messages.js PUBLIC_IDENTIFIER=jane-doe LEAD_NAME=Jane Doe", "tabId": 3}}),
                               capture_output=True, text=True, env=env, check=False)
    out = json.loads(directive.stdout) if directive.returncode == 0 else {}
    specific = out.get("hookSpecificOutput", {})
    check(directive.returncode == 0 and set(out) == {"hookSpecificOutput"} and specific.get("hookEventName") == "PreToolUse"
          and specific.get("permissionDecision") == "allow"
          and specific.get("updatedInput") == {"action": "javascript_exec", "text": named(substituted(THREAD, '"jane-doe"'), '"Jane Doe"'), "tabId": 3},
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
