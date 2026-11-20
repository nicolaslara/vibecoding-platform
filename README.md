# Chapter 3, step 1: the agent, in the Image

Branch `ch3.1-opencode`. Before: `ch2-serve`. Next: `ch3.2-turn`.

The agent, its config and the model's name are more layers of the same Image:
the coding agent OpenCode, and `code/opencode.json`, with our Model Endpoint
as its model and a key read from the environment variable
`AUTHORIZATION_BEARER`. The template gains `AGENTS.md`, which tells the agent
about the app. Nothing connects the agent to `chat` yet.

## Run it

```sh
cd code
uv run vibecode.py reset alice     # start a fresh Sandbox from the updated Image
uv run vibecode.py chat alice
modal shell sb-…                   # in a second terminal, with the Sandbox ID chat printed
cd /project/app                    # inside the Sandbox
opencode
```

OpenCode opens inside the Sandbox, in `/project/app`, and names our Model
Endpoint as its model. This tests the installed agent directly. The next step
connects it to `chat`. It has no key yet: a prompt typed there is refused
with `Error: Unauthorized: proxy auth required`. Step 3 gives it one. A Sandbox that is running keeps the Image it started
from, which is why the reset comes first.

Every terminal needs `ENDPOINT_URL`, from chapter 1. After checking out this
branch, reset the user first, so her Sandbox is one this branch made.

## Test it

```sh
uv run checks/ch3_1_opencode.py     # from the repository root
```

Done when the agent's command answers inside the Sandbox and its model is
ours.

## See what changed

```sh
git diff ch2-serve ch3.1-opencode -- code
```
