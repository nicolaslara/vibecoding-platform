# A vibecoding platform on Modal Sandboxes

A workshop. You build an application where each user gets a Sandbox with a
coding agent inside: they type what they want, and watch their web app change
in a browser tab.

It is built in chapters, and most chapters in steps. Every chapter and every
step is a branch that holds the application as it stands at that point.

The slides: <https://nicolaslara.github.io/vibecoding-platform/>

## The chapters

| Chapter | Branch | Its steps | What you have at the end |
| --- | --- | --- | --- |
| 0. Create the scaffolding | `ch0-setup` | | Modal is set up, and an interactive prompt repeats what you type. |
| 1. Set up an endpoint | `ch1-endpoint` | | The model answers with the key, and refuses without it. |
| 2. Serve each user's app | `ch2-serve` | `ch2.1-sandbox`, `ch2.2-name`, `ch2.3-image`, `ch2.4-connect`, `ch2.5-probe` | A Sandbox per user, and a link that opens the template. |
| 3. Let an agent change the app | `ch3-agent` | `ch3.1-opencode`, `ch3.2-turn`, `ch3.3-secret` | A message changes the app. |
| 4. Keep the key away from the agent | `ch4-key-out` | | The agent still works, and cannot read the key. |
| 5. Save the work | `ch5-snapshots` | | The work survives the Sandbox. |
| 6. Undo a message and fork a project | `ch6-undo` | `ch6.1-turns`, `ch6.2-undo`, `ch6.3-fork` | `undo` takes back a message, and `fork` copies a project. |
| 7. Give each user an address (optional) | `ch7-link` | `ch7.1-http`, `ch7.2-websocket` | Each user has an address of their own, and hot reload passes. |

A chapter's last step and the chapter itself are two names for the same commit.

## Moving through them

```sh
git clone https://github.com/nicolaslara/vibecoding-platform.git
cd vibecoding-platform
git checkout ch0-setup                        # start here, and read its README
git checkout ch2.1-sandbox                    # any branch runs on its own
git diff ch2.1-sandbox ch2.2-name -- code     # what a step adds
```

Every branch has its own README: what the step adds, how to run it, and how to
test it. In a fresh clone, a branch you have not checked out yet is
`origin/ch2.2-name` in a `git diff`.

All branches use the same App and the same Sandbox name per user. After moving
to another branch, run `uv run vibecode.py reset alice` from `code/` before
`chat`, so that her Sandbox is one this branch made.

## On `main`

`main` holds the finished application, in [`code/`](code/), and the slides.
`uv run python slides/build.py` builds the deck into `dist/index.html`. It
reads each step's code from the branches.
