"""The chapter slides. For each chapter: the goal and what hurts today, the design drawn on the diagram, the
Modal features it leans on, and the code it adds with notes in the margin.

Each chapter is a branch (ch0-setup … ch7-link) that holds the application at the end of that chapter. The
slides read the branches of this repository as text: the code a chapter adds is `git diff` between two
branches. A code slide names the lines it shows and the lines its notes point at; when one of them is no
longer in the diff the build fails, so the slides cannot drift from the code.
"""

import ast
import base64
import difflib
import html
import pathlib
import re
import subprocess

from common.deck import hl, slide

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
SHOTS = HERE / "assets" / "shots"  # screenshots, by name; a missing one is drawn as a placeholder

VIBECODE, OPENCODE, LINK = "code/vibecode.py", "code/opencode.json", "code/link.py"
AGENTS = "code/app/AGENTS.md"
REPO = "github.com/nicolaslara/vibecoding-platform"  # where this repository is published
APART = "apart"  # in a code slide's show list: the next range gets a box of its own
SKIP = "skip"  # in a show list: lines are left out here, inside the same box, marked with a ⋯
# How a box of code that starts inside a function names that function: "label" writes "in boot(user)" in the
# box's corner, "def" opens the box with the function's def line and a ⋯, and "" leaves it out.
FUNCTION = "def"

