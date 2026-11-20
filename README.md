# Chapter 2, step 5: the link is printed before the app is up, so we add a readiness probe

Branches `ch2.5-probe` and `ch2-serve`: two names for the same commit.
Before: `ch2.4-connect`. Next: `ch3.1-opencode`.

Until now the link was printed before the app was up. The Sandbox gets a
readiness probe on port 8080, and `wait_until_ready()` returns when the port
answers, so `chat` waits until the app answers before it prints the link. That
is the end of chapter 2, serve each user's app: a Sandbox per user, and a link
that opens the template.

## Run it

```sh
cd code
uv run vibecode.py reset alice
uv run vibecode.py chat alice     # new alice sb-…, then the link
uv run vibecode.py chat alice     # running alice sb-…, the same link
uv run vibecode.py chat bob       # another user, another Sandbox and link
```

Open the link: the template app. A second `chat` finds the same Sandbox.

Every terminal needs `ENDPOINT_URL`, from chapter 1. After checking out this
branch, reset the user first, so her Sandbox is one this branch made.

## Test it

```sh
uv run checks/ch2_serve.py     # from the repository root
```

Done when the link serves the template, only with its token, and a second chat
finds the same Sandbox.

## See what changed

```sh
git diff ch2.4-connect ch2-serve -- code
```
