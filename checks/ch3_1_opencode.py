"""Chapter 3, step 1: the coding agent is in the Image.

    uv run checks/ch3_1_opencode.py [user]

The script:

    $ uv run vibecode.py reset alice     # the Image changed: the next Sandbox starts from the new one
    $ uv run vibecode.py chat alice      # the first run builds the Image again, with the agent in it
    >

OpenCode is installed in the Image, with a configuration that names our Model Endpoint. The template
gains AGENTS.md: what the agent should know about the project.

Done when the agent's command answers inside the Sandbox and its model is ours.
"""

import stage
import vibecode
from stage import USER

stage.run("reset")
stage.run("chat")
version = stage.inside(USER, "opencode", "--version")[1]
model = stage.inside(USER, "sh", "-c", "echo $MODEL")[1]
rules = stage.inside(USER, "head", "-c", "60", "/project/app/AGENTS.md")[1]
stage.note("in the Sandbox, opencode --version:", version)
stage.note("in the Sandbox, $MODEL:", model)
stage.note("in the Sandbox, AGENTS.md starts:", rules, "\n")
stage.run("reset")

stage.expect("the agent is installed in the Sandbox", version == "1.18.30")
stage.expect("its model is our Model Endpoint", model == vibecode.MODEL)
stage.expect("the template has the agent's instructions", rules.startswith("This is a Vite + React app"))
stage.done()
