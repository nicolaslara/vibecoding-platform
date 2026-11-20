# Chapter 3, step 3: the key, in the Sandbox

Branches `ch3.3-secret` and `ch3-agent`: two names for the same commit.
Before: `ch3.2-turn`. Next: `ch4-key-out`.

One line: the Secret `model-token` is attached to the Sandbox. It is the quick
way to hand the agent its key: `AUTHORIZATION_BEARER` becomes an environment
variable inside, which is where `opencode.json` reads the key. That is the end
of chapter 3, let an agent change the app: a message changes the app. The key
is now where the agent can read it. We take it back in the next chapter.

## Run it

```sh
cd code
uv run vibecode.py reset alice     # her Sandbox from step 2 has no key
uv run vibecode.py chat alice
> Change the heading in src/App.jsx to say exactly: Hello workshop
```

The agent prints its steps, `→ Read src/App.jsx` and `← Edit src/App.jsx`,
then a line that starts with `done`. The open tab shows the new heading.

Every terminal needs `ENDPOINT_URL`, from chapter 1. After checking out this
branch, reset the user first, so her Sandbox is one this branch made.

## Test it

```sh
uv run checks/ch3_agent.py     # from the repository root
```

Done when the agent's edit is in the project and the second message got an
answer.

## See what changed

```sh
git diff ch3.2-turn ch3-agent -- code
```
