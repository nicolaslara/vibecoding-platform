"""Chapter 6, step 1: a snapshot of the Sandbox before every message, on record per user.

    uv run checks/ch6_1_turns.py [user]

The script:

    $ uv run vibecode.py reset alice
    $ uv run vibecode.py chat alice
    > Change the heading to say Saved.     # "turn 1": a snapshot of the Sandbox was taken first
    > Add a line under the heading that says Still here.     # "turn 2"
    $ uv run vibecode.py reset alice       # forgets the turns

Each snapshot is an Image of the whole Sandbox. Their ids are kept in a Dict on Modal, under the
user's name. Nothing starts from them yet: when the Sandbox ends, the next chat is at the template.

Done when the Dict holds one Image id per message, and reset forgets them.
"""

import stage
import vibecode

stage.run("reset")
said = stage.run(
    "chat",
    tab_open=True,
    typed=[
        "Change the heading in src/App.jsx to say exactly: Saved",
        "Add a paragraph under the heading that says exactly: Still here",
    ],
)
turns = vibecode.turns_of.get(stage.USER, [])
stage.note("the turns in the Dict:", *turns, "\n")
stage.run("reset")

stage.expect("both turns ended well", stage.turns_ended_well(said) == 2 and "\nturn 2 " in said)
stage.expect("the Dict holds one Image id per message", len(turns) == 2 and all(t.startswith("im-") for t in turns))
stage.expect("reset forgot them", not vibecode.turns_of.get(stage.USER))
stage.done()
