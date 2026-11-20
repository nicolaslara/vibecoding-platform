"""Chapter 3: a message changes the app.

    uv run checks/ch3_agent.py [user]

The script:

    $ uv run vibecode.py reset alice
    $ uv run vibecode.py chat alice      # open the link
    > Change the heading to say Hello workshop.
                                         # the agent's steps print as it takes them; the tab reloads
    > What does the heading say now? Answer in one line.
                                         # it remembers: the chat continues

The work lives in the Sandbox and nowhere else. Close the tab, wait 30 s, chat again: the template.

What is wrong with it, and chapter 4 fixes: the model key is in the Sandbox, where the agent and
anything it runs can read it. The check prints the key's first three characters from inside, or
"not there" from chapter 4 on.

Done when the agent's edit is in the project and the second message got an answer.
"""

import stage

stage.run("reset")
said = stage.run(
    "chat",
    tab_open=True,
    typed=[
        "Change the heading in src/App.jsx to say exactly: Hello workshop",
        "What does the heading say now? Answer in one line.",
    ],
)
edited = stage.in_project(stage.USER, "Hello workshop")
key = stage.inside(stage.USER, "sh", "-c", 'printf %.3s "$AUTHORIZATION_BEARER"')[1]
stage.note("the project has the new heading:", edited)
stage.note(
    "the model key, read from inside the Sandbox:",
    f"{key}… <- chapter 4 removes it" if key == "wk-" else "not there",
    "\n",
)

answer = said.split("What does the heading say now?", 1)[-1]
stage.expect("both turns ended well", stage.turns_ended_well(said) == 2)
stage.expect("the agent's edit is in the project", edited)
stage.expect("the second message was answered from the same chat", "Hello workshop" in answer)
stage.done()
