"""Chapter 2: each user has the template app in a browser tab.

    uv run checks/ch2_serve.py [user]

The script:

    $ uv run vibecode.py reset alice
    $ uv run vibecode.py chat alice      # "new alice sb-…", then a link: open it, the template is there
    >                                    # an empty line leaves; the Sandbox stays up
    $ uv run vibecode.py chat alice      # "running alice sb-…": the same Sandbox, found by name
    $ uv run vibecode.py chat bob        # another user, another Sandbox

Close the tab and 30 s later the Sandbox ends. Nothing is kept yet: the next chat starts from the
template.

Done when the link serves the template, only with its token, and a second chat finds the same Sandbox.
"""

import time

import stage
from stage import USER

stage.run("reset")
first = stage.run("chat")
sandbox = stage.sandbox_of()

access = sandbox.create_connect_token()
asked = time.time()
with_token = stage.visit(access.url, access.token)
waited = time.time() - asked
without = stage.visit(access.url)
stage.note(
    "the link, with its token   ",
    with_token[0],
    f"after {waited:.1f} s",
    "the page names /src/main.jsx:",
    "/src/main.jsx" in with_token[1],
)
stage.note("the link, without the token", without[0], "\n")

second = stage.run("chat")
other = f"{USER}-2"
stage.run("reset", other)
third = stage.run("chat", other)
stage.run("reset", other)

stage.expect("chat started a Sandbox and printed a link", f"new {USER} sb-" in first and "open https://" in first)
stage.expect("the link serves the template app", with_token[0] == 200 and "/src/main.jsx" in with_token[1])
stage.expect("without the token the link is refused", without[0] in (401, 403))
stage.expect("a second chat found the same Sandbox by name", f"running {USER} {sandbox.object_id}" in second)
stage.expect("another user got a Sandbox of their own", f"new {other} sb-" in third and sandbox.object_id not in third)
stage.done()
