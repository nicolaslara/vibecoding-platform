"""Chapter 2, step 1: a Sandbox on Modal, and a command run in it.

    uv run checks/ch2_1_sandbox.py [user]

The script:

    $ uv run vibecode.py chat alice      # "new alice sb-…", then "hello from a Sandbox"
    >                                    # an empty line leaves
    $ modal container list               # the Sandbox is there, and gone 30 s after its last command

Done when chat starts a Sandbox, a command answers from inside it, and the Sandbox ends once nothing uses it.
"""

import time

import stage
import vibecode
from stage import USER

started = []  # a Sandbox has no name at this step: the check keeps the one that chat boots
boot = vibecode.boot
vibecode.boot = lambda user: started.append(boot(user)) or started[-1]

said = stage.run("chat")
sandbox, left = started[0], time.time()
while sandbox.poll() is None and time.time() - left < 90:
    time.sleep(2)
stage.note("the Sandbox ended", f"{time.time() - left:.0f} s after its last command", "\n")

stage.expect("chat started a Sandbox", f"new {USER} sb-" in said)
stage.expect("a command answered from inside it", "hello from a Sandbox" in said)
stage.expect("the Sandbox ended once nothing used it", sandbox.poll() is not None)
stage.done()
