"""A vibecoding app on Modal Sandboxes: one Sandbox per user, with a coding agent inside.

    uv run vibecode.py chat alice    # starts alice's Sandbox, then type one message per line
    uv run vibecode.py reset alice   # end alice's Sandbox

Each user gets a Sandbox named after them, and chat runs a command in it. The Sandbox ends when
nobody uses it, and the next command starts a new one.
"""

import os
import sys

import modal

APP = "vibecode"  # every user's Sandbox lives in this App

# The Model Endpoint the agent calls, by its host name: its URL without the https://.
#   $ export ENDPOINT_URL=$(modal endpoint info kimi-k3 --json | jq -r .service_url)
MODEL = os.environ["ENDPOINT_URL"].removeprefix("https://")


def running(user):
    """The user's Sandbox, or None when it is not up."""
    try:
        sandbox = modal.Sandbox.from_name(APP, user)
    except modal.exception.NotFoundError:
        return None
    return sandbox if sandbox.poll() is None else None


def boot(user):
    """The user's Sandbox: the one that is running, or a new one."""
    sandbox = running(user)
    if sandbox:
        print("running", user, sandbox.object_id)
        return sandbox

    app = modal.App.lookup(APP, create_if_missing=True)
    sandbox = modal.Sandbox.create(
        app=app,
        name=user,
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


def reset(user):
    """End the user's Sandbox: the next chat starts a new one."""
    sandbox = running(user)
    if sandbox:
        sandbox.terminate(wait=True)


if __name__ == "__main__":
    commands = {"chat": chat, "reset": reset}
    if len(sys.argv) < 3 or sys.argv[1] not in commands:
        sys.exit(f"usage: vibecode.py {'|'.join(commands)} <user>")
    try:
        commands[sys.argv[1]](*sys.argv[2:])
    except KeyboardInterrupt:
        print("\nleft")
