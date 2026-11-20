"""Chapter 2, step 2: each user's Sandbox has their name, and is found again by it.

    uv run checks/ch2_2_name.py [user]

The script:

    $ uv run vibecode.py reset alice
    $ uv run vibecode.py chat alice      # "new alice sb-…"
    >                                    # an empty line leaves; the Sandbox stays up
    $ uv run vibecode.py chat alice      # "running alice sb-…": the same Sandbox, found by name
    $ uv run vibecode.py chat bob        # another user, another Sandbox
    $ uv run vibecode.py reset alice     # ends hers

Done when a second chat finds the same Sandbox, another user gets one of their own, and reset ends it.
"""

import stage
from stage import USER

stage.run("reset")
first = stage.run("chat")
sandbox = stage.sandbox_of()
second = stage.run("chat")
other = f"{USER}-2"
stage.run("reset", other)
third = stage.run("chat", other)
stage.run("reset", other)
stage.run("reset")

stage.expect("chat started a Sandbox with the user's name", f"new {USER} sb-" in first and sandbox is not None)
stage.expect("a second chat found the same Sandbox by name", f"running {USER} {sandbox.object_id}" in second)
stage.expect("another user got a Sandbox of their own", f"new {other} sb-" in third and sandbox.object_id not in third)
stage.expect("reset ended it", stage.sandbox_of() is None)
stage.done()
