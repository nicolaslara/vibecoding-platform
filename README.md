# Chapter 2, step 3: let's run an actual web app

Branch `ch2.3-image`. Before: `ch2.2-name`. Next: `ch2.4-connect`.

The Sandbox starts from our own Image, built once and cached, with the app
template in `code/app` and its packages installed. The command we pass to
`Sandbox.create`, `npm run dev`, runs as its main process: the template's dev
server. `chat` prints the line where the dev server says it listens.

## Run it

```sh
cd code
uv run vibecode.py reset alice
uv run vibecode.py chat alice
modal shell sb-…          # in a second terminal, with the Sandbox ID chat printed
curl localhost:8080       # inside the Sandbox
```

`chat` prints `new alice sb-…` and `➜ Local: http://localhost:8080/`. The
first run builds the Image. Later runs find it built. Port 8080 has no address
outside yet, so the test is a shell inside the running Sandbox: `curl` prints
the page's HTML, starting with `<!doctype html>`.

Every terminal needs `ENDPOINT_URL`, from chapter 1. After checking out this
branch, reset the user first, so her Sandbox is one this branch made.

## Test it

```sh
uv run checks/ch2_3_image.py     # from the repository root
```

Done when the template is inside the Sandbox and its main process says it
serves on port 8080.

## See what changed

```sh
git diff ch2.2-name ch2.3-image -- code
```
