"""Chapter 0: Modal is set up, and the starting application runs.

    uv run checks/ch0_setup.py

The script:

    $ export MODAL_ENVIRONMENT=vibecoding-demo   # only with an Environment made for the workshop: in every terminal
    $ export MODAL_PROFILE=personal              # only with several profiles: the workspace
    $ modal token info                           # the workspace this terminal talks to
    $ echo $MODAL_ENVIRONMENT                    # that Environment, or nothing for the default one
    $ modal shell -c 'echo hello from a Sandbox' # a first Sandbox, there: Modal starts it, runs the command, ends it
    $ uv run vibecode.py chat alice              # the starting application: it repeats what is typed
    > hello

`modal shell` alone leaves you at a prompt inside the Sandbox, until `exit`. It takes what a Sandbox
takes: `--cpu 4 --memory 8192 --gpu t4`, an `--image`.

Done when the Sandbox answers from the workspace and Environment you meant to use.
"""

import subprocess
import sys

import modal

import stage

info = subprocess.run([sys.executable, "-m", "modal", "token", "info"], capture_output=True, text=True).stdout
workspace = next((line.split()[1] for line in info.splitlines() if line.startswith("Workspace:")), "")
environment = modal.config.config.get("environment") or "(the workspace default)"
print("$ modal token info")
stage.note("workspace  ", workspace or "none: run `modal setup`")
print("$ echo $MODAL_ENVIRONMENT")
stage.note("environment", environment, "\n")

print("$ modal shell -c 'echo hello from a Sandbox'")
shell = [sys.executable, "-m", "modal", "shell", "--no-pty", "-c", "echo hello from a Sandbox"]  # no terminal here
answer = subprocess.run(shell, capture_output=True, text=True).stdout.strip()
print(answer, "\n")

said = stage.run("chat", typed=["hello"])

stage.expect("the modal command is logged in to a workspace", bool(workspace))
stage.expect("the application's prompt takes a message", "> hello" in said)
stage.expect(f"a Sandbox ran in {workspace} / {environment}", answer == "hello from a Sandbox")
stage.done()