# Per chapter, what the talk shows:
#   title      the goal, as the chapter's name
#   opens      the first chapter only: the setup, as steps that come before anything else. Nothing hurts yet,
#              so it has no problems and no wants. The steps after the credits picture carry its code in a corner
#   problems   what hurts before the chapter
#   wants      what the chapter builds, one answer per line
#   design     the design in one line, over the diagram. Left out when the first step's picture is the same picture
#   features   the Modal features it leans on: (name, a line of code, what to know)
#   options    ways to build it, drawn side by side: name, drawing, what to know, docs page, and example
#              (a page of Modal's examples, and what to call it)
#   seen       what we see when we try the chapter by hand: the title over its recorded trace. With
#              seen_from, the trace starts at the first line that begins with it
#   seen_as    in place of the recorded run, what to type and what it prints: commands, shot and foot, as in steps
#   seen_before_code  show the run before the code, when testing a setup done in the dashboard or shell
#   picture    a drawing that explains the idea of the chapter, with a few lines under it
#   compare    comparisons drawn as cards: a title and the options, each with a drawing. With last, the
#              comparison closes the chapter, after what was built, in place of coming before it. With hidden, it
#              is a hidden slide: in the deck only when it is opened with ?hidden=1
#   steps      things typed or clicked rather than coded: title, commands, and shot (screenshot name, where
#              in the dashboard) or, for a step with no dashboard side, foot. A step with picture in place
#              of commands is one image from slides/assets/shots, as large as the slide
#   state      where we are when the chapter starts, in place of problems: the left column of its first slide.
#              A line is neutral, or ("ok", line) for what works, or ("no", line) for what does not
#   tries      after the recorded run, things to type to test it by hand: title, commands and foot, as in steps.
#              commands given as a list are shown as one box each
#   last_step  the branch of the chapter's last step: the same commit as the chapter's own branch, under the
#              step's name, so that every step can be checked out by number
#   parts      a chapter built in steps: each step's branch, check, step (its name, over the diagram: a step
#              without one has no picture, for a step that adds nothing to it), features, seen
#              and code. The chapter's own branch, check, seen and code are its last step
#   code       the code slides: title, optional sub, the lines to show as (start, end) or (file, start, end), and the notes.
#              With context, that many unchanged lines come with each change, for a slide that needs more around it.
#              APART between two ranges puts the second in a box of its own. With whole, the slide shows
#              the code as the step leaves it, not its diff, for a change that moves code; lit names lines to light.
#              With moved, the named function comes first as a before-and-after diff of its own. SKIP in
#              a show list leaves lines out inside one box
#              in the margin as (first line, last line, text[, docs page]). A key is a piece of the line;
#              "^x" is a line that is exactly x; an end of (key, n) takes n more lines. A note with a docs
#              page is about a Modal feature: its lines are lit, an arrow points at them, the page is linked.
CHAPTERS = [
    dict(
        n=0,
        seen="It runs: a prompt here, that reads messages",
        seen_from="$ uv run vibecode.py",
        branch="ch0-setup",
        check="ch0_setup",
        title="Create the scaffolding",
        opens=[
            dict(
                title="Install Modal and log in",
                commands="""# needs uv: docs.astral.sh/uv
$ uv tool install modal
Installed 29 packages in 55ms
 + modal==1.6.4
Installed 1 executable: modal
# fix $PATH if uv warns that the tool is not in your path
$ export PATH="$HOME/.local/bin:$PATH"   # or add it to ~/.zshrc or ~/.bashrc if needed
# log in: opens a browser to sign up or sign in, and saves a token on this machine
$ modal setup""",
                foot="modal.com/docs/guide",
            ),
            dict(title="Claim your credits", picture="credits", foot="scan the code, and fill in the form it opens"),
            dict(
                title="An Environment for the workshop",
                commands="""# a new account has one Environment, main: nothing to do
# had an account already? make an Environment for the workshop, and name it in every terminal
$ modal environment create vibecoding-demo
$ export MODAL_ENVIRONMENT=vibecoding-demo
# several workspaces? name the profile to use, too
$ modal profile list
$ export MODAL_PROFILE=personal
# the workspace this terminal talks to
$ modal token info
      Workspace: nicolaslara""",
                shot=("environment", "Settings → Environments"),
            ),
            dict(
                title="Let's test it out!",
                commands="""# Modal starts a Sandbox in our Environment, runs the command in it, and ends it
$ modal shell -c 'echo hello from a Sandbox; echo $MODAL_SANDBOX_ID'
hello from a Sandbox
sb-01M7Q5EQKZ335BAYXDNC2S2N3W
# ask for more: 4 cores, 8 GiB of memory, a GPU
$ modal shell --cpu 4 --memory 8192 --gpu t4 -c 'nvidia-smi -L'
GPU 0: Tesla T4 (UUID: GPU-d3fb014f-022a-976e-6843-b1c40a906011)
# or stay inside: a prompt in the Sandbox, until exit
$ modal shell
Welcome to Modal's debug shell!
We've provided a number of utilities for you, like `curl` and `ps`.
root / → hostname
modal
root / → exit""",
                foot="modal shell --help",
            ),
        ],
        design="What we're building",
        steps=[
            dict(
                title="Get the code, at chapter 0",
                commands="""$ git clone https://%s.git
$ cd vibecoding-platform
# each chapter is a branch, the application at the end of it: check one out to catch up or jump ahead
$ git checkout ch0-setup
# the application is in code/: its commands run from there
$ cd code"""
                % REPO,
                foot="git checkout ch0-setup",
            )
        ],
        code=[
            dict(
                title="Scaffolding: an interactive prompt",
                show=[("import sys", "nleft")],
                notes=[
                    ("def ask", 'return ""', "Ctrl-C, EOF or an empty line: leave quietly. This part never changes"),
                    ("def chat", "said:", "Our main loop"),
                    ("commands = {", "nleft", "one function per command"),
                ],
            )
        ],
    ),
    dict(
        n=1,
        seen="The model answers with the key, and refuses without it",
        seen_before_code=True,
        seen_as=dict(
            commands=[
                """# with the token
$ curl $ENDPOINT_URL/v1/chat/completions \\
    -H "Authorization: Bearer $AUTHORIZATION_BEARER" \\
    -d '{"messages": [{"role": "user", "content": "Say hello in one word"}]}'
{…,"model":"moonshotai/Kimi-K3","choices":[{…,"message":{"role":"assistant","content":"Hello!",…""",
                """# without it
$ curl $ENDPOINT_URL/v1/chat/completions \\
    -d '{"messages": [{"role": "user", "content": "Say hello in one word"}]}'
{"error":"proxy auth required"}""",
            ],
            foot="git checkout ch1-endpoint",
        ),
        branch="ch1-endpoint",
        check="ch1_endpoint",
        title="Set up an endpoint",
        design="A model served by Modal, and its key in a Secret",
        features_title="Proxy token, Model Endpoint, Secret",
        features=[
            (
                "Proxy token",
                "Authorization: Bearer wk-….ws-…",
                "The key for it. It works in its own workspace only, and must be let into the Environment.",
            ),
            (
                "Model Endpoint",
                "modal endpoint create --shared --model moonshotai/Kimi-K3",
                "An open model served by Modal behind an OpenAI-compatible API. Billed per token; nothing to "
                "deploy or keep warm.",
            ),
            (
                "Secret",
                "modal secret create model-token AUTHORIZATION_BEARER=…",
                "Named, encrypted values. Attach the Secret to a container to expose them as environment variables.",
            ),
        ],
        steps=[
            dict(
                title="A proxy token for our environment",
                commands="""# prints the id and the secret, once
$ modal workspace proxy-tokens create --name vibecoding-demo
      wk-…   ws-…
# a token must be let into an Environment before it works there
$ modal workspace proxy-tokens allow wk-… vibecoding-demo
# keep it for this terminal: the id, a dot, the secret
$ export AUTHORIZATION_BEARER=wk-….ws-…""",
                shot=("proxy-token", "Settings → Proxy Tokens → New Token"),
            ),
            dict(
                title="A Model Endpoint, for Kimi K3",
                commands="""$ modal endpoint create --shared --model moonshotai/Kimi-K3 --name kimi-k3
# its URL, which the code will read from ENDPOINT_URL
$ modal endpoint info kimi-k3""",
                shot=("endpoint", "Endpoints → Create endpoint → Model choices"),
            ),
            dict(
                title="The key, stored as a Secret",
                wide=True,
                commands="""$ modal secret create model-token AUTHORIZATION_BEARER=$AUTHORIZATION_BEARER
# the Secret is there, and the Endpoint is live
$ modal secret list
      model-token
$ modal endpoint info kimi-k3
      State:        live""",
                shot=("secret", "Secrets → Create new secret → Custom"),
            ),
            dict(
                title="Testing the endpoint",
                commands="""# the token, and your Endpoint's URL
$ export AUTHORIZATION_BEARER=wk-….ws-…
$ export ENDPOINT_URL=$(modal endpoint info kimi-k3 --json | jq -r .service_url)
# without jq: export ENDPOINT_URL=https://…  the URL that endpoint info prints
$ curl $ENDPOINT_URL/v1/chat/completions \\
    -H "Authorization: Bearer $AUTHORIZATION_BEARER" \\
    -d '{"messages": [{"role": "user", "content": "Say hello in one word"}]}'
{…,"model":"moonshotai/Kimi-K3","choices":[{…,"message":{"role":"assistant","content":"Hello!",…""",
                foot="an OpenAI-compatible API: /v1/chat/completions",
            ),
        ],
        code=[
            dict(
                title="The code reads the Endpoint's URL from the environment",
                show=[("# The Model Endpoint", "MODEL =")],
                notes=[
                    ("#   $ export", None, "the export from the curl: once per terminal"),
                    ("MODEL =", None, "the model's name: the URL without https://", "shared-endpoints"),
                ],
            )
        ],
    ),
    dict(
        n=2,
        seen="A Sandbox per user, and a link that opens the template",
        branch="ch2-serve",
        last_step="ch2.5-probe",
        check="ch2_serve",
        title="Serve each user's app",
        wants=[
            "A Sandbox per user, running their copy of the app.",
            "It starts in seconds, from an image built once.",
            "A private link for the user's browser, with no public port.",
            "It goes to sleep when nobody is looking.",
        ],
        state=[
            "chat is a prompt on the laptop: it reads messages and repeats them.",
            ("ok", "A model answers on Modal, with our key in a Secret."),
            ("no", "Nothing runs for the user yet: no app, and no place to run one."),
        ],
        design="One Sandbox per user, named after them, all from one Image",
        features_title="Readiness probe",
        features=[
            (
                "Readiness probe",
                "readiness_probe=modal.Probe.with_tcp(8080)",
                "wait_until_ready() returns when the port answers.",
            ),
        ],
        step="Step 5: the link is printed before the app is up, so we add a readiness probe",
        parts=[
            dict(
                branch="ch2.1-sandbox",
                check="ch2_1_sandbox",
                step="Step 1: a Sandbox, and a command run in it",
                features_title="Sandbox, idle timeout",
                features=[
                    (
                        "Sandbox",
                        "modal.Sandbox.create(app=app)",
                        "An isolated execution environment. We can run code in it via exec.",
                    ),
                    (
                        "Idle timeout",
                        "idle_timeout=30",
                        "The Sandbox ends when nothing has used it for 30 s.",
                    ),
                ],
                seen="A Sandbox starts, answers, and ends when nothing uses it",
                seen_as=dict(
                    commands=[
                        """$ uv run vibecode.py chat alice
new alice sb-01M7QQ18AV2P1JTY3DZNP7NRX1
hello from a Sandbox
> """,
                        """# in a second terminal, before the Sandbox idles out
# use the Sandbox ID printed above
$ modal shell sb-01M7QQ18AV2P1JTY3DZNP7NRX1""",
                    ],
                    foot="git checkout ch2.1-sandbox",
                ),
                code=[
                    dict(
                        title="boot: a Sandbox for the user. chat runs a command in it",
                        show=[("import modal", "APP ="), ("def boot", "    return sandbox"), ("def chat", "hello.stdout.read")],
                        notes=[
                            ("APP =", None, "one App holds every user's Sandbox"),
                            ("modal.Sandbox.create(", None, "Sandbox.create: a container, started now", "sandboxes"),
                            ("idle_timeout", "timeout=3600", "it ends when nobody uses it", "sandboxes#idle-timeouts"),
                            ("sandbox.exec", "hello.stdout.read", "exec: a command inside it, and what it printed", "sandbox-spawn"),
                        ],
                    )
                ],
            ),
            dict(
                branch="ch2.2-name",
                check="ch2_2_name",
                step="Step 2: reusing an existing Sandbox",
                features_title="A Sandbox, by name",
                features=[
                    (
                        "Sandbox, by name",
                        "modal.Sandbox.from_name(APP, user)",
                        "One running Sandbox per name in an App. We can find it again by that name.",
                    ),
                ],
                seen="A second chat finds the same Sandbox, and reset ends it",
                seen_as=dict(
                    commands=[
                        """# first chat: create a Sandbox
$ uv run vibecode.py chat alice
new alice sb-01M7QQ2AD8SJYNQ77VAANYW9KH
hello from a Sandbox
> """,
                        """# next chat: reuse the same Sandbox
$ uv run vibecode.py chat alice
running alice sb-01M7QQ2AD8SJYNQ77VAANYW9KH
hello from a Sandbox
> """,
                        """# reset: end it
$ uv run vibecode.py reset alice""",
                    ],
                    foot="git checkout ch2.2-name",
                ),
                code=[
                    dict(
                        title="Reuse a Sandbox by name",
                        sub="running() finds the Sandbox; boot() creates one only when needed.",
                        show=[("def running", "return sandbox if sandbox.poll()"), ("def boot", "name=user")],
                        notes=[
                            ("from_name", "return None", "Sandbox.from_name: one running Sandbox per name", "sandboxes#named-sandboxes"),
                            ("sandbox.poll()", None, "poll(): its exit code, None if still running"),
                            ("sandbox = running(user)", "        return sandbox", "a second chat joins the same Sandbox"),
                            ("name=user", None, "named after the user"),
                        ],
                    ),
                    dict(
                        title="reset: end the user's Sandbox",
                        show=[("def reset", "terminate"), ("commands = {", '"reset": reset')],
                        notes=[
                            ("terminate", None, "the next chat starts a new one"),
                            ('"reset": reset', None, "a second command"),
                        ],
                    ),
                ],
            ),
            dict(
                branch="ch2.3-image",
                check="ch2_3_image",
                step="Step 3: let's run an actual web app",
                features_title="Image, entrypoint",
                features=[
                    (
                        "Image",
                        'modal.Image.from_registry("node:22-slim").run_commands(...)',
                        "An Image built once and cached, with the app template and its packages installed.",
                    ),
                    (
                        "Entrypoint",
                        'modal.Sandbox.create("npm", "run", "dev", image=base)',
                        "The command we pass to Sandbox.create runs as its main process. The Sandbox lives while it runs.",
                    ),
                ],
                seen="The dev server runs inside the Sandbox",
                tries=[
                    dict(
                        title="Test it: a shell inside the running Sandbox",
                        commands=[
                            "$ modal shell sb-01M7QYT59PCJTMNWKSE9QF6GTH",
                            """# inside the Sandbox:
$ curl localhost:8080
<!doctype html>
<html lang="en">
…""",
                        ],
                        foot="modal shell --help",
                    )
                ],
                code=[
                    dict(
                        title="The Image: the template with its packages, built once",
                        show=[("HERE = Path", "APP = "), ("# What every new user", "^)")],
                        notes=[
                            ("from_registry", None, "Image: start from any registry image", "images"),
                            ("add_local_dir", "npm ci", "our template, then its packages. Built once, then cached"),
                        ],
                    ),
                    dict(
                        title="The dev server is the Sandbox's main process",
                        show=[("dev_server =", "workdir="), ("sandbox = boot(user)", "break")],
                        notes=[
                            ("dev_server =", "*dev_server", "the command the Sandbox runs. When it exits, the Sandbox ends", "sandboxes#running-a-sandbox-with-an-entrypoint"),
                            ("image=base", "workdir=", "its files come from our Image. The command runs in /project/app"),
                            ("for line in sandbox.stdout", "break", "what the main process prints: our proof that it runs"),
                        ],
                    ),
                ],
            ),
            dict(
                branch="ch2.4-connect",
                check="ch2_4_connect",
                step="Step 4: a private link, for the browser",
                features_title="Connect token",
                features=[
                    (
                        "Connect token",
                        "sandbox.create_connect_token()",
                        "A URL and a token for one port of one Sandbox. Without the token, the URL answers 401.",
                    ),
                ],
                seen="A link that opens the template, and only with its token",
                code=[
                    dict(
                        title="preview: a link that only opens this user's Sandbox",
                        show=[("def preview", "_modal_connect_token="), ("sandbox = boot(user)", 'print("open"')],
                        notes=[
                            (
                                "create_connect_token",
                                "_modal_connect_token=",
                                "connect token: a URL and a token for this one Sandbox. No public port", "sandbox-networking#connecting-to-sandboxes-with-http-and-websockets",
                            ),
                            ('print("open"', None, "chat prints the link, in place of the log line"),
                        ],
                    )
                ],
            ),
        ],
        code=[
            dict(
                title="A readiness probe: chat waits until the app answers",
                show=[("image=base", "    return sandbox")],
                notes=[
                    ("readiness_probe", None, "Probe: ready when the port answers", "sandboxes#readiness-probes"),
                    ("wait_until_ready", None, "chat waits here, so the link opens at once"),
                ],
            ),
        ],
    ),
    dict(
        n=3,
        seen="A message changes the app",
        branch="ch3-agent",
        last_step="ch3.3-secret",
        check="ch3_agent",
        title="Let an agent change the app",
        wants=[
            "A coding agent in the Sandbox, beside the app.",
            "One run of it per message.",
            "Its steps on the user's screen as it takes them.",
            "A turn that finishes even when the user leaves.",
        ],
        state=[
            ("ok", "Each user has a Sandbox that serves the template, and a private link to it."),
            ("no", "chat still repeats the messages: nothing reads them."),
            ("no", "The model answers, but nothing in the Sandbox calls it."),
        ],
        design="The agent is a process in the same Sandbox, run once per message",
        step="Step 3: the key, in the Sandbox",
        features_title="A Secret on a Sandbox",
        features=[
            (
                "Secret on a Sandbox",
                'secrets=[modal.Secret.from_name("model-token")]',
                "The quick way to hand the agent its key: an environment variable inside. We take it back "
                "in the next chapter.",
            ),
        ],
        parts=[
            dict(
                branch="ch3.1-opencode",
                check="ch3_1_opencode",
                step="Step 1: the agent, in the Image",
                seen="Open OpenCode inside the Sandbox",
                seen_as=dict(
                    sub="Test the installed agent directly. We'll connect it to chat in the next step.",
                    commands=[
                        """# start a fresh Sandbox from the updated Image
$ uv run vibecode.py reset alice
$ uv run vibecode.py chat alice""",
                        """# in a second terminal, use the Sandbox ID printed by chat
$ modal shell sb-…""",
                        """# inside the Sandbox
$ cd /project/app
$ opencode
# it has no key yet: a prompt is refused until step 3""",
                    ],
                    shot=("opencode-start", "OpenCode 1.18.30 inside the Sandbox"),
                    foot="git checkout ch3.1-opencode",
                ),
                features_title="The Image, again",
                features=[
                    (
                        "Image",
                        '.run_commands("npm install -g opencode-ai@1.18.30")',
                        "The agent, its config and the model's name are more layers of the same Image. A Sandbox "
                        "that is running keeps the Image it started from.",
                    ),
                ],
                code=[
                    dict(
                        title="The agent goes into the Image",
                        show=[("# What every new user", "^)")],
                        notes=[
                            ("npm install -g opencode", None, "OpenCode: a coding agent with a command line"),
                            ("add_local_file", None, "its config: which model, and where"),
                            ("# agent. MODEL is part", None, "after changing MODEL, reset the user to start from the updated Image"),
                            ('"MODEL": MODEL', None, "the model's name, from chapter 1"),
                        ],
                    ),
                    dict(
                        title="Its config: the model, and a key read from the environment",
                        show=[(OPENCODE, "^{", "^}")],
                        notes=[
                            ('"model":', None, "MODEL, set in the Image"),
                            ("baseURL", None, "the gateway, called straight from the Sandbox"),
                            ("apiKey", None, "the key: read from the env var AUTHORIZATION_BEARER"),
                        ],
                    ),
                    dict(
                        title="What the agent is told: this app, and many small edits",
                        show=[(AGENTS, "This is a Vite", "- Every edit must leave")],
                        notes=[
                            ("This is a Vite", "with hot reload", "AGENTS.md, in the project: the agent reads it every turn"),
                            ("- The user watches", "until the page is rich", "the page changes every few seconds"),
                            ("- Once a file exists", "- Every edit must leave", "edits, not rewrites: each one reloads the tab"),
                        ],
                    ),
                ],
            ),
            dict(
                branch="ch3.2-turn",
                check="ch3_2_turn",
                step="Step 2: one turn of the agent per message",
                seen="The agent runs in the Sandbox, and the model refuses it: no key yet",
                features_title="exec: a process beside the entrypoint",
                features=[
                    (
                        "exec",
                        'agent = sandbox.exec("sh", "-c", AGENT, message)',
                        "A process beside the entrypoint, in the same filesystem. While it runs, the Sandbox stays up.",
                    ),
                    (
                        "Streamed output",
                        "for chunk in agent.stdout: ...",
                        "Chunks as they arrive, while the agent works.",
                    ),
                    (
                        "Exit code",
                        "agent.wait()",
                        "Blocks until the process ends. The exec outlives its client: close the terminal and the "
                        "agent finishes the turn.",
                    ),
                ],
                code=[
                    dict(
                        title="One turn of the agent is one shell command",
                        show=[("# One turn of the agent", "AGENT = ")],
                        notes=[
                            ("#   -c", None, "the agent remembers the conversation"),
                            ("< /dev/null", "2>&1", "two OpenCode habits: it waits on stdin, and reports on stderr"),
                            ("AGENT =", None, "the whole turn, in one line"),
                        ],
                    ),
                    dict(
                        title="Each message is one exec, and we watch it run",
                        show=[("def chat", "stopped rc=")],
                        notes=[
                            ("if sandbox.poll() is not None", "            print(", "it went idle since the last message: start it again"),
                            ("agent = sandbox.exec", None, "exec: a process beside the dev server. It runs on if we leave", "sandbox-spawn"),
                            ("for chunk in agent.stdout", "print(chunk", "its output, as it comes", "sandbox-spawn#output"),
                            ("if agent.wait() == 0", "stopped rc=", "the exit code is the verdict"),
                        ],
                    ),
                ],
            ),
        ],
        code=[
            dict(
                title="The Sandbox gets the key: one line",
                show=[("idle_timeout=30", ("secrets=", 1))],
                notes=[
                    ("secrets=", None, "the Secret sets AUTHORIZATION_BEARER in the Sandbox. For now", "secrets"),
                ],
            ),
        ],
    ),
    dict(
        n=4,
        seen="The agent still works, and cannot read the key",
        branch="ch4-key-out",
        check="ch4_key_out",
        title="Keep the key away from the agent",
        state=[
            ("ok", "A message changes the app: the agent works."),
            ("no", "The model key is in the agent's environment: one echo prints it."),
            ("no", "The agent runs commands nobody reviewed, and can send what it reads anywhere."),
        ],
        wants=[
            "The key never enters the Sandbox.",
            "Modal adds it to the agent's requests to the model, outside.",
            "The agent and its config stay as they are.",
        ],
        design="Modal adds the key outside the Sandbox, on the way to the model",
        options_title="Three ways to keep the key from the agent",
        options=[
            dict(
                name="Outbound policy",
                drawing="policy",
                chosen=True,
                lines=[
                    "Modal adds the key to the request, outside the Sandbox.",
                ],
                docs="sandbox-secret-injection",
            ),
            dict(
                name="Sidecar",
                drawing="sidecar",
                lines=[
                    "A proxy in a second container, beside the Sandbox, holds the key.",
                ],
                docs="sandbox-sidecars",
            ),
            dict(
                name="MCP server",
                drawing="mcp",
                lines=[
                    "A server outside holds the key, behind a tool the agent calls.",
                ],
                docs="",
                example=("mcp_server_stateless", "an MCP server on Modal"),
            ),
        ],
        features=[],
        code=[
            dict(
                title="Credential injection with header replacement",
                context=12,
                show=[
                    ("^base = (", "modal.Image.from_registry"),
                    SKIP,
                    (".env(", ("^)", 1)),
                    ("MODEL_HOST =", "^)"),
                    ("timeout=3600", "^)"),
                ],
                notes=[
                    ('"AUTHORIZATION_BEARER": "added-outside"', None, "OpenCode uses a placeholder; the real key stays outside"),
                    ("MODEL_HOST =", None, "the gateway opencode.json calls"),
                    ("key_added_outside =", "headers=", "outbound policy: for this host, set this header, from this Secret", "sandbox-secret-injection"),
                    ("_experimental_outbound_policy", None, "the Secret never enters the Sandbox"),
                ],
            ),
        ],
    ),
    dict(
        n=5,
        seen="The work survives the Sandbox",
        branch="ch5-snapshots",
        check="ch5_snapshots",
        title="Save the work",
        wants=[
            "When a Sandbox ends, its filesystem is kept.",
            "The next one starts where the last one ended.",
            "reset still means the template.",
        ],
        state=[
            ("ok", "A message changes the app, and the key stays outside the Sandbox."),
            ("no", "The work lives in the Sandbox, and the Sandbox ends 30 s after the tab closes."),
            ("no", "Nothing is kept: the next chat starts from the template."),
        ],
        design="Keep the filesystem when the Sandbox ends, and wake from it",
        features_title="Exit Snapshot, Dict",
        features=[
            (
                "Exit Snapshot",
                'experimental_options={"enable_exit_snapshot": True}',
                "However the Sandbox ends, its whole filesystem is kept as an Image.",
            ),
            (
                "Dict",
                'modal.Dict.from_name("vibecode-users", create_if_missing=True)',
                "A named key-value store on Modal.",
            ),
        ],
        compare=[
            dict(
                title="Four ways to keep what is in a Sandbox",
                options=[
                    dict(
                        name="Directory Snapshot",
                        drawing="keep-dir",
                        lines=["One directory, while the Sandbox runs.", "Comes back as a mount in a Sandbox."],
                        docs="sandbox-snapshots#directory-snapshots",
                    ),
                    dict(
                        name="Filesystem Snapshot",
                        tag="next chapter: undo",
                        drawing="keep-fs",
                        lines=["The whole filesystem, while the Sandbox runs.", "A new Sandbox starts from it."],
                        docs="sandbox-snapshots#filesystem-snapshots",
                    ),
                    dict(
                        name="Exit Snapshot",
                        tag="this chapter",
                        drawing="keep-fs",
                        lines=["A Filesystem Snapshot, taken when the Sandbox ends.", "A new Sandbox starts from it."],
                        docs="sandbox-exit-snapshots",
                    ),
                    dict(
                        name="Memory Snapshot",
                        drawing="keep-memory",
                        lines=["Filesystem and processes. Taking one ends the Sandbox.", "Comes back running."],
                        docs="sandbox-snapshots#memory-snapshots",
                    ),
                ],
            ),
            dict(
                hidden=True,
                title="Snapshot everything, or only the project?",
                options=[
                    dict(
                        name="Filesystem Snapshot",
                        tag="what we build",
                        drawing="whole",
                        lines=["Base and project, one Image."],
                        good=["Nothing to mount.", "Kept by the Exit Snapshot."],
                        bad=["A new base misses existing users.", "No warm pool."],
                    ),
                    dict(
                        name="Directory Snapshot, mounted",
                        drawing="mounted",
                        lines=["One base. The project is mounted."],
                        good=["A new base reaches every user.", "A warm pool is possible."],
                        bad=["A mount at every start.", "Not kept by the Exit Snapshot."],
                    ),
                ],
            ),
        ],
        code=[
            dict(
                title="When a Sandbox ends, Modal keeps its filesystem. The next one starts from it",
                show=[("def last_filesystem", "return base"), ("app=app,", "^)")],
                notes=[
                    ("include_terminated=True", "_experimental_get_exit_snapshot", "the last Sandbox by that name, and the Image it left", "sandbox-exit-snapshots"),
                    ("except modal.Error", "return base", "nothing kept: the template"),
                    ("image=base", "image=last_filesystem", "restore the user's work; after reset, use the template"),
                    ("experimental_options", None, "Snapshot on exit", "sandbox-exit-snapshots"),
                ],
            ),
            dict(
                title="A record of who has work, so that reset still means the template",
                context=6,
                show=[
                    ("# The app's own record", "has_work = modal.Dict"),
                    ("while message := ask()", "started = time.time()"),
                    APART,
                    ("def reset", "has_work.pop"),
                ],
                notes=[
                    ("has_work = modal.Dict", None, "Dict: a named store on Modal. Not on the laptop", "dicts"),
                    ("has_work[user] = True", None, "on message received, mark as has_work"),
                    ("has_work.pop", None, "reset forgets it"),
                ],
            ),
        ],
    ),
    dict(
        n=6,
        seen="fork: bob gets alice's project, and changes to his do not reach hers",
        seen_as=dict(
            commands=[
                """$ uv run vibecode.py fork alice bob
running alice sb-01M7SGT8N75Q9Y726DNCZM3A47
new bob sb-01M7SGTR4KX4DNVE62VQHPN1M7
open https://a-ta-01m7sgtr4kdmahzh1jyzg0qnav-mkw7u-….w.modal.host/?_modal_connect_token=…""",
                """# bob changes his copy
$ uv run vibecode.py chat bob
running bob sb-01M7SGTR4KX4DNVE62VQHPN1M7
> Change the heading in src/App.jsx to say exactly: Bob
…
turn 2 6s""",
                """# his file, then hers
$ modal shell sb-01M7SGTR4KX4DNVE62VQHPN1M7 -c 'grep h1 /project/app/src/App.jsx'
  return <h1>Bob</h1>
$ modal shell sb-01M7SGT8N75Q9Y726DNCZM3A47 -c 'grep h1 /project/app/src/App.jsx'
  return <h1>Alice</h1>""",
            ],
            foot="git checkout ch6.3-fork",
        ),
        branch="ch6-undo",
        last_step="ch6.3-fork",
        check="ch6_undo",
        title="Undo a message and fork a project",
        state=[
            ("ok", "The user's work survives the Sandbox."),
            ("no", "The agent got it wrong: there is no way back."),
            ("no", "Two people cannot start from the same project."),
        ],
        wants=[
            "A Snapshot before every message, on record per user.",
            "undo: restart the user's Sandbox from the state before the last message.",
            "fork: start another user's Sandbox from a copy of the project.",
        ],
        picture=dict(
            title="Snapshots are Images",
            lines=[
                "A Snapshot is an Image, and a Sandbox always starts from an Image.",
                "Start, wake, undo and fork all create a Sandbox.",
            ],
        ),
        features_title="Step 3: fork, a Sandbox from someone else's state",
        features=[
            (
                "Fork",
                "boot(user).snapshot_filesystem()",
                "Snapshot a running Sandbox and start a second one from it. The first keeps running.",
            ),
        ],
        parts=[
            dict(
                branch="ch6.1-turns",
                check="ch6_1_turns",
                step="Step 1: a Snapshot before every message",
                seen="Every message has a Snapshot before it, on record per user",
                seen_as=dict(
                    commands=[
                        """$ uv run vibecode.py chat alice
> Change the heading in src/App.jsx to say exactly: Saved
…
turn 1 8s
> Add a paragraph under the heading that says exactly: Still here
…
turn 2 6s
>""",
                        """# the record: one Snapshot per message, each an Image
$ modal dict get vibecode-turns alice
['im-01M7SG3MF9RVJDQ92PVT758TS2', 'im-01M7SG3Y220FEYWWWQS7HN2ATZ']""",
                        """$ uv run vibecode.py reset alice
$ modal dict get vibecode-turns alice
None""",
                    ],
                    foot="git checkout ch6.1-turns",
                ),
                features_title="Filesystem Snapshot",
                features=[
                    (
                        "Filesystem Snapshot",
                        "sandbox.snapshot_filesystem()",
                        "The whole filesystem of a running Sandbox, as an Image. The Sandbox keeps running.",
                    ),
                    (
                        "Dict",
                        'modal.Dict.from_name("vibecode-turns", create_if_missing=True)',
                        "The app's record grows: per user, the ids of their Snapshots.",
                    ),
                ],
                code=[
                    dict(
                        title="Before every message, a Snapshot",
                        context=6,
                        show=[
                            ("# The app's own record", "turns_of = modal.Dict"),
                            ("while message := ask()", "for chunk in agent.stdout"),
                        ],
                        notes=[
                            ("turns_of = modal.Dict", None, "each user's list of turn Snapshots"),
                            ("turns = checkpoint", None, "before the agent touches anything: the state undo will go back to"),
                        ],
                    ),
                    dict(
                        title="checkpoint: a Snapshot, and its id on record",
                        show=[
                            ("def checkpoint", "return turns"),
                            APART,
                            ("def reset", "turns_of.pop"),
                        ],
                        notes=[
                            ("snapshot_filesystem", None, "the whole Sandbox as an Image", "sandbox-snapshots#filesystem-snapshots"),
                            ("turns_of.get(user, [])", "turns_of[user] = turns", "its id joins the user's list"),
                            ("turns_of.pop", None, "reset forgets them"),
                        ],
                    ),
                ],
            ),
            dict(
                branch="ch6.2-undo",
                check="ch6_2_undo",
                step="Step 2: undo, a Sandbox from an earlier state",
                seen="undo takes back one message at a time, down to the template",
                features_title="A Sandbox from a Snapshot",
                features=[
                    (
                        "A Sandbox from a Snapshot",
                        "modal.Sandbox.create(*entrypoint, image=snapshot)",
                        "A Snapshot is an Image, so a Sandbox starts from it like from any other.",
                    ),
                ],
                code=[
                    dict(
                        title="Extract Sandbox creation for undo and fork",
                        moved="boot",
                        show=[
                            ("def boot", "sandbox = modal.Sandbox.create("),
                            SKIP,
                            ("sandbox.wait_until_ready()", "return start(user"),
                            APART,
                            ("def start", "image=image,"),
                        ],
                        lit=["image=image,"],
                        notes=[
                            ("app = modal.App.lookup", "    return sandbox", "what boot did itself: start a Sandbox"),
                            ("return start(user", None, "now it picks the Image and hands over"),
                            ("def start(user, image)", '"""A new Sandbox', "the same lines, moved here, with the Image as an argument"),
                            ("image=image,", None, "so undo can start one from a Snapshot", "sandbox-snapshots#filesystem-snapshots"),
                        ],
                    ),
                    dict(
                        title="undo: restart the user's Sandbox from the previous state",
                        show=[("def undo", 'print("open", preview(sandbox, user))')],
                        notes=[
                            ("turns = turns_of.get", "        return", "the user's Snapshots, from the Dict"),
                            ("before = modal.Image.from_id", None, "the Snapshot taken before the last message"),
                            ("sandbox = running(user)", "sandbox.terminate", "one Sandbox per name: the old one ends first"),
                            ("sandbox = start(user, before)", None, "a Sandbox from a Snapshot", "sandbox-snapshots#filesystem-snapshots"),
                            ('print("open"', None, "a new Sandbox has a new link"),
                        ],
                    ),
                ],
            ),
        ],
        code=[
            dict(
                title="fork: start another user's Sandbox from a Snapshot",
                show=[("def fork", 'print("open", preview(sandbox, other))'), ('"reset": reset}', '"fork": fork')],
                notes=[
                    ("now = boot(user).snapshot_filesystem()", None, "the user's current project, as an Image", "sandbox-snapshots#forking"),
                    ("reset(other)", "turns_of[other]", "the new user gets the same history, so they can undo"),
                    ("sandbox = start(other, now)", None, "the same start, under another name"),
                    ('"fork": fork', None, "one more command"),
                ],
            ),
        ],
    ),
    dict(
        n=7,
        seen="Hot reload passes: the open tab follows the agent's edits",
        seen_as=dict(
            commands=[
                """# after a change to link.py, deploy alice's link again
$ uv run link.py alice""",
                """# her address, open in a tab, while she chats
$ uv run vibecode.py chat alice
open https://nicolaslara-vibecoding-demo--vibecode-alice.us-east.modal.run
> Change the heading to say Linked.""",
            ],
            foot="git checkout ch7.2-websocket",
        ),
        branch="ch7-link",
        last_step="ch7.2-websocket",
        check="ch7_link",
        title="Give each user an address",
        optional=True,
        wants=[
            "One address per user, the same after every sleep.",
            "No token in it.",
            "A visit is enough to wake the Sandbox.",
        ],
        state=[
            ("no", "The link changes every time the Sandbox wakes."),
            ("no", "It carries a token: whoever sees the link holds the key to it."),
            ("no", "Someone has to run chat to wake the Sandbox."),
        ],
        features_title="Step 2: hot reload",
        features=[
            (
                "Websockets",
                '@web.websocket("/{path:path}")',
                "A web Function takes websockets too. Hot reload is one: the tab's socket is passed on to the "
                "dev server, both ways.",
            ),
        ],
        parts=[
            dict(
                branch="ch7.1-http",
                check="ch7_1_http",
                step="Step 1: an address per user, which finds or wakes their Sandbox",
                seen="The address stays the same, and a visit starts the Sandbox",
                seen_as=dict(
                    commands=[
                        """$ uv run vibecode.py chat alice
new alice sb-01M7SHJ9EYH3TA6Z0BA3WJHAW4
open https://nicolaslara-vibecoding-demo--vibecode-alice.us-east.modal.run
>""",
                        """# end her Sandbox: nothing runs for alice now. Then visit her address
$ uv run vibecode.py reset alice
$ curl https://nicolaslara-vibecoding-demo--vibecode-alice.us-east.modal.run
<!doctype html>
<html lang="en">
…""",
                        """# the visit started a Sandbox: chat finds it running
$ uv run vibecode.py chat alice
running alice sb-01M7SHJH3N85FJ1GP71AFJH70D
open https://nicolaslara-vibecoding-demo--vibecode-alice.us-east.modal.run""",
                    ],
                    foot="git checkout ch7.1-http",
                ),
                features_title="Web Functions",
                features=[
                    (
                        "Web Function",
                        "@modal.asgi_app(label=...)",
                        "A deployed Function with a host name of its own, run on demand: any ASGI app, websockets "
                        "included.",
                    ),
                    (
                        "Deploy from code",
                        "app.deploy()",
                        "The script defines a small App per user and deploys it at their first chat.",
                    ),
                    (
                        "Concurrency",
                        "@modal.concurrent(max_inputs=100)",
                        "One container serves the many requests of a page at once.",
                    ),
                    (
                        "The address",
                        "https://<workspace>-<environment>--vibecode-alice.modal.run",
                        "Public: anyone who has it can open the app and wake the Sandbox.",
                    ),
                ],
                code=[
                    dict(
                        title="chat prints the user's own address, from link.py",
                        moved="preview",
                        show=[
                            (VIBECODE, "def preview", "return link.address(user)"),
                            (LINK, "def address", "        return link.get_web_url()"),
                        ],
                        notes=[
                            ("access = sandbox.create_connect_token", "_modal_connect_token=", "the link with a token in it goes"),
                            ("import link", "return link.address(user)", "the user's stable address takes its place"),
                            ("modal.Function.from_name", None, "deployed already? Modal knows its URL"),
                            ("app, link = link_for(user)", "app.deploy()", "the first time: deploy it from here", "managing-deployments"),
                        ],
                    ),
                    dict(
                        title="A web Function per user, defined when we need it",
                        show=[(LINK, "# The Function creates Sandboxes", "^)"), (LINK, "def link_for", "def link():")],
                        notes=[
                            ("add_local_python_source", "opencode.json", "it carries our code, so it can start a Sandbox itself"),
                            ("app = modal.App(", None, "one small App per user"),
                            ("serialized=True", None, "defined at run time, shipped as it is"),
                            ("@modal.concurrent", None, "one container, many requests at once", "concurrent-inputs"),
                            ("@modal.asgi_app", None, "web Function: a host name of its own", "webhooks#asgi-apps---fastapi-fasthtml-starlette"),
                        ],
                    ),
                    dict(
                        title="For each request: find the Sandbox or wake it, then pass the request on",
                        show=[
                            (LINK, "@web.api_route", ("content=await request.body()", 1)),
                            APART,
                            (LINK, "def sandbox_access():", "return access"),
                        ],
                        notes=[
                            ("with lock:", "if time.time() - checked", "one wake at a time, remembered for 5 s"),
                            ("sandbox = vibecode.boot(user)", None, "the same boot as chat: running, or woken from where it ended"),
                            ('headers["authorization"]', None, "the Function presents the token. The browser never sees it"),
                            ("response = await client.request", "content=await request.body()", "the same request, on the Sandbox"),
                        ],
                    ),
                    dict(
                        title="A visit and a chat can both start the Sandbox: the second waits",
                        show=[(VIBECODE, 'print("running", user', "        return boot(user)")],
                        notes=[
                            ("return start(user", None, "Sandbox names are unique: only one create wins", "sandboxes#named-sandboxes"),
                            ("except modal.exception.AlreadyExistsError", "return boot(user)", "the other one is starting it: look again in a second"),
                        ],
                    ),
                ],
            ),
        ],
        code=[
            dict(
                title="Proxy the WebSocket connection for hot reload",
                show=[(LINK, "@web.websocket", "return_when=asyncio.FIRST_COMPLETED")],
                notes=[
                    ("@web.websocket", None, "web Functions take websockets", "webhooks#websockets"),
                    ("async with websockets.connect", ") as dev_server:", "a second socket, to the dev server, with the token"),
                    ("async def to_the_tab", "await dev_server.send(message)", "relay messages until either connection closes"),
                ],
            ),
        ],
    ),
]  # fmt: skip

