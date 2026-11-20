# Chapter 2, step 1: a Sandbox, and a command run in it

Branch `ch2.1-sandbox`. Before: `ch1-endpoint`. Next: `ch2.2-name`.

A Sandbox is an isolated execution environment. `boot` starts one on Modal, in
an App named `vibecode`, and `chat` runs one command in it via exec and prints
what it says. The Sandbox ends when nothing has used it for 30 s: that is
`idle_timeout=30`.

## Run it

```sh
cd code
uv run vibecode.py chat alice
modal shell sb-…     # in a second terminal, with the Sandbox ID chat printed
```

`chat` prints `new alice sb-…`, then `hello from a Sandbox`, then the prompt.
`modal shell` opens a shell inside that same Sandbox: run it before the
Sandbox idles out. Every `chat` starts another Sandbox: nothing finds the
first one again yet.

Every terminal needs `ENDPOINT_URL`, from chapter 1.

## Test it

```sh
uv run checks/ch2_1_sandbox.py     # from the repository root
```

Done when chat starts a Sandbox, a command answers from inside it, and the
Sandbox ends once nothing uses it.

## See what changed

```sh
git diff ch1-endpoint ch2.1-sandbox -- code
```
