"""Chapter 6: undo takes back one message, and fork gives another user a copy.

    uv run checks/ch6_undo.py [user]

The script:

    $ uv run vibecode.py reset alice
    $ uv run vibecode.py chat alice        # open the link
    > Change the heading to say First.
    > Change the heading to say Second.
    $ uv run vibecode.py undo alice        # "turn 1", a new Sandbox and a new link: the heading is First
    $ uv run vibecode.py fork alice bob    # bob's link shows First too, in a Sandbox of his own
    $ uv run vibecode.py undo alice        # "turn 0": the template
    $ uv run vibecode.py undo alice        # "nothing to undo"

Undo and fork both start a Sandbox from a snapshot. The link belongs to one Sandbox, so each prints a
new one.

Done when each undo puts the project back as it was before one message, the agent's chat with it, and
the fork has the same project in another Sandbox.
"""

import stage
import vibecode
from stage import USER

OTHER = f"{USER}-fork"

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

print(f"$ uv run vibecode.py fork {USER} {OTHER}")
vibecode.fork(USER, OTHER)
print()
copy = stage.in_project(OTHER, "First")
own = stage.sandbox_of(OTHER).object_id not in (before, after)
stage.note("the fork has the heading First:", copy, "| in a Sandbox of its own:", own, "\n")
stage.run("reset", OTHER)

twice = stage.run("undo")
template = stage.in_project(USER, "Hello from the template") and not stage.in_project(USER, "First")
stage.note("after two the project is the template:", template, "\n")

empty = stage.run("undo")
asked = stage.run("chat", typed=["What did I ask you to do before this message? If nothing, answer: nothing"])
answer = asked.split("If nothing, answer: nothing", 1)[-1]

stage.expect("two messages changed the project twice", two)
stage.expect(
    "undo took back the second message only, in a new Sandbox", "turn 1" in once and back_to_first and after != before
)
stage.expect("the fork has the same project in a Sandbox of its own", copy and own)
stage.expect("a second undo took back the first: the template", "turn 0" in twice and template)
stage.expect("a third has nothing to take back", "nothing to undo" in empty)
stage.expect("the agent's chat went back too", "First" not in answer and "Second" not in answer)
stage.done()