DOCS = "https://modal.com/docs/guide/"
# The documentation page of each feature card, by the card's name. Checked against modal.com on 2026-11-17.
FEATURE_DOCS = {
    "Workspace": "workspaces",
    "Environment": "environments",
    "Sandbox": "sandboxes",
    "Model Endpoint": "shared-endpoints",
    "Proxy token": "webhook-proxy-auth",
    "Secret": "secrets",
    "Image": "images",
    "Sandbox, by name": "sandboxes#named-sandboxes",
    "Entrypoint": "sandboxes#running-a-sandbox-with-an-entrypoint",
    "Websockets": "webhooks#websockets",
    "Readiness probe": "sandboxes#readiness-probes",
    "Connect token": "sandbox-networking#connecting-to-sandboxes-with-http-and-websockets",
    "Idle timeout": "sandboxes#idle-timeouts",
    "exec": "sandbox-spawn",
    "Streamed output": "sandbox-spawn#output",
    "Exit code": "sandboxes#return-codes",
    "Secret on a Sandbox": "secrets",
    "Sidecar": "sandbox-sidecars",
    "Outbound policy": "sandbox-secret-injection",
    "Exit Snapshot": "sandbox-exit-snapshots",
    "Filesystem Snapshot": "sandbox-snapshots#filesystem-snapshots",
    "A Sandbox from a Snapshot": "sandbox-snapshots#filesystem-snapshots",
    "Dict": "dicts",
    "Fork": "sandbox-snapshots#forking",
    "Web Function": "webhooks#asgi-apps---fastapi-fasthtml-starlette",
    "Deploy from code": "managing-deployments",
    "Concurrency": "concurrent-inputs",
}

