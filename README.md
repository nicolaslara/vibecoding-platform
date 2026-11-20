# Chapter 2, step 2: reusing an existing Sandbox

Branch `ch2.2-name`. Before: `ch2.1-sandbox`. Next: `ch2.3-image`.

The Sandbox now carries the user's name. There is one running Sandbox per name
in an App, and we can find it again by that name. `running()` finds the
Sandbox, `boot()` creates one only when needed, and a new command, `reset`,
ends it.

## Run it

```sh
cd code
uv run vibecode.py chat alice     # first chat: new alice sb-…
uv run vibecode.py chat alice     # next chat: running alice sb-…, the same id
uv run vibecode.py reset alice    # reset: end it
```

Leave each chat with an empty line. The first `chat` creates a Sandbox. The
next one reuses it: it prints `running alice` with the id the first one
printed. `chat bob` gets a Sandbox of his own.

Every terminal needs `ENDPOINT_URL`, from chapter 1. After checking out this
branch, reset the user first, so her Sandbox is one this branch made.

## Test it

```sh
uv run checks/ch2_2_name.py     # from the repository root
```

Done when a second chat finds the same Sandbox, another user gets one of their
own, and reset ends it.

## See what changed

```sh
git diff ch2.1-sandbox ch2.2-name -- code
```
