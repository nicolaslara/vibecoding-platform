"""Record checks/outputs/vibecode.txt: a scripted session of one user, from the template.

    uv run checks/record.py [user] > checks/outputs/vibecode.txt

The user (alice unless named) is reset first.
It calls the commands of code/vibecode.py in this process and stands in for the keyboard: each prompt is
typed for the user, and after each turn a `tab:` line says what the browser tab would show. Colour codes are
left out of the recording and connect tokens are masked. The sleep outlasts idle_timeout with no tab open, so the
last chat wakes a new Sandbox.
"""

import re
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))
import vibecode  # noqa: E402

USER = (sys.argv[1:] or ["alice"])[0]
SESSION = [
    ("chat", ["A landing page for a bakery called Crumb: hero, three products, opening hours.",
              "Make it dark mode with a warm accent colour."]),
    ("undo", []),
    ("sleep", 45),
    ("chat", ["Add a newsletter signup box under the hero."]),
]  # fmt: skip


def tab(user):
    """What the tab shows: the stylesheet the dev server serves, fetched through a connect token."""
    time.sleep(2)  # hot reload
    cred = vibecode.running(user).create_connect_token()
    url = f"{cred.url}/src/App.css?direct"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {cred.token}"})
    try:
        css = urllib.request.urlopen(req, timeout=10).read().decode()
    except OSError as e:  # the agent may keep its styles elsewhere
        return f"no src/App.css ({e})"
    bg = re.search(r"background[^:]*:\s*([^;]+)", css)
    return f"{len(css.splitlines())} lines of css, background {bg[1] if bg else 'none'}"


def keyboard(prompts):
    """Stands in for vibecode.ask: types the next prompt, after saying what the last turn left in the tab."""
    prompts = iter(prompts)
    turns = 0

    def ask():
        nonlocal turns
        if turns:
            print("tab:", tab(USER))
        turns += 1
        msg = next(prompts, "")
        print(">", msg)
        return msg

    return ask


class Recording:
    """stdout for the recording: whole lines, without colour codes."""

    def __init__(self):
        self.line = ""

    def write(self, text):
        *lines, self.line = (self.line + text).split("\n")
        for line in lines:
            line = re.sub(r"\x1b\[[0-9;]*m", "", line)
            line = re.sub(r"(_modal_connect_token=)\S+", r"\1<token>", line)  # a live credential
            sys.__stdout__.write(line + "\n")

    def flush(self):
        sys.__stdout__.flush()


if __name__ == "__main__":
    t = time.time()
    sys.stdout = Recording()
    vibecode.reset(USER)
    for cmd, arg in SESSION:
        if cmd == "sleep":
            print(f"$ sleep {arg}   # the tab is closed, nothing runs\n")
            time.sleep(arg)
            continue
        print(f"$ uv run vibecode.py {cmd} {USER}")
        if cmd == "chat":
            vibecode.ask = keyboard(arg)
            vibecode.chat(USER)
        else:
            vibecode.undo(USER)
            print("tab:", tab(USER), "\n")
    print(f"recorded {USER} in {time.time() - t:.0f} s", file=sys.stderr)
