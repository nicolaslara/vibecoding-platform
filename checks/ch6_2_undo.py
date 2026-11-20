"""Chapter 6, step 2: undo takes back one message.

    uv run checks/ch6_2_undo.py [user]

The script:

    $ uv run vibecode.py reset alice
    $ uv run vibecode.py chat alice        # open the link
    > Change the heading to say First.
    > Change the heading to say Second.
    $ uv run vibecode.py undo alice        # "turn 1", a new Sandbox and a new link: the heading is First
    $ uv run vibecode.py undo alice        # "turn 0": the template
    $ uv run vibecode.py undo alice        # "nothing to undo"

Undo starts a Sandbox from the snapshot taken before the last message. The link belongs to one
Sandbox, so undo prints a new one.

Done when each undo puts the project back as it was before one message.
"""

import stage
from stage import USER

stage.run("reset")
stage.run(
    "chat",
    tab_open=True,
    typed=[
        "Change the heading in src/App.jsx to say exactly: First",
        "Change the heading in src/App.jsx to say exactly: Second",
    ],
)
two = stage.in_project(USER, "Second")
before = stage.sandbox_of().object_id

once = stage.run("undo")
after = stage.sandbox_of().object_id
back_to_first = stage.in_project(USER, "First") and not stage.in_project(USER, "Second")
stage.note("after one undo the heading is First:", back_to_first, "| a new Sandbox:", after != before, "\n")

twice = stage.run("undo")
template = stage.in_project(USER, "Hello from the template") and not stage.in_project(USER, "First")
stage.note("after two the project is the template:", template, "\n")

empty = stage.run("undo")
stage.run("reset")

stage.expect("two messages changed the project twice", two)
stage.expect(
    "undo took back the second message only, in a new Sandbox", "turn 1" in once and back_to_first and after != before
)
stage.expect("a second undo took back the first: the template", "turn 0" in twice and template)
stage.expect("a third has nothing to take back", "nothing to undo" in empty)
stage.done()
