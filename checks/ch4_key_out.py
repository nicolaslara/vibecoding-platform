"""Chapter 4: the agent still works, and the model key is no longer in the Sandbox.

    uv run checks/ch4_key_out.py [user]

The script:

    $ uv run vibecode.py reset alice     # her Sandbox from chapter 3 has the key inside
    $ uv run vibecode.py chat alice
    > Change the heading to say Key is out.
    >                                    # leave, and keep the tab open so the Sandbox stays up
    $ uv run python -c "import vibecode; print(vibecode.running('alice').exec('printenv', 'AUTHORIZATION_BEARER').stdout.read())"
                                         # added-outside: a placeholder, not the key

Modal adds the key to requests for the model's host, outside the Sandbox. The check sends such a
request from inside with no key at all, and it is answered.

What it does not do: an outbound policy cannot be combined with an egress allowlist, so the Sandbox
can still reach any host. The check shows that too.

Done when the agent's edit is in the project, the key is not in the Sandbox's environment, and a
request to the model that carries no key is answered.
"""

import stage
import vibecode

REACH = "node -e 'fetch(process.argv[1], {signal: AbortSignal.timeout(15000)}).then(r => console.log(r.status), e => console.log(\"refused\"))'"

stage.run("reset")
said = stage.run("chat", tab_open=True, typed=["Change the heading in src/App.jsx to say exactly: Key is out"])
edited = stage.in_project(stage.USER, "Key is out")
environment = stage.inside(stage.USER, "env")[1]
model = stage.inside(stage.USER, "sh", "-c", f"{REACH} https://{vibecode.MODEL_HOST}/v1/models")[1]
elsewhere = stage.inside(stage.USER, "sh", "-c", f"{REACH} https://example.com")[1]
placeholder = [line for line in environment.splitlines() if line.startswith("AUTHORIZATION_BEARER=")]
stage.note("the project has the new heading:          ", edited)
stage.note("in the Sandbox's environment:             ", *placeholder)
stage.note("the model, asked from inside with no key: ", model)
stage.note("example.com, from inside:                 ", elsewhere, "<- egress is open\n")

stage.expect("the turn ended well and the edit is in the project", stage.turns_ended_well(said) == 1 and edited)
stage.expect("no proxy token in the Sandbox's environment", "wk-" not in environment)
stage.expect("a request to the model with no key is answered: the key is added outside", model == "200")
stage.done()
