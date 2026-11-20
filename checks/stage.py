"""What every chapter's check shares.

A check is its chapter's script, in the theater sense: the commands to type, in order, and what
should be seen after each. It runs them against Modal, prints them with their output, and ends
with one line per goal of the chapter: `ok` or `FAIL`.

It calls the commands of code/vibecode.py in this process and stands in for the keyboard. Connect
tokens are live credentials, so they are masked in everything printed.
"""

import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))

USER = (sys.argv[1:] or ["check"])[0]  # the user a check plays, unless one is named
failed = []


class Masked:
    """stdout for a check: whole lines, without colour codes or connect tokens. It keeps what it printed."""

    def __init__(self):
        self.line = ""
        self.text = ""

    def write(self, text):
        *lines, self.line = (self.line + text).split("\n")
        for line in lines:
            line = re.sub(r"\x1b\[[0-9;]*m", "", line)
            line = re.sub(r"(_modal_connect_token=)\S+", r"\1<token>", line)
            self.text += line + "\n"
            sys.__stdout__.write(line + "\n")
        sys.__stdout__.flush()

    def flush(self):
        sys.__stdout__.flush()


sys.stdout = Masked()


def run(command, user=USER, typed=(), tab_open=False):
    """One command of the application, as typed at a terminal. `typed` is what the user types at its prompt.

    With `tab_open` the check stands in for the browser tab the user opens on the link: something
    keeps the Sandbox busy for two minutes, so the idle clock does not end it under the check.
    Returns what the command printed.
    """
    import vibecode

    before = len(sys.stdout.text)
    print(f"$ uv run vibecode.py {command} {user}")
    typed = iter(typed)

    def keyboard():
        nonlocal tab_open
        if tab_open:
            vibecode.running(user).exec("sleep", "120")
            tab_open = False
        line = next(typed, "")
        print(">", line)
        return line

    vibecode.ask = keyboard
    getattr(vibecode, command)(user)
    print()
    return sys.stdout.text[before:]


def turns_ended_well(said):
    """How many turns of the agent ended with exit code 0, in what a chat printed."""
    return len(re.findall(r"^(?:done|turn \d+) \d+s$", said, re.M))


def note(*what):
    """Something the check looked at, in the transcript."""
    print("     ", *what)


def expect(goal, ok):
    """One goal of the chapter: met or not."""
    print("ok   " if ok else "FAIL ", goal)
    if not ok:
        failed.append(goal)


def done():
    """The last line of a check: the process fails when a goal did."""
    sys.exit(f"{len(failed)} goal(s) not met" if failed else 0)


def sandbox_of(user=USER):
    """The user's running Sandbox, or None."""
    import vibecode

    return vibecode.running(user)


def inside(user, *command):
    """Run a command in the user's Sandbox: its exit code and what it printed.

    A Sandbox that went idle since the last command is booted again first.
    """
    import vibecode

    process = (sandbox_of(user) or vibecode.boot(user)).exec(*command)
    output = process.stdout.read()
    return process.wait(), output.strip()


def in_project(user, phrase):
    """Whether a file under the app's src/ contains the phrase."""
    return inside(user, "grep", "-rqF", phrase, "/project/app/src")[0] == 0


def visit(url, token=None):
    """One GET: the status, and the body."""
    request = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"} if token else {})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return response.status, response.read().decode()
    except urllib.error.HTTPError as error:
        return error.code, ""
