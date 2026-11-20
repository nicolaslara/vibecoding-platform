# Chapter 0: create the scaffolding

Branch `ch0-setup`. Next: `ch1-endpoint`.

You install Modal, log in, start a first Sandbox, and run the scaffolding: an
interactive prompt that repeats what you type. It is the main loop that every
later chapter adds to.

## Set up

You need [uv](https://docs.astral.sh/uv/) and git.

```sh
uv tool install modal     # the `modal` command
modal setup               # opens a browser to sign up or sign in
```

If uv warns that the tool is not in your path: `export PATH="$HOME/.local/bin:$PATH"`.

A new account has one Environment, `main`: nothing to do. If you had an
account already, make an Environment for the workshop, and name it in every
terminal:

```sh
modal environment create vibecoding-demo
export MODAL_ENVIRONMENT=vibecoding-demo
export MODAL_PROFILE=personal     # only if you have several workspaces
```

## Run it

```sh
modal shell -c 'echo hello from a Sandbox; echo $MODAL_SANDBOX_ID'
cd code
uv run vibecode.py chat alice
```

The first command prints `hello from a Sandbox` and an id, `sb-…`: Modal
started a Sandbox in your Environment, ran the command in it, and ended it.
Then type `hello` at the prompt and it answers `alice said: hello`. An empty
line ends the chat.

## Test it

```sh
uv run checks/ch0_setup.py     # from the repository root
```

Done when the Sandbox answers from the workspace and Environment you meant to
use.
