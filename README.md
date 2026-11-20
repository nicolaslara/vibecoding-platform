# Chapter 3, step 2: one turn of the agent per message

Branch `ch3.2-turn`. Before: `ch3.1-opencode`. Next: `ch3.3-secret`.

Every message now runs the agent once, with exec: a process beside the
entrypoint, in the user's Sandbox. `chat` prints its output in chunks as they
arrive. If the Sandbox went idle and ended between two messages, `chat` starts
it again. The model refuses the agent: no key yet. That is the planned end of
this step.

## Run it

```sh
cd code
uv run vibecode.py reset alice
uv run vibecode.py chat alice
> Change the heading in src/App.jsx to say exactly: Hello workshop
```

It prints `Error: Unauthorized: proxy auth required`, then `stopped rc=1`.

Every terminal needs `ENDPOINT_URL`, from chapter 1. After checking out this
branch, reset the user first, so her Sandbox is one this branch made.

## Test it

```sh
uv run checks/ch3_2_turn.py     # from the repository root
```

Done when the agent ran in the Sandbox and the model refused it for lack of a
key.

## See what changed

```sh
git diff ch3.1-opencode ch3.2-turn -- code
```
