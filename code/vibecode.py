"""A vibecoding app on Modal Sandboxes: one Sandbox per user, with a coding agent inside.

    uv run vibecode.py chat alice    # open the link it prints, then type one message per line
    uv run vibecode.py reset alice   # start over from the template

Each user gets a Sandbox named after them. Its main process is the dev server of their app. The
Sandbox ends when nobody uses it, and the next command starts a new one from the template.
"""

import os
import sys
from pathlib import Path

import modal

HERE = Path(__file__).parent
APP = "vibecode"  # every user's Sandbox lives in this App

# The Model Endpoint the agent calls, by its host name: its URL without the https://.
#   $ export ENDPOINT_URL=$(modal endpoint info kimi-k3 --json | jq -r .service_url)
MODEL = os.environ["ENDPOINT_URL"].removeprefix("https://")

# What every new user starts from: a Vite template with its packages installed, and the OpenCode
# agent. MODEL is part of the Image: after changing it, `reset` the user.
base = (
    modal.Image.from_registry("node:22-slim")
    .add_local_dir(HERE / "app", "/project/app", copy=True)
    .run_commands("cd /project/app && npm ci")
    .run_commands("npm install -g opencode-ai@1.18.30")
    .add_local_file(HERE / "opencode.json", "/root/.config/opencode/opencode.json", copy=True)
    .env(
        {
            "MODEL": MODEL,  # opencode.json reads it
            "OPENCODE_DISABLE_MODELS_FETCH": "true",
        }
    )
)


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
    dev_server = ["npm", "run", "dev"]  # the Sandbox's main process
    sandbox = modal.Sandbox.create(
        *dev_server,
        app=app,
        name=user,
        image=base,
        workdir="/project/app",
        readiness_probe=modal.Probe.with_tcp(8080),
        idle_timeout=30,  # it ends 30 s after the last activity
        timeout=3600,  # and after an hour at most
    )

    sandbox.wait_until_ready()
    print("new", user, sandbox.object_id)
    return sandbox


def preview(sandbox, user):
    """The link to the user's app.

    It is the address of this one Sandbox, with a connect token in it, because no port is public.
    """
    access = sandbox.create_connect_token(user_metadata={"user": user})
    return f"{access.url}/?_modal_connect_token={access.token}"


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
    print("open", preview(sandbox, user))

    while message := ask():
        print(f"{user} said: {message}")


def reset(user):
    """Back to the template: no Sandbox."""
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
