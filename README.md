# Chapter 7, optional, step 1: an address per user, which finds or wakes their Sandbox

Branch `ch7.1-http`. Before: `ch6-undo`. Next: `ch7.2-websocket`.

A connect-token link changes every time the Sandbox wakes, and it carries a
token. A new file, `code/link.py`, defines a small App per user with one web
Function, and deploys it at their first chat. Modal gives the Function a host
name of its own: the user's address. For each request it finds the Sandbox or
wakes it, then passes the request on. From here on, `chat` always prints that
address.

## Run it

```sh
cd code
uv run vibecode.py reset alice
uv run vibecode.py chat alice     # new alice sb-…, open https://…--vibecode-alice.….modal.run
>
uv run vibecode.py reset alice    # end her Sandbox: nothing runs for alice now
curl <her address>                # then visit her address
uv run vibecode.py chat alice     # running alice sb-…: the visit started a Sandbox
```

The address stays the same, has no token in it, and a visit starts the
Sandbox: `curl` prints the page's HTML, and the second `chat` finds a Sandbox
running. Hot reload does not pass yet. That is step 2.

The address is public: anyone who has it can open the app and wake the
Sandbox. `modal app stop vibecode-alice` takes it down.

Every terminal needs `ENDPOINT_URL`, from chapter 1. After checking out this
branch, reset the user first, so her Sandbox is one this branch made.

## Test it

```sh
uv run checks/ch7_1_http.py     # from the repository root
```

Done when the address is the same before and after the sleep, and a visit
alone brought the Sandbox back.

## See what changed

```sh
git diff ch6-undo ch7.1-http -- code
```
