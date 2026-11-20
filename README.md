# Chapter 4: keep the key away from the agent

Branch `ch4-key-out`. Before: `ch3-agent`. Next: `ch5-snapshots`.

The Secret never enters the Sandbox. Credential injection with header
replacement takes its place: an outbound policy, by which Modal adds the key
outside the Sandbox, to the `Authorization` header of requests for the model's
host. Inside, `AUTHORIZATION_BEARER` is a placeholder, `added-outside`. The
agent and its config stay as they are.

## Run it

```sh
cd code
uv run vibecode.py reset alice     # her Sandbox from chapter 3 has the key inside
uv run vibecode.py chat alice
> Change the heading in src/App.jsx to say exactly: Key is out
>
uv run python -c "import vibecode; print(vibecode.running('alice').exec('printenv', 'AUTHORIZATION_BEARER').stdout.read())"
```

The agent still works, and cannot read the key. Leave the chat and keep the
tab open, so the Sandbox stays up. The last command then prints
`added-outside`: a placeholder, not the key.

The Sandbox can still reach any host. An outbound policy cannot be combined
with a list of allowed hosts.

Every terminal needs `ENDPOINT_URL`, from chapter 1. After checking out this
branch, reset the user first, so her Sandbox is one this branch made.

## Test it

```sh
uv run checks/ch4_key_out.py     # from the repository root
```

Done when the agent's edit is in the project, the key is not in the Sandbox's
environment, and a request to the model that carries no key is answered.

## See what changed

```sh
git diff ch3-agent ch4-key-out -- code
```
