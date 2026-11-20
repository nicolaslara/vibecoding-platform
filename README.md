# Chapter 6, step 1: a Snapshot before every message

Branch `ch6.1-turns`. Before: `ch5-snapshots`. Next: `ch6.2-undo`.

Before every message, `checkpoint` takes a Filesystem Snapshot: the whole
filesystem of the running Sandbox, as an Image. The Sandbox keeps running. The
app's record grows: the record of who has work, from chapter 5, becomes the
Dict `vibecode-turns`, which holds, per user, the ids of their Snapshots.
Nothing uses them yet. The next step, undo, does.

## Run it

```sh
cd code
uv run vibecode.py reset alice
uv run vibecode.py chat alice
> Change the heading in src/App.jsx to say exactly: Saved
> Add a paragraph under the heading that says exactly: Still here
>
modal dict get vibecode-turns alice     # the record: one Snapshot per message
uv run vibecode.py reset alice
modal dict get vibecode-turns alice     # None
```

Each turn ends with its number: a line that starts with `turn 1`, then one
that starts with `turn 2`. The first `modal dict get` prints two Image ids,
`['im-…', 'im-…']`. After `reset alice` it prints `None`.

Every terminal needs `ENDPOINT_URL`, from chapter 1. After checking out this
branch, reset the user first, so her Sandbox is one this branch made.

## Test it

```sh
uv run checks/ch6_1_turns.py     # from the repository root
```

Done when the Dict holds one Image id per message, and reset forgets them.

## See what changed

```sh
git diff ch5-snapshots ch6.1-turns -- code
```
