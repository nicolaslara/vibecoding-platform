"""Chapter 5: the work survives the Sandbox.

    uv run checks/ch5_snapshots.py [user]

The script:

    $ uv run vibecode.py reset alice
    $ uv run vibecode.py chat alice
    > Change the heading to say Saved.
    >                                      # leave, close the tab
    $ sleep 45                             # the idle clock ends the Sandbox; Modal keeps its filesystem
    $ uv run vibecode.py chat alice        # "new alice sb-…": another Sandbox, the same project
    > Add a line under the heading that says Still here.
    >
    $ uv run vibecode.py reset alice       # and reset still means the template
    $ uv run vibecode.py chat alice

Done when the heading survives the sleep in a new Sandbox, and a reset brings the template back.
"""

import time

import stage

stage.run("reset")
stage.run("chat", typed=["Change the heading in src/App.jsx to say exactly: Saved"])
first = stage.sandbox_of()

print("$ sleep 45   # no tab, no chat: the idle clock runs out")
started = time.time()
while first.poll() is None:
    time.sleep(5)
stage.note(f"{first.object_id} ended {time.time() - started:.0f} s after the chat left\n")

woken = stage.run("chat", typed=["Add a paragraph under the heading that says exactly: Still here"])
second = stage.sandbox_of()
survived = stage.in_project(stage.USER, "Saved")
added = stage.in_project(stage.USER, "Still here")
stage.note("the Sandbox after the sleep:", second.object_id)
stage.note("the heading from before the sleep is in it:", survived, "\n")

stage.run("reset")
stage.run("chat")
fresh = not stage.in_project(stage.USER, "Saved")
stage.note("after a reset the project is the template again:", fresh, "\n")
stage.run("reset")

stage.expect("the first Sandbox ended on its own when idle", first.poll() is not None)
stage.expect("the next chat started another Sandbox", second.object_id != first.object_id and "new " in woken)
stage.expect("the work from before the sleep is in the new Sandbox", survived)
stage.expect("the agent went on from there", added and stage.turns_ended_well(woken) == 1)
stage.expect("a reset brings the template back", fresh)
stage.done()
