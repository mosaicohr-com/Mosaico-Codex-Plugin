#!/usr/bin/env python3
"""Every approved browser script carries the same text normalisation, and the rule behaves as specified.

The rule (mirrored by the Mosaico application, which recomputes the integrity digest over normalised text):
  1. Unicode NFC.
  2. Every space separator (U+00A0, U+1680, U+2000-U+200A, U+202F, U+205F, U+3000) becomes a plain space.
  3. Zero-width characters (U+200B-U+200D, U+2060, U+FEFF) are removed.
  4. CRLF and CR become LF.
  5. Every other C0 or C1 control character (U+0000-U+001F, U+007F-U+009F) except LF and TAB is removed.
  6. Each run of plain spaces becomes one space.
  7. Spaces and tabs at the end of each line are removed.
URNs, URLs, identifiers and timestamps are never passed through it.

The JavaScript is run under node when it is installed; a Python mirror of the same rule is always checked against the same cases
and against the script source.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BROWSER = ROOT / "plugins" / "mosaico-claude" / "browser"
SCRIPTS = sorted(BROWSER.glob("*.js"))
HELPER = re.compile(r"^const normalizeText = .*$", re.MULTILINE)

SPACES = "\u00a0\u1680" + "".join(chr(c) for c in range(0x2000, 0x200B)) + "\u202f\u205f\u3000"
ZERO_WIDTH = "\u200b\u200c\u200d\u2060\ufeff"


def check(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL: {message}")


def mirror(text: str) -> str:
    """The same rule in Python: what the application implements."""
    text = unicodedata.normalize("NFC", text)
    text = re.sub("[" + SPACES + "]", " ", text)
    text = re.sub("[" + ZERO_WIDTH + "]", "", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub("[\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f-\u009f]", "", text)
    text = re.sub(" {2,}", " ", text)
    return re.sub(r"[ \t]+(?=\n|\Z)", "", text)


CASES = [
    ("a\u00a0b", "a b"),  # NBSP
    ("a\u200bb\u200c\u200d\u2060\ufeffc", "abc"),  # zero-width
    ("one\r\ntwo\rthree\nfour", "one\ntwo\nthree\nfour"),  # CRLF, CR
    ("a\u2009b\u202fc\u205fd\u3000e\u2003f\u1680g", "a b c d e f g"),  # thin, narrow no-break, medium math, ideographic, em, ogham
    ("a   b \u00a0 \u00a0c", "a b c"),  # runs collapse, also across NBSP
    ("end   \t \nnext \t", "end\nnext"),  # line ends trimmed (spaces and tabs)
    ("a\u0001b\u0000c\u0085d\u009fe\u007ff\u000bg\u000ch", "abcdefgh"),  # C0 and C1 removed
    ("keep\ttab\nand newline", "keep\ttab\nand newline"),  # TAB and LF kept
    ("e\u0301", "\u00e9"),  # NFC
    ("emoji \U0001f600 and \"quotes\" \\ ok", "emoji \U0001f600 and \"quotes\" \\ ok"),
    ("a\u200b b", "a b"),  # zero-width removed before runs collapse
    ("", ""),
]
UNTOUCHED = [
    "urn:li:fsd_profile:ACoAAB1234_-x",
    "urn:li:msg_conversation:(urn:li:fsd_profile:OWNERID1,2-ABC==)",
    "https://www.linkedin.com/in/jane-doe/?a=1&b=2",
    "2026-10-06T08:15:30.000Z",
    "jane-doe_42",
]

NODE_HARNESS = r"""
const fs = require('fs');
const cases = JSON.parse(fs.readFileSync(0, 'utf8'));
const out = {};
for (const file of process.argv.slice(1)) {
  const line = fs.readFileSync(file, 'utf8').split('\n').find((l) => l.startsWith('const normalizeText = '));
  const normalizeText = new Function(line.replace('const normalizeText = ', 'return ').replace(/;$/, ''))();
  out[file] = cases.map((c) => normalizeText(c));
}
console.log(JSON.stringify(out));
"""


def main() -> None:
    check(len(SCRIPTS) == 5, "expected the five approved browser scripts")
    lines = []
    for script in SCRIPTS:
        source = script.read_text(encoding="utf-8")
        found = HELPER.findall(source)
        check(len(found) == 1, f"{script.name} does not define normalizeText exactly once")
        lines.append(found[0])
        check("Text normalisation (0.8.5" in source and "NFC" in source and "zero-width" in source and "CRLF" in source and "digest is computed after normalisation" in source,
              f"{script.name} header does not state the normalisation rule")
        check(source.index("const normalizeText") < source.index("const payload"), f"{script.name} defines normalizeText after the payload")
    check(len(set(lines)) == 1, "the five scripts do not carry the same normalizeText")
    rule = lines[0]
    for needle in ('normalize("NFC")', '\\u00A0', '\\u2000-\\u200A', '\\u202F', '\\u205F', '\\u3000', '\\u200B-\\u200D', '\\u2060', '\\uFEFF', '\\r\\n?', '\\u007F-\\u009F'):
        check(needle in rule, f"the rule is missing {needle}")

    # The Python mirror agrees with the cases.
    for given, wanted in CASES:
        check(mirror(given) == wanted, f"mirror: {given!r} -> {mirror(given)!r}, wanted {wanted!r}")
        check(mirror(mirror(given)) == wanted, f"mirror not idempotent on {given!r}")
    for value in UNTOUCHED:
        check(mirror(value) == value, f"mirror changed {value!r}")
    # Every space separator in the spec is replaced, whatever the platform's Unicode tables say.
    for char in SPACES:
        check(mirror(f"a{char}b") == "a b", f"mirror: U+{ord(char):04X} not replaced")

    # The scripts' own rule agrees with the mirror, under node.
    node = shutil.which("node")
    if node is None:
        print("SKIP: node is not installed, so the JavaScript rule was checked by source only.")
    else:
        inputs = [given for given, _ in CASES] + UNTOUCHED + [f"a{char}b" for char in SPACES]
        done = subprocess.run([node, "-e", NODE_HARNESS, *map(str, SCRIPTS)], input=json.dumps(inputs), capture_output=True, text=True, encoding="utf-8", check=False)
        check(done.returncode == 0, f"node failed: {done.stderr[-300:]}")
        results = json.loads(done.stdout)
        for script, produced in results.items():
            for given, got in zip(inputs, produced):
                check(got == mirror(given), f"{Path(script).name}: {given!r} -> {got!r}, the mirror says {mirror(given)!r}")
            check(produced[len(CASES):len(CASES) + len(UNTOUCHED)] == UNTOUCHED, f"{Path(script).name} changed a URN, URL, identifier or timestamp")

    # Where it is applied: message text only; identifiers, URNs and timestamps are never normalised.
    for script in SCRIPTS:
        uses = re.findall(r"normalizeText\(([^)]*)\)", script.read_text(encoding="utf-8").split("\n", 1)[1].replace(HELPER.findall(script.read_text(encoding="utf-8"))[0], ""))
        if script.name == "linkedin-thread-messages.js":
            check(any("m.body.text" in use for use in uses), "the thread script does not normalise message text")
            # Message text, the profile's and the participants' names (search keywords and displayName), the Lead's own name (0.9.2)
            # and the name rule's own parameter (foldName): nothing else.
            check(all(("m.body.text" in use or "firstName" in use or "[" in use or use in ("LEAD_NAME", "s")) for use in uses), f"thread script normalises an unexpected value: {uses}")
        else:
            check(uses == [], f"{script.name} normalises a value although it returns no free text: {uses}")
    print("PASS: all five approved scripts carry one normalisation rule, it matches the Python mirror on NBSP, zero-width, CRLF, thin space and control characters, and URNs, URLs and timestamps are untouched.")


if __name__ == "__main__":
    main()