LINE = 18.5  # px, a line of code on a code slide
PAD = 12  # px, above the first line
ROWS = 27  # lines a code slide holds
BLOCK_GAP = 2  # lines the break between two boxes of code takes: their padding, and the space between
NOTE_LINE = 23  # px, a line of handwriting
NOTE_CHARS = 26  # characters of handwriting across the margin, counted low: a note that wraps must not be hit
NOTE_GAP = 20  # px, between two notes that would otherwise touch

CSS = """
  .ch-why { display: grid; grid-template-columns: 1fr 1fr; gap: 22px; align-items: stretch; padding-top: 8px; }
  .ch-why .col { padding: 24px 28px 10px; border: 1px solid var(--semantic-border-elevated); border-radius: var(--radius-lg); background: var(--semantic-background-elevated); }
  .ch-why .bad { border-top: 3px solid var(--semantic-text-danger); }
  .ch-why .good { border-top: 3px solid var(--semantic-text-accent); }
  .ch-why h3 { margin: 0 0 18px; font-size: 13px; line-height: 16px; letter-spacing: .08em; text-transform: uppercase; font-weight: 600; }
  .ch-why .bad h3 { color: var(--semantic-text-danger); }
  .ch-why .good h3 { color: var(--semantic-text-accent); }
  .ch-why ul { margin: 0; padding: 0; list-style: none; }
  .ch-why li { position: relative; margin: 0 0 18px; padding-left: 34px; font-size: 23px; line-height: 33px; color: var(--semantic-text-primary); }
  .ch-why li::before { position: absolute; left: 0; font-weight: 600; }
  .ch-why .bad li::before { content: "✗"; color: var(--semantic-text-danger); }
  .ch-why .now { border-top: 3px solid var(--semantic-border-elevated); }
  .ch-why .now h3 { color: var(--semantic-text-secondary); }
  .ch-why .now li::before { content: "·"; color: var(--semantic-text-secondary); }
  .ch-why .now li.ok::before { content: "✓"; color: var(--semantic-text-accent); }
  .ch-why .now li.no::before { content: "✗"; color: var(--semantic-text-danger); }
  .ch-why .good li::before { content: "✓"; color: var(--semantic-text-accent); }
  .ch-feat h3, .ch-hidden h3 { margin: 0 0 12px; font-size: 13px; line-height: 16px; letter-spacing: .08em; text-transform: uppercase; font-weight: 600; color: var(--semantic-text-accent); }
  .ch-table a { color: inherit; text-decoration: none; border-bottom: 1px solid var(--semantic-border-primary-hover); }
  .ch-feat { display: grid; grid-template-columns: 1fr; gap: 9px; align-content: start; }
  .ch-feat .card { display: grid; grid-template-columns: .82fr 1.18fr; gap: 26px; align-items: center; padding: 9px 20px; }
  .ch-feat h3 { margin: 0 0 2px; font-size: 19px; line-height: 26px; letter-spacing: 0; text-transform: none; font-weight: 500; color: var(--semantic-text-primary); }
  .ch-feat p { margin: 0; font-size: 15.5px; line-height: 22px; color: var(--semantic-text-secondary); }
  .ch-feat pre.code { font-size: 13px; line-height: 20px; padding: 9px 14px; white-space: pre; overflow: hidden; }
  pre.code .sh-p { color: #a6e22e; user-select: none; }
  pre.code .sh-cmd { color: #66d9ef; }
  pre.code .sh-sub { color: #f8f8f2; }
  pre.code .sh-flag { color: #fd971f; }
  pre.code .sh-str { color: #e6db74; }
  pre.code .sh-var { color: #ae81ff; }
  pre.code .sh-op { color: #f92672; }
  pre.code .sh-c { color: #8f908a; font-style: italic; }
  pre.code .sh-o { color: #a9aaa0; }
  pre.code .sh-m { color: #e6db74; }
  .ch-steps { display: grid; grid-template-columns: 1.12fr .88fr; gap: 20px; height: 100%; min-height: 0; align-items: start; }
  .ch-steps.alone { grid-template-columns: 1fr; }
  .ch-steps.wide { grid-template-columns: 2fr 1fr; }
  .ch-picture { height: 100%; min-height: 0; display: flex; align-items: center; justify-content: center; }
  .ch-picture img { max-width: 100%; max-height: 100%; border-radius: var(--radius-lg); }
  .ch-credits { position: absolute; right: 70px; bottom: 64px; width: 150px; height: 150px; border-radius: 8px; }
  .ch-steps pre.code, .ch-shell pre.code { font-size: 14px; line-height: 25px; padding: 14px 18px; white-space: pre-wrap; word-break: break-word; }
  .ch-shot { margin: 0; padding: 0; border: 1px solid var(--semantic-border-elevated); border-radius: var(--radius-lg); overflow: hidden; display: block; background: var(--semantic-background-elevated); }
  .ch-shot img { display: block; width: 100%; height: auto; }
  .ch-shot figcaption { padding: 7px 12px; font-size: 13px; line-height: 18px; color: var(--semantic-text-tertiary); border-top: 1px solid var(--semantic-border-secondary); }
  .ch-shot.todo { border-style: dashed; background: none; }
  .ch-shot.todo .hole { aspect-ratio: 16 / 10; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 8px; color: var(--semantic-text-tertiary); font-size: 16px; }
  .ch-shot.todo .hole b { font-weight: 500; color: var(--semantic-text-secondary); font-size: 19px; }
  .ch-shot.todo .hole code { font-family: var(--font-mono); font-size: 12.5px; }
  .ch-code { display: grid; grid-template-columns: 856px 1fr; gap: 0; align-items: start; }
  .ch-code pre.code { box-sizing: border-box; font-size: 13px; line-height: 18.5px; padding: 12px 16px; white-space: pre; overflow: hidden; }
  .ch-code pre.code { position: relative; }
  .ch-code pre.code[data-in]::after { content: attr(data-in); position: absolute; top: 5px; right: 14px; font-family: var(--font-mono); font-size: 12px; line-height: 16px; color: var(--semantic-text-tertiary); }
  .ch-code .ch-blocks, .ch-steps .ch-blocks { display: flex; flex-direction: column; gap: 11px; min-width: 0; }
  .ch-code .ln { border-radius: 0; }  /* lit lines that follow each other read as one block */
  .ch-code .ln.add { background: rgba(120, 200, 120, .17); }
  .ch-code .ln.del { background: rgba(230, 110, 110, .15); opacity: .7; }
  .ch-code .ln.hunk { color: #8f908a; }
  .ch-code .ln.file { color: #e6db74; font-weight: 600; }
  .ch-code .g { user-select: none; opacity: .7; }
  .ch-code .ln.feat { background: rgba(110, 150, 255, .24); box-shadow: inset 3px 0 0 #7f9cff; }
  .ch-opts { display: grid; grid-template-columns: repeat(var(--cols, 3), 1fr); gap: 16px; align-items: stretch; }
  .ch-opts .card { padding: 16px 18px; display: flex; flex-direction: column; }
  .ch-opts .card.chosen { border-color: var(--semantic-text-accent); }
  .ch-opts h3 { margin: 0 0 4px; font-size: 20px; line-height: 26px; font-weight: 500; color: var(--semantic-text-primary); }
  .ch-opts h3 span { margin-left: 10px; font-size: 11px; letter-spacing: .1em; text-transform: uppercase; font-weight: 600; color: var(--semantic-text-accent); }
  .ch-opts svg { width: 100%; height: auto; margin: 6px 0 10px; }
  .ch-opts p { margin: 0 0 10px; font-size: 16px; line-height: 24px; color: var(--semantic-text-secondary); }
  .ch-opts p:first-of-type { color: var(--semantic-text-primary); }
  .ch-opts a.ch-docs { margin-top: auto; align-self: flex-start; }
  .ch-opts.many p { font-size: 15px; line-height: 22px; }
  .ch-opts.many h3 { font-size: 18px; }
  .ch-opts.many h3 span { display: block; margin: 2px 0 0; }
  .ch-opts ul { list-style: none; margin: 2px 0 8px; padding: 0; }
  .ch-opts li { position: relative; margin: 0 0 7px; padding-left: 26px; font-size: 16px; line-height: 24px; color: var(--semantic-text-primary); }
  .ch-opts li::before { position: absolute; left: 0; font-weight: 600; }
  .ch-opts li.good::before { content: "✓"; color: var(--semantic-text-accent); }
  .ch-opts li.bad::before { content: "✗"; color: var(--semantic-text-danger); }
  .kp-on { fill: var(--semantic-background-accent); stroke: var(--semantic-text-accent); stroke-width: 1.5; }
  .kp-off { fill: none; stroke: var(--semantic-border-primary); opacity: .6; }
  .kp-off-t { font-size: 13px; fill: var(--semantic-text-tertiary); }
  .kp-on-t { font-size: 13px; font-weight: 500; fill: var(--semantic-text-primary); }
  .kp-no { font-size: 13px; font-weight: 600; fill: var(--semantic-text-danger); }
  .ch-tree { display: flex; flex-direction: column; height: 100%; min-height: 0; }
  .ch-tree svg { width: 100%; height: auto; flex: 0 1 auto; min-height: 0; }
  .ch-tree ul { margin: 6px 0 0; padding-left: 20px; font-size: 16.5px; line-height: 25px; color: var(--semantic-text-secondary); }
  .tr-node { fill: var(--semantic-background-elevated); stroke: var(--semantic-border-primary-hover); stroke-width: 1.5; }
  .tr-root { fill: var(--semantic-background-secondary); stroke: var(--semantic-text-primary); stroke-width: 1.5; }
  .tr-n { font-size: 13px; font-weight: 500; fill: var(--semantic-text-primary); text-anchor: middle; }
  .tr-user { font-size: 15px; font-weight: 600; fill: var(--semantic-text-primary); }
  .tr-op { font-size: 14px; font-weight: 600; fill: var(--semantic-text-accent); }
  .tr-go { fill: none; stroke: var(--semantic-text-accent); stroke-width: 2; }
  .tr-sb { fill: none; stroke: var(--semantic-text-accent); stroke-width: 1.5; }
  .tr-sbt { font-size: 13px; font-weight: 500; fill: var(--semantic-text-accent); }
  .tr-gone { opacity: .45; }
  .tr-dash { stroke-dasharray: 5 5; }
  .ch-trace pre.code { font-size: 13px; line-height: 20px; padding: 14px 18px; white-space: pre; overflow: hidden; }
  a.ch-docs { display: inline-block; font-family: var(--font-mono); font-size: 12px; line-height: 16px; color: var(--semantic-text-tertiary); text-decoration: none; border-bottom: 1px solid var(--semantic-border-primary-hover); }
  a.ch-docs:hover { color: var(--semantic-text-accent); }
  .ch-feat a.ch-docs { margin-top: 5px; }
  .ch-margin .note a.ch-docs { display: table; margin-top: 1px; }
  .ch-margin .note code { font-family: var(--font-mono); font-size: 15px; letter-spacing: 0; color: inherit; background: none; border: 0; padding: 0; }
  .ch-margin { position: relative; align-self: stretch; }
  .ch-margin svg { position: absolute; left: 0; top: 0; width: 44px; height: 100%; overflow: visible; }
  .ch-margin path { stroke: var(--semantic-text-accent); stroke-width: 2.6; fill: none; stroke-linecap: round; }
  .ch-margin .note { position: absolute; left: 46px; right: 0; font-family: AnnotationHand, cursive; font-size: 21px; line-height: 23px; color: var(--semantic-text-accent); }
  .ch-hidden { display: grid; grid-template-columns: 1.4fr .6fr; gap: 22px; }
  .ch-hidden pre.code { font-size: 13px; line-height: 22px; padding: 12px 16px; white-space: pre-wrap; }
  .ch-hidden ul { margin: 0; padding-left: 20px; font-size: 16px; line-height: 25px; }
  table.ch-table { border-collapse: collapse; width: 100%; font-size: 17px; line-height: 24px; color: var(--semantic-text-primary); }
  .ch-table th { text-align: left; font-size: 12px; letter-spacing: .08em; text-transform: uppercase; font-weight: 600; color: var(--semantic-text-accent); padding: 0 14px 8px 0; }
  .ch-table td { padding: 9px 14px 9px 0; border-top: 1px solid var(--semantic-border-secondary); vertical-align: top; }
  .ch-table td:first-child { font-family: var(--font-mono); font-size: 15px; white-space: nowrap; color: var(--semantic-text-primary); }
  .ch-table.wide td:first-child { font-family: var(--font-sans); white-space: normal; width: 24%; }
  .ch-table td { color: var(--semantic-text-secondary); font-size: 15.5px; }
"""


