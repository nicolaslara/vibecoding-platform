# Chapter 2, step 4: a private link, for the browser

Branch `ch2.4-connect`. Before: `ch2.3-image`. Next: `ch2.5-probe`.

A connect token is a URL and a token for one port of one Sandbox. `preview`
asks Modal for one, for port 8080, and `chat` prints the two as one link that
only opens this user's Sandbox.

## Run it

```sh
cd code
uv run vibecode.py reset alice
uv run vibecode.py chat alice
```

It prints `open https://….w.modal.host/?_modal_connect_token=…`. Open it: the
template app is in your browser. Without the token, the URL answers 401.

Every terminal needs `ENDPOINT_URL`, from chapter 1. After checking out this
branch, reset the user first, so her Sandbox is one this branch made.

## Test it

```sh
uv run checks/ch2_4_connect.py     # from the repository root
```

Done when the link serves the template, and only with its token.

## See what changed

```sh
git diff ch2.3-image ch2.4-connect -- code
```
