# Chapter 6, step 3: fork, a Sandbox from someone else's state

Branches `ch6.3-fork` and `ch6-undo`: two names for the same commit.
Before: `ch6.2-undo`. Next: `ch7.1-http`.

A new command, `fork`, takes a Snapshot of one user's running Sandbox and
starts another user's Sandbox from it. The first keeps running. The copy gets
her list of turns too, so it can undo. That is the end of chapter 6, undo a
message and fork a project.

## Run it

```sh
cd code
uv run vibecode.py reset alice
uv run vibecode.py chat alice
> Change the heading in src/App.jsx to say exactly: Alice
>
uv run vibecode.py fork alice bob     # running alice sb-…, new bob sb-…, bob's link
uv run vibecode.py chat bob           # bob changes his copy
> Change the heading in src/App.jsx to say exactly: Bob
>
modal shell <bob's sb-…> -c 'grep h1 /project/app/src/App.jsx'       # his file
modal shell <alice's sb-…> -c 'grep h1 /project/app/src/App.jsx'     # then hers
```

bob gets alice's project, and changes to his do not reach hers: the first
`modal shell` prints `return <h1>Bob</h1>`, the second `return <h1>Alice</h1>`.
A Sandbox ends after 30 s idle. `chat alice` or `chat bob` brings it back, as a
new Sandbox with a new id and the same files: use that id.

Every terminal needs `ENDPOINT_URL`, from chapter 1. After checking out this
branch, reset the user first, so her Sandbox is one this branch made.

## Test it

```sh
uv run checks/ch6_undo.py     # from the repository root
```

Done when each undo puts the project back as it was before one message, the
agent's chat with it, and the fork has the same project in another Sandbox.

## See what changed

```sh
git diff ch6.2-undo ch6-undo -- code
```