def git(*args) -> str:
    done = subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True)
    if done.returncode:
        raise SystemExit("slides/chapters.py: git %s: %s" % (" ".join(args), done.stderr.strip()))
    return done.stdout


def ref(branch: str) -> str:
    """The chapter branch as this repository has it: its own, or the one it was cloned from."""
    local = subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", "--verify", "--quiet", "refs/heads/" + branch], capture_output=True
    )
    return branch if local.returncode == 0 else "origin/" + branch


def kicker(ch) -> str:
    step = " · step %d of %d" % ch["at"] if "at" in ch else ""
    return "Chapter %d%s%s" % (ch["n"], " · optional" if ch.get("optional") else "", step)


# ---------- shell commands and screenshots ----------
def _words(command: str, first=True) -> str:
    """A command line, coloured by the role of each word. `first`: whether it opens with the command's name."""
    out = []
    for word in re.findall(r"\s+|\"[^\"]*\"|'[^']*'|\S+", command):
        text = html.escape(word)
        if not word.strip():
            out.append(text)
        elif word in ("&&", "|", ">", ";"):
            out.append('<span class="sh-op">%s</span>' % text)
            first = True
        elif word[0] in "\"'":
            out.append('<span class="sh-str">%s</span>' % text)
        elif word.startswith("-") and len(word) > 1:
            out.append('<span class="sh-flag">%s</span>' % text)
        elif word.startswith("$") or re.fullmatch(r"[A-Z_]+=.*", word):
            out.append('<span class="sh-var">%s</span>' % text)
        elif first:
            out.append('<span class="sh-cmd">%s</span>' % text)
            first = False
        else:
            out.append('<span class="sh-sub">%s</span>' % text)
    return "".join(out)


def shell(script: str) -> str:
    """A terminal session as HTML: `$ ` lines are commands, `> ` lines are typed at the app's prompt, the
    rest is output. What follows two spaces and a # is a comment. A command that ends with a backslash
    goes on in the next line."""
    out, goes_on = [], False
    for line in script.split("\n"):
        cut = re.search(r"(^|\s{2,})#", line)
        code, comment = (line[: cut.start(0) + len(cut.group(1))], line[cut.end(0) - 1 :]) if cut else (line, "")
        if goes_on:
            marked = _words(code, first=False)
        elif code.startswith("$ "):
            marked = '<span class="sh-p">$</span> ' + _words(code[2:])
        elif code.startswith(">"):
            marked = '<span class="sh-p">&gt;</span><span class="sh-m">%s</span>' % html.escape(code[1:])
        else:
            marked = '<span class="sh-o">%s</span>' % html.escape(code)
        goes_on = (goes_on or code.startswith("$ ")) and code.rstrip().endswith("\\")
        out.append(marked + ('<span class="sh-c">%s</span>' % html.escape(comment) if comment else ""))
    return "\n".join(out)


def shot(name: str, caption: str, *, show_caption: bool = True) -> str:
    """A screenshot from slides/assets/shots, or a dashed placeholder that says which file is missing."""
    path = SHOTS / (name + ".png")
    if path.exists():
        data = base64.b64encode(path.read_bytes()).decode("ascii")
        return '<figure class="ch-shot"><img src="data:image/png;base64,%s" alt="%s">%s</figure>' % (
            data,
            html.escape(caption),
            "<figcaption>%s</figcaption>" % html.escape(caption) if show_caption else "",
        )
    return (
        '<figure class="ch-shot todo"><div class="hole"><span>screenshot to add</span><b>%s</b>'
        "<code>slides/assets/shots/%s.png</code></div></figure>"
    ) % (html.escape(caption), name)


# ---------- what the check says, for the speaker ----------
def check_of(ch) -> dict:
    """The chapter's check, from its branch: the script, the prose, the goal, and the recorded verdicts."""
    doc = ast.get_docstring(ast.parse(git("show", "%s:checks/%s.py" % (ref(ch["branch"]), ch["check"]))))
    blocks = doc.split("\n\n")
    at = next(k for k, b in enumerate(blocks) if b.startswith("The script:"))
    script = [b for b in blocks[at + 1 :] if b.startswith("    ")]
    after = [b for b in blocks[at + 1 :] if not b.startswith("    ")]
    done = next((b for b in after if b.startswith("Done when")), "")
    recorded = git("show", "%s:checks/outputs/%s.txt" % (ref(ch["branch"]), ch["check"])).split("\n")
    return dict(
        script="\n\n".join("\n".join(line[4:] for line in b.split("\n")) for b in script),
        prose=[" ".join(b.split()) for b in after if b is not done],
        done=" ".join(done.split()),
        goals=[(line[:2] == "ok", line[5:].strip()) for line in recorded if line.startswith(("ok   ", "FAIL "))],
    )


