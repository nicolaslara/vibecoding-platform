"""Chapter 3, step 2: every message runs the agent once, inside the user's Sandbox.

    uv run checks/ch3_2_turn.py [user]

The script:

    $ uv run vibecode.py reset alice
    $ uv run vibecode.py chat alice
    > Change the heading to say Hello workshop.
                                         # the agent starts, calls the model, and is refused

The agent runs as a process beside the dev server, and chat prints its output as it comes. It has no
key for the model yet, so the model's gateway refuses it. The next step gives the Sandbox the key.

Done when the agent ran in the Sandbox and the model refused it for lack of a key.
"""

import stage

stage.run("reset")
said = stage.run("chat", tab_open=True, typed=["Change the heading in src/App.jsx to say exactly: Hello workshop"])
edited = stage.in_project(stage.USER, "Hello workshop")
stage.note("the project has the new heading:", edited, "\n")
stage.run("reset")

stage.expect("the agent ran inside the Sandbox, with our model", "> build · " in said)
stage.expect("the model refused it: no key", "proxy auth required" in said and "stopped rc=1" in said)
stage.expect("nothing changed in the project", not edited)
stage.done()
