"""A vibecoding app on Modal Sandboxes: one Sandbox per user, with a coding agent inside.

    uv run vibecode.py chat alice    # type one message per line

The starting point: a prompt that reads messages. Each chapter puts more of Modal behind it.
"""

import sys


def ask():
    """A line from the user. An empty line, EOF or Ctrl-C ends the chat."""
    try:
        return input("> ")
    except (EOFError, KeyboardInterrupt):
        print()
        return ""


def chat(user):
    """Read messages, one per line."""
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