def speaker(ch, check) -> str:
    """Speaker notes for the end of a chapter: what to run, and what should be seen."""
    return "<p>By hand, on %s:</p><pre>%s</pre><p>%s</p>" % (
        ch["branch"],
        html.escape(check["script"]),
        html.escape(check["done"]),
    )


# ---------- the code a chapter adds ----------
def changes(prev, ch, context=2) -> dict:
    """The code the chapter adds, per file, as rows of (kind, text): hunk, ctx, add, del. `context` is how
    many unchanged lines come with each change.

    Module docstrings are left out, changed or new: the slides around the code say what a file is.
    """
    if prev is None:  # the first chapter: its file as it is
        source = git("show", "%s:%s" % (ref(ch["branch"]), VIBECODE)).rstrip().split("\n")
        return {VIBECODE: [("ctx", line) for line in source[docstring_end(ch, VIBECODE) :]]}
    files, rows, at, skip = {}, [], 0, 0
    diff = git("diff", "--no-color", "-U%d" % context, ref(prev["branch"]), ref(ch["branch"]), "--", "code")
    for line in diff.split("\n"):
        if line.startswith("diff --git"):
            path = line.split(" b/")[-1]
            rows = files.setdefault(path, [])
            skip = docstring_end(ch, path)
        elif line.startswith(("index ", "--- ", "+++ ", "new file", "\\")) or not line:
            continue
        elif line.startswith("@@"):
            at = int(line.split("+")[1].split(",")[0].split(" ")[0])  # the hunk's first line in the new file
            rows.append(("hunk", "⋯"))
        else:
            if at > skip:
                rows.append(({"+": "add", "-": "del"}.get(line[0], "ctx"), line[1:]))
            at += line[0] != "-"
    return files


def function_of(source: list, name: str) -> list:
    """The lines of a top-level function, without the blank lines after it."""
    start = next(i for i, line in enumerate(source) if line.startswith("def %s(" % name))
    end = next((i for i in range(start + 1, len(source)) if source[i] and not source[i][0].isspace()), len(source))
    lines = source[start:end]
    while lines and not lines[-1].strip():
        lines.pop()
    return lines


def moved(prev, ch, name) -> list:
    """One function as rows of a diff, the step before against this one: everything that left it is a
    removed line, where git's own diff would call most of it unchanged because it now lives elsewhere."""
    old, new = (function_of(git("show", "%s:%s" % (ref(c["branch"]), VIBECODE)).split("\n"), name) for c in (prev, ch))
    rows = []
    for op, a1, a2, b1, b2 in difflib.SequenceMatcher(
        lambda line: not line.strip(), old, new, autojunk=False
    ).get_opcodes():
        if op == "equal":
            rows += [("ctx", line) for line in old[a1:a2]]
        else:
            rows += [("del", line) for line in old[a1:a2]] + [("add", line) for line in new[b1:b2]]
    return rows


def docstring_end(ch, path) -> int:
    """How many lines of the file, as the chapter leaves it, are its module docstring and the blank after it."""
    if not path.endswith(".py"):
        return 0
    first = ast.parse(git("show", "%s:%s" % (ref(ch["branch"]), path))).body[0]
    is_docstring = isinstance(first, ast.Expr) and isinstance(getattr(first, "value", None), ast.Constant)
    return first.end_lineno + 1 if is_docstring else 0


def has(row, key) -> bool:
    """Whether a row is the one a key names: "^x" is a line that is exactly x, anything else a piece of it."""
    if row[0] in ("hunk", "gap", "head"):
        return False
    return row[1].strip() == key[1:] if key.startswith("^") else key in row[1]


def find(rows, key, start, what) -> int:
    for k in range(start, len(rows)):
        if has(rows[k], key):
            return k
    raise SystemExit("slides/chapters.py: %s: no line with %r in the chapter's code" % (what, key))


def shown(files, shot, what) -> list:
    """The rows a code slide shows: ranges in presentation order, with APART starting an independent block."""
    out, last = [], (None, -1)
    ranges = [part for part in shot["show"] if part not in (APART, SKIP)]
    several = len({part[0] if len(part) == 3 else VIBECODE for part in ranges}) > 1
    apart = skipped = False
    for part in shot["show"]:
        if part == APART:  # the next range gets a box of its own, even when only blank lines lie between
            apart = True
            continue
        if part == SKIP:  # lines left out inside one box: the ⋯ takes the kind and the indent of what follows
            skipped = True
            continue
        path, start, end = part if len(part) == 3 else (VIBECODE, *part)
        rows = files.get(path)
        if rows is None:
            raise SystemExit("slides/chapters.py: %s: the chapter does not change %s" % (what, path))
        end, extra = end if isinstance(end, tuple) else (end, 0)
        i = find(rows, start, last[1] + 1 if last[0] == path and not apart else 0, what)
        j = find(rows, end, i, what) + extra
        if skipped and last[0] == path:
            kind, text = rows[i]
            out.append((kind, text[: len(text) - len(text.lstrip())] + "⋯"))
        elif last[0] != path:
            out += [("file", path)] if several else []
        elif not apart and all(row == ("ctx", "") or row == ("add", "") for row in rows[last[1] + 1 : i]):
            out += rows[last[1] + 1 : i]  # only blank lines between two ranges: keep them
        elif out[-1][0] != "hunk":
            out.append(("hunk", "⋯"))
        out += rows[i : j + 1]
        last, apart, skipped = (path, j), False, False
    if len(out) > ROWS:
        raise SystemExit("slides/chapters.py: %s: %d lines, a slide holds %d" % (what, len(out), ROWS))
    return out


def lines_of(rows, lit=(), prose=False) -> str:
    """Rows as highlighted lines. Each run of code between two headings is highlighted as one piece. The
    rows in `lit` are the ones a Modal feature's note points at. Prose, such as Markdown, is not coloured
    as code."""
    out, run = [], []
    rows = [(kind + (" feat" if k in lit else ""), text) for k, (kind, text) in enumerate(rows)]

    def flush():
        if not run:
            return
        texts = [text for _, text in run]
        marked = [] if prose else hl("\n".join(texts)).split("\n")
        if len(marked) != len(texts):
            marked = [html.escape(t) for t in texts]
        for (kind, text), h in zip(run, marked):
            if text.strip() == "⋯":  # lines left out: not code, so not coloured as code
                h = html.escape(text)
            gutter = {"add": "+", "del": "-"}.get(kind.split()[0], " ")
            out.append('<span class="ln %s"><span class="g">%s </span>%s</span>' % (kind, gutter, h or " "))
        run.clear()

    for kind, text in rows:
        if kind.split()[0] in ("file", "hunk"):
            flush()
            out.append('<span class="ln %s">%s</span>' % (kind, html.escape(text)))
        else:
            run.append((kind, text))
    flush()
    return "".join(out)


# Anchors whose own words are too long for a label.
DOCS_NAMES = {
    "sandbox-exit-snapshots": "Exit Snapshots",
    "sandbox-snapshots": "Snapshots",
    "filesystem-snapshots": "Filesystem Snapshots",
    "directory-snapshots": "Directory Snapshots",
    "memory-snapshots": "Memory Snapshots",
    "connecting-to-sandboxes-with-http-and-websockets": "connecting to sandboxes",
    "running-a-sandbox-with-an-entrypoint": "sandbox with an entrypoint",
    "restricting-by-domain-name-domain-allowlist": "domain allowlist",
    "asgi-apps---fastapi-fasthtml-starlette": "ASGI apps",
    "unmounting-a-mounted-image": "unmounting an image",
}


def docs_link(page: str) -> str:
    """A link to a documentation page, named after the subsection it points at."""
    name = page.split("#")[-1]
    label = DOCS_NAMES.get(name, name.replace("-", " "))
    return '<a class="ch-docs" href="%s%s" target="_blank" rel="noopener">docs: %s ↗</a>' % (DOCS, page, label)


def example_link(page: str, label: str) -> str:
    """A link to one of Modal's examples."""
    return '<a class="ch-docs" href="%s%s" target="_blank" rel="noopener">example: %s ↗</a>' % (
        DOCS.replace("/guide/", "/examples/"),
        page,
        label,
    )


def placed(rows, notes, what) -> list:
    """Where each note goes: the rows it is about, its text, and its docs page when it names a Modal feature."""
    out = []
    for first, last, text, *docs in notes:
        i = find(rows, first, 0, what)
        j = find(rows, last, i, what) if last else i
        out.append(dict(i=i, j=j, text=text, docs=docs[0] if docs else ""))
    return sorted(out, key=lambda note: (note["i"], note["j"]))


