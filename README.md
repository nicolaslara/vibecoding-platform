# Chapter 7, optional, step 2: hot reload

Branches `ch7.2-websocket` and `ch7-link`: two names for the same commit.
Before: `ch7.1-http`. Next: `main`.

A web Function takes websockets too. Hot reload is one: the Function now
proxies the tab's WebSocket connection to the dev server, both ways, so the
open tab follows the agent's edits. That is the end of chapter 7, give each
user an address.

## Run it

```sh
cd code
uv run link.py alice               # deploy alice's link again, with this branch's code
uv run vibecode.py chat alice      # her address: open it, or reload the tab if it was open
> Change the heading to say Linked.
```

Coming from step 1, do both: deploy the link again, and reload the tab. `chat`
deploys a link only when there is none, so the link from step 1 keeps running
step 1's code until `uv run link.py alice` replaces it. It is replaced at
once. A tab that was opened against the old link never reconnects its hot
reload socket, so reload it. Then the tab changes while the agent edits.

Every terminal needs `ENDPOINT_URL`, from chapter 1. After checking out this
branch, reset the user first, so her Sandbox is one this branch made.

## Test it

```sh
uv run checks/ch7_link.py     # from the repository root
```

Done when the address is the same before and after the sleep, and a visit
alone brought the Sandbox back.

## See what changed

```sh
git diff ch7.1-http ch7-link -- code
```
