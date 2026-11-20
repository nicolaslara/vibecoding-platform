"""A vibecoding app on Modal Sandboxes: one Sandbox per user, with a coding agent inside.

    uv run vibecode.py chat alice    # open the link it prints, then type one message per line
    uv run vibecode.py reset alice   # start over from the template

Each user gets a Sandbox named after them. Its main process is the dev server of their app, and
every message runs the coding agent once, inside. A snapshot is taken before each message.
The Sandbox ends when nobody uses it, and the next command brings it back from where it ended.
"""

import os
import sys
import time
from pathlib import Path

import modal
import modal.experimental

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
            "AUTHORIZATION_BEARER": "added-outside",  # OpenCode wants a key; the real one never comes in
            "OPENCODE_DISABLE_MODELS_FETCH": "true",
        }
    )
)

# The model key never enters the Sandbox. Modal adds it outside, to requests for the model's host:
# the gateway that opencode.json calls.
MODEL_HOST = "inference.us-west.modal.direct"
key_added_outside = modal.experimental.OutboundPolicy().with_header_replacement(
    domain=MODEL_HOST,
    secret=modal.Secret.from_name("model-token"),
    headers={"Authorization": "Bearer $AUTHORIZATION_BEARER"},
)

# The app's own record. For each user: one snapshot id per message, taken before that message.
turns_of = modal.Dict.from_name("vibecode-turns", create_if_missing=True)

# One turn of the agent, as a shell command: $0 is the message.
#   -c            continue the project's chat, so the agent remembers the earlier messages
#   < /dev/null   OpenCode waits for as long as its stdin is open
#   2>&1          OpenCode prints its steps on stderr and only its last message on stdout
AGENT = 'exec opencode run --auto -c -- "$0" < /dev/null 2>&1'


def running(user):
    """The user's Sandbox, or None when it is not up."""
    try:
        sandbox = modal.Sandbox.from_name(APP, user)
    except modal.exception.NotFoundError:
        return None
    return sandbox if sandbox.poll() is None else None


def last_filesystem(user):
    """The filesystem the user's last Sandbox ended with, or the base when none was kept."""
    try:
        last = modal.Sandbox.from_name(APP, user, include_terminated=True)
        return last._experimental_get_exit_snapshot()
    except modal.Error:
        return base


def boot(user):
    """The user's Sandbox: the one that is running, or a new one from where the last one ended."""
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
        image=last_filesystem(user) if turns_of.get(user) else base,
        workdir="/project/app",
        readiness_probe=modal.Probe.with_tcp(8080),
        idle_timeout=30,  # it ends 30 s after the last activity
        timeout=3600,  # and after an hour at most
        experimental_options={"enable_exit_snapshot": True},  # its filesystem is kept when it ends
        _experimental_outbound_policy=key_added_outside,  # the model key, added on the way out
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
    """Send messages to the agent, one per line, and print what it does."""
    sandbox = boot(user)
    print("open", preview(sandbox, user))

    while message := ask():
        if sandbox.poll() is not None:  # it went idle and ended while the user was away
            sandbox = boot(user)
            print("open", preview(sandbox, user))

        turns = checkpoint(sandbox, user)  # before the message: the state as it was
        started = time.time()
        agent = sandbox.exec("sh", "-c", AGENT, message, timeout=600)  # ten minutes at most
        for chunk in agent.stdout:  # each step, as the agent takes it
            print(chunk, end="")

        if agent.wait() == 0:
            print(f"turn {len(turns)} {time.time() - started:.0f}s")
        else:
            print(f"turn {len(turns)} stopped rc={agent.returncode}")


def checkpoint(sandbox, user):
    """Snapshot the Sandbox's filesystem as a new turn and return the user's turns."""
    snapshot = sandbox.snapshot_filesystem()
    turns = turns_of.get(user, []) + [snapshot.object_id]
    turns_of[user] = turns
    return turns


def reset(user):
    """Back to the template: no Sandbox, no turns."""
    sandbox = running(user)
    if sandbox:
        sandbox.terminate(wait=True)
    turns_of.pop(user, None)


if __name__ == "__main__":
    commands = {"chat": chat, "reset": reset}
    if len(sys.argv) < 3 or sys.argv[1] not in commands:
        sys.exit(f"usage: vibecode.py {'|'.join(commands)} <user>")
    try:
        commands[sys.argv[1]](*sys.argv[2:])
    except KeyboardInterrupt:
        print("\nleft; a turn in progress finishes in the Sandbox")
