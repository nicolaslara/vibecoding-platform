# Chapter 5: save the work

Branch `ch5-snapshots`. Before: `ch4-key-out`. Next: `ch6.1-turns`.

The Sandbox is created with an Exit Snapshot: however it ends, its whole
filesystem is kept as an Image. `last_filesystem` reads that back, and `boot`
starts the next Sandbox from it, so the next one starts where the last one
ended. A Dict named `vibecode-users`, a named key-value store on Modal, is a
record of who has work, so that `reset` still means the template.

## Run it

```sh
cd code
uv run vibecode.py reset alice
uv run vibecode.py chat alice
> Change the heading in src/App.jsx to say exactly: Saved
>                                  # leave, and close the tab
sleep 45                           # the Sandbox goes idle and ends
uv run vibecode.py chat alice      # new alice sb-…: another Sandbox, the same project
```

The second `chat` prints `new alice` with another id, and its link shows the
heading `Saved`: the work survives the Sandbox. After `reset alice`, the next
`chat` shows the template again.

Every terminal needs `ENDPOINT_URL`, from chapter 1. After checking out this
branch, reset the user first, so her Sandbox is one this branch made.

## Test it

```sh
uv run checks/ch5_snapshots.py     # from the repository root
```

Done when the heading survives the sleep in a new Sandbox, and a reset brings
the template back.

## See what changed

```sh
git diff ch4-key-out ch5-snapshots -- code
```
