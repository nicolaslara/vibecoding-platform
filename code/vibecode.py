"""A vibecoding app on Modal Sandboxes: one Sandbox per user, with a coding agent inside.

    uv run vibecode.py chat alice    # starts a Sandbox, then type one message per line

Each chat starts a Sandbox and runs a command in it. The Sandbox ends when nothing uses it.
"""

import os
import sys

import modal

APP = "vibecode"  # every user's Sandbox lives in this App

# The Model Endpoint the agent calls, by its host name: its URL without the https://.
#   $ export ENDPOINT_URL=$(modal endpoint info kimi-k3 --json | jq -r .service_url)
MODEL = os.environ["ENDPOINT_URL"].removeprefix("https://")


def boot(user):
    """A new Sandbox for the user."""
    app = modal.App.lookup(APP, create_if_missing=True)
    sandbox = modal.Sandbox.create(
        app=app,
        idle_timeout=30,  # it ends 30 s after the last activity
        timeout=3600,  # and after an hour at most
    )

    print("new", user, sandbox.object_id)
    return sandbox


def ask():
    """A line from the user. An empty line, EOF or Ctrl-C ends the chat."""
    try:
        return input("> ")
    except (EOFError, KeyboardInterrupt):
        print()
        return ""


def chat(user):
    """Read messages, one per line."""
    sandbox = boot(user)
    hello = sandbox.exec("echo", "hello from a Sandbox")  # a command, run inside it
    print(hello.stdout.read(), end="")

    while message := ask():
        print(f"{user} said: {message}")


if __name__ == "__main__":
    commands = {"chat": chat}
    if len(sys.argv) < 3 or sys.argv[1] not in commands:
        sys.exit(f"usage: vibecode.py {'|'.join(commands)} <user>")
    try:
        commands[sys.argv[1]](*sys.argv[2:])
    except KeyboardInterrupt:
        print("\nleft")