def margin(notes, rows=0) -> str:
    """The notes beside the code, in handwriting: a stroke along the lines a note is about, and for a Modal
    feature an arrow at them and a link to its documentation. `rows` is how many lines the code beside them
    takes: notes that would run past its end are moved up, closer together."""
    placed_at, floor = [], 0
    for note in notes:
        top, bottom = PAD + note["i"] * LINE, PAD + (note["j"] + 1) * LINE
        text_height = NOTE_LINE * -(-len(note["text"]) // NOTE_CHARS)
        height = text_height + (18 if note["docs"] else 0)
        y = max((top + bottom) / 2 - height / 2, floor)
        floor = y + height + NOTE_GAP
        placed_at.append([y, height, text_height])
    end = 2 * PAD + rows * LINE + NOTE_LINE if rows else None  # a little below the code's last line
    for spot in reversed(placed_at):
        if end is None:
            break
        spot[0] = max(0, min(spot[0], end - spot[1]))
        end = spot[0] - 9
    strokes, labels = [], []
    for note, (y, height, text_height) in zip(notes, placed_at):
        top, bottom = PAD + note["i"] * LINE, PAD + (note["j"] + 1) * LINE
        middle = (top + bottom) / 2
        a, b, at = top + 3, bottom - 3, y + min(text_height, NOTE_LINE * 2) / 2
        if note["j"] > note["i"] or not note["docs"]:
            strokes.append(
                '<path d="M11 %.1f C6 %.1f 15 %.1f 10 %.1f"/>' % (a, a + (b - a) / 3, a + 2 * (b - a) / 3, b)
            )
        if note["docs"]:  # an arrow, its head at the code
            strokes.append('<path d="M40 %.1f Q28 %.1f 15 %.1f"/>' % (at, middle, middle))
            strokes.append('<path d="M15 %.1f L24 %.1f M15 %.1f L25 %.1f"/>' % (middle, middle - 6, middle, middle + 5))
        else:
            strokes.append('<path d="M14 %.1f Q28 %.1f 40 %.1f"/>' % (middle, middle, at))
        link = docs_link(note["docs"]) if note["docs"] else ""
        # a name such as AUTHORIZATION_BEARER is too wide for the margin in handwriting: it is set as code
        text = re.sub(r"\b[A-Z][A-Z0-9]*_[A-Z0-9_]+\b", r"<code>\g<0></code>", html.escape(note["text"]))
        labels.append('<div class="note" style="top:%.1fpx">%s%s</div>' % (y, text, link))
    return '<div class="ch-margin"><svg>%s</svg>%s</div>' % ("".join(strokes), "".join(labels))


# ---------- the slides of a chapter ----------
def why(ch) -> str:
    """The chapter's first slide: what hurts, or where we are, on the left; what we build on the right."""

    def column(cls, head, items):
        return '<div class="col %s"><h3>%s</h3><ul>%s</ul></div>' % (
            cls,
            head,
            "".join(
                "<li>%s</li>" % html.escape(item)
                if isinstance(item, str)
                else '<li class="%s">%s</li>' % (item[0], html.escape(item[1]))
                for item in items
            ),
        )

    body = '<div class="ch-why">%s%s</div>' % (
        column("now", "Where we are", ch["state"]) if "state" in ch else column("bad", "Problems", ch["problems"]),
        column("good fragment", "What we'll build", ch["wants"]),  # appears on the next key press
    )
    return slide(body, kicker(ch), ch["title"], foot="git checkout %s" % ch["branch"])


def design(ch, diagram, annotate) -> str:
    return slide(annotate(diagram(ch["n"]), ch["n"]), kicker(ch), ch["design"], foot="green: what this chapter adds")


def design_so_far(step, diagram, annotate) -> str:
    """A step's own picture: the application as it stands after the step, with the callouts so far."""
    at = step["at"][0]
    drawn = annotate(diagram(round(step["n"] + at / 10, 1)), step["n"], at)
    return slide(drawn, kicker(step), step["step"], foot="green: what this step adds")


def sample(code: str) -> str:
    """A feature's line of code: a command, an address or header shown as it is, or Python."""
    if code.startswith(("modal ", "export ", "rsync ")):
        return shell("$ " + code)
    if code.startswith(("http", "Authorization")):
        return html.escape(code)
    return hl(code)


def features(ch) -> str:
    """The Modal features of a chapter, one row each: what it is, then its line of code, never wrapped."""
    rows = "".join(
        '<div class="card"><div><h3>%s</h3><p>%s</p></div><div>%s%s</div></div>'
        % (
            html.escape(name),
            html.escape(text),
            '<pre class="code">%s</pre>' % sample(code) if code else "",
            docs_link(FEATURE_DOCS[name]) if name in FEATURE_DOCS else "",
        )
        for name, code, text in ch["features"]
    )
    return slide('<div class="ch-feat">%s</div>' % rows, kicker(ch), ch["features_title"])


def drawing(kind: str) -> str:
    """One way to keep a key from the agent, as a small picture: who holds the key is drawn in accent."""

    def box(x, w, label, cls="vc-box"):
        return (
            '<rect class="%s" x="%d" y="70" width="%d" height="44" rx="8"/><text class="vc-t" x="%d" y="97">%s</text>'
            % (
                cls,
                x,
                w,
                x + 12,
                label,
            )
        )

    def arrow(x1, x2):
        return '<line class="vc-a" x1="%d" y1="92" x2="%d" y2="92" marker-end="url(#vc-head)"/>' % (x1, x2)

    def above(x, label):
        return '<text class="vc-s" x="%d" y="60">%s</text>' % (x, label)

    def network(x1, x2, label=""):
        """A stretch of network the option leans on, in accent, with its name under it."""
        name = '<text class="vc-s" x="%d" y="130" text-anchor="middle" style="font-size:12px">%s</text>'
        return (
            '<g class="vc-new"><line class="vc-a" x1="%d" y1="92" x2="%d" y2="92" marker-end="url(#vc-head-new)"/>%s</g>'
            % (
                x1,
                x2,
                name % ((x1 + x2) // 2 + 11, label) if label else "",
            )
        )

    frame = '<rect class="vc-sb" x="6" y="26" width="%d" height="112" rx="12"/><text class="vc-s" x="18" y="46">Sandbox</text>'
    parts = {
        "policy": frame % 150
        + box(26, 110, "agent")
        + above(190, "outbound network")  # Modal's proxy sits on the Sandbox's way out
        + box(188, 92, "+ key", "vc-side")
        + box(308, 66, "API")
        + network(136, 186)
        + network(280, 306),
        # A Sidecar is a container of its own, beside the Sandbox's main one: the two share a host, and a
        # bridge network joins them.
        "sidecar": '<rect class="vc-state" x="2" y="4" width="304" height="142" rx="14" stroke-dasharray="5 4"/>'
        + '<text class="vc-s" x="14" y="20">same host</text>'
        + '<rect class="vc-sb" x="12" y="28" width="100" height="108" rx="12"/><text class="vc-s" x="24" y="48">Sandbox</text>'
        + box(20, 84, "agent")
        + above(198, "Sidecar")
        + box(196, 104, "proxy + key", "vc-side")
        + box(324, 52, "API")
        + network(104, 194, "bridge network")
        + arrow(300, 322),
        "mcp": frame % 150
        + box(26, 110, "agent")
        + above(190, "MCP server")
        + box(188, 100, "tool + key", "vc-side")
        + box(312, 62, "API")
        + arrow(136, 186)
        + arrow(288, 310),
    }
    head = (
        '<defs><marker id="vc-head" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" '
        'orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z" class="vc-head"/></marker>'
        '<marker id="vc-head-new" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" '
        'orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z" class="vc-head-new"/></marker></defs>'
    )
    if kind in parts:
        return own_markers(
            '<svg viewBox="0 0 380 150" role="img" aria-label="%s">%s%s</svg>' % (kind, head, parts[kind])
        )
    return own_markers(kept(kind, head))


def kept(kind: str, head: str) -> str:
    """What a kind of Snapshot keeps, or how a Sandbox is put together from one."""

    def bar(x, y, w, label, on):
        return (
            '<rect class="%s" x="%d" y="%d" width="%d" height="28" rx="6"/><text class="%s" x="%d" y="%d">%s</text>'
            % (
                "kp-on" if on else "kp-off",
                x,
                y,
                w,
                "kp-on-t" if on else "kp-off-t",
                x + 10,
                y + 19,
                label,
            )
        )

    def frame(x, y, w, h, label):
        return (
            '<rect class="vc-sb" x="%d" y="%d" width="%d" height="%d" rx="10"/><text class="vc-s" x="%d" y="%d">%s</text>'
            % (
                x,
                y,
                w,
                h,
                x + 10,
                y + 18,
                label,
            )
        )

    def arrow(x1, y1, x2, y2, cls="vc-a"):
        return '<line class="%s" x1="%d" y1="%d" x2="%d" y2="%d" marker-end="url(#vc-head)"/>' % (cls, x1, y1, x2, y2)

    if kind.startswith("keep-"):  # a Sandbox as three layers; the ones the Snapshot keeps are lit
        lit = {"keep-dir": {2}, "keep-fs": {1, 2}, "keep-memory": {0, 1, 2}}[kind]
        layers = ["running processes", "system, packages, agent", "/project"]
        body = frame(4, 4, 252, 132, "Sandbox") + "".join(
            bar(14, 30 + 34 * k, 232, label, k in lit) for k, label in enumerate(layers)
        )
        return '<svg viewBox="0 0 260 140" role="img" aria-label="%s">%s%s</svg>' % (kind, head, body)
    if kind == "whole":  # base and project fused in one Image; a newer base does not reach it
        body = (
            frame(150, 6, 190, 96, "alice's Snapshot")
            + bar(160, 30, 170, "base v1", True)
            + bar(160, 62, 170, "her project", True)
            + arrow(342, 54, 398, 54)
            + '<rect class="tr-sb" x="400" y="39" width="136" height="30" rx="15"/><text class="tr-sbt" x="414" y="59">Sandbox alice</text>'
            + bar(10, 126, 130, "base v2, newer", False)
            + arrow(142, 140, 226, 110, "vc-a tr-dash")
            + '<text class="kp-no" x="236" y="132">✗ does not reach her</text>'
        )
        return '<svg viewBox="0 0 540 160" role="img" aria-label="%s">%s%s</svg>' % (kind, head, body)
    body = (  # one base for everyone, each project mounted into its Sandbox
        bar(205, 4, 130, "base v2, newer", False)
        + arrow(240, 34, 150, 62)
        + arrow(300, 34, 390, 62)
        + frame(40, 64, 220, 92, "Sandbox alice")
        + bar(50, 88, 200, "base v2", False)
        + bar(50, 120, 200, "alice's project, mounted", True)
        + frame(280, 64, 220, 92, "Sandbox bob")
        + bar(290, 88, 200, "base v2", False)
        + bar(290, 120, 200, "bob's project, mounted", True)
    )
    return '<svg viewBox="0 0 540 160" role="img" aria-label="%s">%s%s</svg>' % (kind, head, body)


def cards(ch, title, options, hidden=False) -> str:
    """Options side by side, each with a drawing: ways to build something, or kinds of a thing."""

    def marks(option):
        items = [("good", line) for line in option.get("good", [])] + [("bad", line) for line in option.get("bad", [])]
        return (
            "<ul>%s</ul>" % "".join('<li class="%s">%s</li>' % (cls, html.escape(line)) for cls, line in items)
            if items
            else ""
        )

    body = "".join(
        '<div class="card%s"><h3>%s%s</h3>%s%s%s%s</div>'
        % (
            " chosen" if option.get("chosen") or option.get("tag") else "",
            html.escape(option["name"]),
            "<span>%s</span>" % html.escape(option.get("tag") or "what we build")
            if option.get("chosen") or option.get("tag")
            else "",
            drawing(option["drawing"]),
            "".join("<p>%s</p>" % html.escape(line) for line in option["lines"]),
            marks(option),
            (docs_link(option["docs"]) if option.get("docs") else "")
            + (example_link(*option["example"]) if option.get("example") else ""),
        )
        for option in options
    )
    return slide(
        '<div class="ch-opts%s" style="--cols:%d">%s</div>' % (" many" if len(options) > 3 else "", len(options), body),
        kicker(ch),
        title,
        hidden=hidden,
    )


_drawings = iter(range(1, 10_000))


def own_markers(svg: str) -> str:
    """Give a drawing arrowhead markers of its own. A marker that lives in a slide which is not shown does
    not draw, so drawings must not share ids."""
    n = next(_drawings)
    for name in ("vc-head-new", "vc-head"):
        svg = svg.replace('id="%s"' % name, 'id="%s-%d"' % (name, n)).replace(
            "url(#%s)" % name, "url(#%s-%d)" % (name, n)
        )
    return svg


def tree() -> str:
    """The states of three users as a tree rooted at the template: messages grow it, undo and fork start
    a Sandbox from a state that is already in it."""
    o = [
        '<defs><marker id="vc-head" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" '
        'orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z" class="vc-head"/></marker>'
        '<marker id="vc-head-new" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
        'orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z" class="vc-head-new"/></marker></defs>'
    ]

    def node(x, y, label, cls="tr-node"):
        o.append(
            '<circle class="%s" cx="%d" cy="%d" r="16"/><text class="tr-n" x="%d" y="%d">%s</text>'
            % (cls, x, y, x, y + 5, label)
        )

    def edge(x1, y1, x2, y2, label="", cls="vc-a", at=None):
        o.append(
            '<line class="%s" x1="%d" y1="%d" x2="%d" y2="%d" marker-end="url(#vc-head)"/>' % (cls, x1, y1, x2, y2)
        )
        if label:
            x, y = at or ((x1 + x2) // 2, (y1 + y2) // 2 - 8)
            o.append('<text class="vc-s" x="%d" y="%d" text-anchor="middle">%s</text>' % (x, y, label))

    def say(x, y, text, cls="vc-s"):
        o.append('<text class="%s" x="%d" y="%d">%s</text>' % (cls, x, y, html.escape(text)))

    def sandbox(x, y, w, name):
        o.append('<rect class="tr-sb" x="%d" y="%d" width="%d" height="30" rx="15"/>' % (x, y, w))
        say(x + 14, y + 20, "Sandbox " + name, "tr-sbt")

    # the root
    node(140, 225, "0", "tr-root")
    say(62, 262, "the template", "tr-user")
    say(62, 280, "base Image, the root")
    # alice: three messages, an undo, then another message
    say(292, 172, "alice", "tr-user")
    edge(155, 218, 295, 137, "message 1", at=(196, 160))
    node(310, 130, "1")
    edge(326, 130, 464, 130, "message 2")
    node(480, 130, "2")
    o.append('<g class="tr-gone">')
    edge(496, 130, 634, 130, "message 3", at=(572, 148))
    node(650, 130, "3")
    o.append("</g>")
    say(680, 134, "dropped from her list")
    o.append('<path class="tr-go" d="M646 114 Q565 80 486 113" marker-end="url(#vc-head-new)"/>')
    say(520, 84, "undo: start from the parent", "tr-op")
    edge(494, 138, 636, 198, "a new message 3", at=(536, 198))
    node(650, 205, "3′")
    sandbox(680, 190, 150, "alice")
    # carol: a fork of alice's first state
    o.append('<path class="tr-go" d="M322 119 L466 57" marker-end="url(#vc-head-new)"/>')
    node(480, 50, "1")
    say(462, 24, "carol", "tr-user")
    sandbox(508, 35, 150, "carol")
    say(672, 55, "fork: started from alice's state 1", "tr-op")
    # bob: two messages, then asleep
    say(296, 362, "bob", "tr-user")
    edge(155, 232, 295, 313, "message 1", at=(190, 302))
    node(310, 320, "1")
    edge(326, 320, 464, 320, "message 2")
    node(480, 320, "2")
    edge(496, 320, 634, 320, "it sleeps", cls="vc-a tr-dash")
    node(650, 320, "z")
    say(680, 317, "where bob left off: an Exit Snapshot")
    say(680, 335, "wake: start from it", "tr-op")
    # legend
    o.append('<circle class="tr-node" cx="72" cy="392" r="8"/>')
    say(88, 396, "a state, kept as an Image")
    o.append('<rect class="tr-sb" x="330" y="381" width="56" height="22" rx="11"/>')
    say(396, 396, "a running Sandbox, started from the state it sits on")
    o.append('<line class="vc-a" x1="800" y1="392" x2="840" y2="392" marker-end="url(#vc-head)"/>')
    say(850, 396, "a message makes the next state")
    return own_markers(
        '<svg viewBox="0 0 1160 410" role="img" aria-label="The states of three users as a tree. The template is '
        "the root. alice sent three messages, undid the third and sent another. carol forked alice's first state. "
        'bob sent two messages and his Sandbox went to sleep.">%s</svg>' % "".join(o)
    )


def picture(ch) -> str:
    lines = "".join("<li>%s</li>" % html.escape(line) for line in ch["picture"]["lines"])
    return slide('<div class="ch-tree">%s<ul>%s</ul></div>' % (tree(), lines), kicker(ch), ch["picture"]["title"])


TRACE_ROWS = 25  # lines a trace slide holds
TRACE_WIDTH = 132  # characters across it


# The checks play users of their own. A slide shows the users the audience types: alice, and bob beside her.
CAST = (("check-fork", "bob"), ("check-2", "bob"), ("linkcheck", "alice"), ("check", "alice"))


def trace(ch, check, notes="") -> str:
    """How the chapter looks when tried by hand: the recorded run, without the agent's diffs."""
    recorded = git("show", "%s:checks/outputs/%s.txt" % (ref(ch["branch"]), ch["check"]))
    for played, shown in CAST:
        recorded = re.sub(r"\b%s\b" % re.escape(played), shown, recorded)
    recorded = recorded.split("\n")
    if "seen_from" in ch:  # the run as recorded opens with steps an earlier slide has shown
        first = next(i for i, line in enumerate(recorded) if line.startswith(ch["seen_from"]))
        recorded = recorded[first:]
    kept = []
    for line in recorded:
        if line.startswith("      "):  # what the check noted for itself: not something typed or printed
            continue
        if not line.strip() or line.startswith(("ok   ", "FAIL ", "> build ·")):
            continue
        if line.startswith(("Index:", "====", "--- ", "+++ ", "@@", "+", "-", " ", "Wrote file")):
            continue
        kept.append(line if len(line) <= TRACE_WIDTH else line[: TRACE_WIDTH - 1] + "…")
    if len(kept) > TRACE_ROWS:
        kept = kept[: TRACE_ROWS - 1] + ["…"]
    body = '<div class="ch-trace"><pre class="code">%s</pre></div>' % shell("\n".join(kept))
    return slide(body, kicker(ch), ch["seen"], foot="git checkout %s" % ch["branch"], notes=notes)


def picture_of(name: str, cls: str) -> str:
    """An image from slides/assets/shots, or nothing when that file is not there."""
    path = SHOTS / (name + ".png")
    if not path.exists():
        return ""
    return '<img class="%s" src="data:image/png;base64,%s" alt="">' % (
        cls,
        base64.b64encode(path.read_bytes()).decode("ascii"),
    )


def typed(ch, step, credits=False, notes="") -> str:
    """A step: what is typed, beside a screenshot when it has one. With credits, the QR code of
    the credits offer sits in the corner, for whoever has not scanned it yet."""
    if "picture" in step:
        body = '<div class="ch-picture">%s</div>' % (picture_of(step["picture"], "") or shot(step["picture"], ""))
        return slide(body, kicker(ch), step["title"], foot=step["foot"])
    shown = step.get("shot")
    boxes = step["commands"] if isinstance(step["commands"], list) else [step["commands"]]
    body = '<div class="ch-steps%s"><div class="ch-blocks">%s</div>%s</div>' % (
        (" wide" if step.get("wide") else "") if shown else " alone",
        "".join('<pre class="code">%s</pre>' % shell(box) for box in boxes),
        shot(*shown) if shown else "",
    )
    if credits:
        body += picture_of("credits-qr", "ch-credits")
    foot = step.get("foot") or ("command line, or the dashboard: %s" % shown[1] if shown else "")
    return slide(body, kicker(ch), step["title"], step.get("sub", ""), foot=foot, notes=notes)


def enclosing(sources, block) -> str:
    """The def line of the function a box of code starts inside, or nothing: when the box starts at the top
    level, when it shows that def line itself, or when its lines are not found in any of the files."""
    kept = [text for kind, text in block if kind in ("ctx", "add")]
    first = next((k for k, text in enumerate(kept) if text.strip()), None)
    if first is None or not kept[first].startswith(" "):
        return ""
    lines = kept[first:]
    while lines and not lines[-1].strip():
        lines.pop()
    for source in sources:
        for k in range(len(source) - len(lines) + 1):
            if source[k : k + len(lines)] != lines:  # the whole box: two functions may open with the same lines
                continue
            within = len(lines[0]) - len(lines[0].lstrip())
            for line in reversed(source[:k]):  # outwards, block by block, until a def or the top level
                indent = len(line) - len(line.lstrip())
                if not line.strip() or indent >= within:
                    continue
                if line.lstrip().startswith(("def ", "async def ")):
                    return line
                within = indent
            return ""
    return ""


TOO_TALL = []  # code slides that have no room for a def line on top of their boxes: they get the label


def in_blocks(rows, what, sources=()) -> tuple:
    """The rows of a code slide as blocks, one box each, split where lines are skipped. A block whose lines
    are all new is shown as code, without diff marks, and only the lines its notes point at are lit. A block
    that changes code that was there is a diff: every added line is green, and none is lit. Returns the
    blocks, each with the place of its first row and whether it is all new, and the rows as they are laid
    out: the space between two boxes takes BLOCK_GAP rows. With sources, a box that starts inside a function
    opens with that function's def line and a ⋯, when the slide has the room."""

    def lay(heads):
        blocks, laid, block, apart = [], [], [], False
        for row in rows + [("hunk", "")]:
            if row[0] != "hunk":
                block.append(row)
                continue
            if block:
                kinds = {kind for kind, _ in block if kind != "file"}
                new = kinds <= {"add"} or kinds <= {"ctx"}  # all new, or the code as it stands: no diff to show
                block = [("ctx" if new and kind == "add" else kind, text) for kind, text in block]
                head = enclosing(sources, block) if heads else ""
                if head:
                    body = next(text for kind, text in block if kind in ("ctx", "add") and text.strip())
                    dots = " " * (2 + len(body) - len(body.lstrip())) + "⋯"  # under the gutter, at the body's indent
                    top = [row for row in block if row[0] == "file"]
                    block = top + [("head", head), ("hunk", dots)] + block[len(top) :]
                laid += [("gap", "")] * BLOCK_GAP if apart else []
                blocks.append((len(laid), block, new))
                laid += block
                block, apart = [], True
        return blocks, laid

    blocks, laid = lay(bool(sources))
    if sources and len(laid) > ROWS:
        TOO_TALL.append(what)
        blocks, laid = lay(False)
    if len(laid) > ROWS:
        raise SystemExit("slides/chapters.py: %s: %d lines with its breaks, a slide holds %d" % (what, len(laid), ROWS))
    return blocks, laid


def code(prev, ch, notes="") -> list:
    files = changes(prev, ch)
    foot = VIBECODE if prev is None else "git diff %s %s -- code" % (prev["branch"], ch["branch"])
    out = []
    for k, part in enumerate(ch["code"], 1):
        what = "%s, code slide %d" % (ch["branch"], k)
        here = changes(prev, ch, part["context"]) if "context" in part and prev is not None else files
        if part.get("whole"):  # the code as this step leaves it, where a diff would read badly
            here = changes(None, ch)
        if part.get("moved"):  # first that function, before and after, then the code as it stands
            here = dict(
                files, **{VIBECODE: moved(prev, ch, part["moved"]) + [("hunk", "⋯")] + changes(None, ch)[VIBECODE]}
            )
        paths = {shot[0] if len(shot) == 3 else VIBECODE for shot in part["show"] if shot != APART}
        sources = [
            git("show", "%s:%s" % (ref(ch["branch"]), path)).split("\n")
            for path in sorted(paths)
            if FUNCTION and path.endswith(".py")
        ]
        blocks, rows = in_blocks(shown(here, part, what), what, sources if FUNCTION == "def" else ())
        notes_here = placed(rows, part["notes"], what)
        lit = {k for note in notes_here if note["docs"] for k in range(note["i"], note["j"] + 1)}
        lit |= {find(rows, key, 0, what) for key in part.get("lit", [])}
        prose = all(len(shot) == 3 and shot[0].endswith(".md") for shot in part["show"])
        boxes = ""
        for at, block, new in blocks:  # a box whose function is not on its first line names it in its corner
            name = "" if any(kind == "head" for kind, _ in block) else enclosing(sources, block).strip()
            name = re.sub(r"^(async )?def ", "", name).rstrip(":")
            boxes += '<pre class="code"%s>%s</pre>' % (
                ' data-in="in %s"' % html.escape(name) if name else "",
                lines_of(block, {k - at for k in lit if new and at <= k < at + len(block)}, prose),
            )
        body = '<div class="ch-code"><div class="ch-blocks">%s</div>%s</div>' % (boxes, margin(notes_here, len(rows)))
        out.append(
            slide(
                body,
                kicker(ch),
                part["title"],
                part.get("sub", ""),
                foot=foot,
                notes=notes if k == len(ch["code"]) else "",
            )
        )
    return out


def chapter_parts(diagram, annotate) -> list:
    """One section of the deck per chapter: why, the ways to build it when there are several, the design,
    the features, what is typed, the code, and how it looks when tried by hand. The first chapter opens
    with the setup in place of a why. A chapter built in steps shows each step's picture, features, code and run."""
    out, prev = [], None
    for ch in CHAPTERS:
        check = check_of(ch)
        slides, claimed = [], False
        for step in ch.get("opens", []):  # the credits code sits in a corner once it has been shown large
            slides.append(typed(ch, step, credits=claimed))
            claimed = claimed or step.get("picture") == "credits"
        steps = ch.get("parts", [])
        if ch.get("problems") or ch.get("state"):
            slides.append(why(ch))
        if ch.get("options"):
            slides.append(cards(ch, ch["options_title"], ch["options"]))
        if ch.get("picture"):
            slides.append(picture(ch))
        if ch.get("design"):
            slides.append(design(ch, diagram, annotate))
        if ch.get("features") and not steps:
            slides.append(features(ch))
        slides += [
            cards(ch, c["title"], c["options"], c.get("hidden", False))
            for c in ch.get("compare", [])
            if not c.get("last")
        ]
        slides += [typed(ch, step) for step in ch.get("steps", [])]
        before = prev
        for k, part in enumerate(steps, 1):  # each step: its picture, its features, its code, how it looks
            part = dict(part, n=ch["n"], at=(k, len(steps) + 1))
            part_check = check_of(part)
            slides += [design_so_far(part, diagram, annotate)] if part.get("step") else []
            slides.append(features(part))
            slides += code(before, part)
            if "seen_as" in part:
                slides.append(typed(part, dict(part["seen_as"], title=part["seen"]), notes=speaker(part, part_check)))
            else:
                slides.append(trace(part, part_check, speaker(part, part_check)))
            slides += [typed(part, step) for step in part.get("tries", [])]
            before = part
        last = dict(ch, at=(len(steps) + 1, len(steps) + 1)) if steps else ch
        if steps and ch.get("last_step"):  # the last step has a branch of its own, the same commit as the chapter's
            last = dict(last, branch=ch["last_step"])
        if steps:
            slides += [design_so_far(last, diagram, annotate)] if ch.get("step") else []
            slides.append(features(last))
        if "seen_as" in ch:
            seen = typed(last, dict(ch["seen_as"], title=ch["seen"]), notes=speaker(ch, check))
        else:
            seen = trace(last, check, speaker(ch, check))
        if ch.get("seen_before_code"):
            slides.append(seen)
        slides += code(before, last)
        if not ch.get("seen_before_code"):
            slides.append(seen)
        slides += [
            cards(ch, c["title"], c["options"], c.get("hidden", False)) for c in ch.get("compare", []) if c.get("last")
        ]
        slides += [typed(last, step) for step in ch.get("tries", [])]
        out.append(
            dict(
                name="ch%d" % ch["n"],
                title=ch["title"],
                label="%d · %s" % (ch["n"], ch["title"]),
                opener=False,
                slides=slides,
            )
        )
        prev = ch
    return out
