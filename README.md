# Chapter 6, step 2: undo, a Sandbox from an earlier state

Branch `ch6.2-undo`. Before: `ch6.1-turns`. Next: `ch6.3-fork`.

A Snapshot is an Image, so a Sandbox starts from it like from any other.
Sandbox creation is extracted from `boot` into a function of its own, `start`,
for undo and fork. A new command, `undo`, restarts the user's Sandbox from the
state before the last message.

## Run it

```sh
cd code
uv run vibecode.py reset alice
uv run vibecode.py chat alice
> Change the heading in src/App.jsx to say exactly: First
> Change the heading in src/App.jsx to say exactly: Second
>
uv run vibecode.py undo alice     # new alice sb-…, turn 1, a new link
uv run vibecode.py undo alice     # turn 0: the template
uv run vibecode.py undo alice     # nothing to undo
```

`undo` takes back one message at a time, down to the template. After the first
`undo` the new link shows the heading `First`. Each `undo` is a new Sandbox,
so it prints a new link.

Every terminal needs `ENDPOINT_URL`, from chapter 1. After checking out this
branch, reset the user first, so her Sandbox is one this branch made.

## Test it

```sh
uv run checks/ch6_2_undo.py     # from the repository root
```

Done when each undo puts the project back as it was before one message.

## See what changed

```sh
git diff ch6.1-turns ch6.2-undo -- code
```
