"""Chapter 2, step 4: a link to the user's app, for their browser.

    uv run checks/ch2_4_connect.py [user]

The script:

    $ uv run vibecode.py reset alice
    $ uv run vibecode.py chat alice      # "new alice sb-…", then a link: open it, the template is there
    >

The link is the address of this one Sandbox, with a connect token in it. No port of the Sandbox is
public. The first visit waits until the dev server answers.

Done when the link serves the template, and only with its token.
"""

import time

import stage
from stage import USER

stage.run("reset")
said = stage.run("chat")
access = stage.sandbox_of().create_connect_token()

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
stage.run("reset")

stage.expect("chat started a Sandbox and printed a link", f"new {USER} sb-" in said and "open https://" in said)
stage.expect("the link serves the template app", with_token[0] == 200 and "/src/main.jsx" in with_token[1])
stage.expect("without the token the link is refused", without[0] in (401, 403))
stage.done()
