# A vibecoding app: one Sandbox per user with the coding agent inside, the model key in a Sidecar, one link
# per user that stays the same, a snapshot per message, the idle clock.
#   uv run vibecode.py deploy       # once, and after a change: the base Image by name, the link Function
#   uv run vibecode.py chat alice   # open the link it prints, type a message per line, watch the tab;
#                                   # an empty line, EOF or Ctrl-C ends the chat and the Sandbox stays;
#                                   # Ctrl-C while the agent works leaves too, and the agent finishes the turn
#   uv run vibecode.py undo alice   # takes back the last message, running or not; the tab flips
#   uv run vibecode.py chat alice   # continues: the same Sandbox by name, or a new one from where it ended
#   uv run vibecode.py chat bob     # a second user, in a second terminal: own Sandbox, own link, same base
#   uv run vibecode.py reset alice  # alice starts over from the template
import asyncio
import os
import sys
import threading
import time

import modal

os.chdir(os.path.dirname(os.path.abspath(__file__)))   # the files it ships sit beside it
APP = "vibecode"   # the deployed App: the link Function and every user's Sandbox
app = modal.App(APP)
# the Model Endpoint the agent calls, yours: `modal endpoint info kimi-k3` shows it as URL
MODEL = "nicolaslara-vibecoding-demo--ep-kimi-k3-server.us-west.modal.direct"
# the base, as a recipe: a Vite template with its deps, then OpenCode pointed at the Sidecar
recipe = (modal.Image.from_registry("node:22-slim")
          .add_local_dir("app", "/project/app", copy=True)
          .run_commands("cd /project/app && npm ci")
          .run_commands("npm install -g opencode-ai@1.18.30")
          .add_local_file("opencode.json", "/root/.config/opencode/opencode.json",
                          copy=True)
          .env({"OPENCODE_DISABLE_MODELS_FETCH": "true", "XDG_DATA_HOME": "/project/chat",
                "MODEL": MODEL, "MODAL_PROXY_TOKEN": "in-the-sidecar"})
          .apt_install("rsync", "procps"))
# the base, built: deploy publishes it under this name, so code on Modal can use it too
base = modal.Image.from_name("vibecode-base")
proxy = modal.Image.from_registry("caddy:2.11")   # the Sidecar's Image
web = modal.Image.debian_slim().pip_install("fastapi[standard]", "httpx", "websockets")
# the app's own record, user: [snapshot id per message, taken before it]
turns_of = modal.Dict.from_name("vibecode-turns", create_if_missing=True)

def running(user):  # the user's Sandbox while it is up
    try:
        sb = modal.Sandbox.from_name(APP, user)
        return sb if sb.poll() is None else None
    except modal.exception.NotFoundError:
        return None

def asleep(user):  # the filesystem the user's last Sandbox ended with
    try:
        last = modal.Sandbox.from_name(APP, user, include_terminated=True)
        return last._experimental_get_exit_snapshot()
    except modal.Error:
        return base   # nothing kept

def boot(user):
    sb = running(user)
    if sb:
        print("running", user, sb.object_id)
        return sb
    shop = modal.App.lookup(APP, create_if_missing=True)
    sb = modal.Sandbox.create(
        "npm", "run", "dev", "--", "--base", f"/{user}/",  # the entrypoint, at /<user>/
        app=shop, workdir="/project/app",
        image=asleep(user) if turns_of.get(user) else base,  # back from sleep, or new
        readiness_probe=modal.Probe.with_tcp(8080),
        name=user, idle_timeout=30, timeout=3600,  # by name; sleeps when idle
        experimental_options={"enable_exit_snapshot": True},  # and keeps its filesystem
        outbound_domain_allowlist=["registry.npmjs.org"])  # egress: npm only
    # the model key never enters: a Sidecar holds it and reaches one host
    sb._experimental_sidecars.create(
        "caddy", "reverse-proxy", "--from", ":8080", "--change-host-header",
        "--to", "https://inference.us-west.modal.direct",
        "--header-up", "Authorization: Bearer {env.AUTHORIZATION_BEARER}",
        name="tools", image=proxy.build(shop),
        secrets=[modal.Secret.from_name("model-token")],
        outbound_domain_allowlist=["inference.us-west.modal.direct"])
    sb.wait_until_ready()
    print("new", user, sb.object_id)
    return sb

@app.function(image=web, timeout=3600)   # a tab's websocket lives as long as a Sandbox
@modal.concurrent(max_inputs=100)
@modal.asgi_app()
def link():  # one address for every user: <url>/<user>/ is their dev server, proxied
    import httpx
    import websockets
    from fastapi import FastAPI, HTTPException, Request, Response, WebSocket
    api, client = FastAPI(), httpx.AsyncClient(timeout=60)
    doors, waking = {}, threading.Lock()

    def door(user):  # the user's Sandbox, found or woken, and a connect token for it
        checked, cred = doors.get(user, (0, None))
        if time.time() - checked < 5: return cred   # in use a moment ago: still up
        sb = running(user)
        if not sb:
            if not turns_of.get(user): raise HTTPException(404)   # nobody by that name
            with waking: sb = boot(user)   # one wake at a time; the others find it running
        # no public port, and the token stays on this side of the link
        cred = sb.create_connect_token(user_metadata={"user": user})
        doors[user] = time.time(), cred
        return cred

    @api.api_route("/{user}/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
    async def http(user: str, request: Request):
        cred = await asyncio.to_thread(door, user)
        heads = {k: v for k, v in request.headers.items()
                 if k not in ("host", "accept-encoding")}
        r = await client.request(
            request.method, cred.url + request.url.path, params=request.query_params,
            content=await request.body(),
            headers={**heads, "authorization": f"Bearer {cred.token}"})
        return Response(r.content, r.status_code, media_type=r.headers.get("content-type"))

    @api.websocket("/{user}/{path:path}")   # hot reload
    async def ws(user: str, tab: WebSocket):
        cred = await asyncio.to_thread(door, user)
        url = f"{cred.url.replace('https', 'wss')}{tab.url.path}?{tab.url.query}"
        async with websockets.connect(
                url, subprotocols=tab.scope["subprotocols"],
                additional_headers={"Authorization": f"Bearer {cred.token}"}) as dev:
            await tab.accept(dev.subprotocol)
            async def down():
                async for message in dev: await tab.send_text(message)
            async def up():
                async for message in tab.iter_text(): await dev.send(message)
            pumps = [asyncio.create_task(down()), asyncio.create_task(up())]
            await asyncio.wait(pumps, return_when=asyncio.FIRST_COMPLETED)
    return api

def deploy():  # build the base and name it, deploy the link Function
    recipe.build(modal.App.lookup(APP, create_if_missing=True)).publish("vibecode-base")
    app.deploy()

def ask():  # a line from the user; an empty one, EOF or Ctrl-C ends the chat
    try: return input("> ")
    except (EOFError, KeyboardInterrupt): print(); return ""

def chat(user="alice"):
    sb = boot(user)
    print(f"open {modal.Function.from_name(APP, 'link').get_web_url()}/{user}/")
    while msg := ask():
        if sb.poll() is not None: sb = boot(user)   # the idle clock got it
        while sb.exec("flock", "-n", "/tmp/turn", "true").wait():   # a turn left running
            print("a turn is still running; waiting for it (undo stops it)"); time.sleep(10)
        turns = checkpoint(sb, user)   # before the message: what undo goes back to
        # one exec of the agent per message, continuing its chat; flock: one turn at a time
        t = time.time()
        run = ('exec flock /tmp/turn timeout -k 5 600 '   # ten minutes, children too
               'opencode run --auto $1 -- "$0" < /dev/null 2>&1')
        p = sb.exec("sh", "-c", run, msg, "-c" if turns[1:] else "")
        for chunk in p.stdout: print(chunk, end="")   # each step as the agent takes it
        if p.wait(): print(f"turn {len(turns)} stopped rc={p.returncode}")
        else: print(f"turn {len(turns)} {time.time() - t:.0f}s")

def checkpoint(sb, user):  # a snapshot of the project, app and chat, as a turn
    turns = turns_of.get(user, []) + [sb.snapshot_directory("/project").object_id]
    turns_of[user] = turns
    return turns

def restore(sb, snapshot_id):  # mount a turn beside the project, sync the project to it
    path = f"/history/{time.time_ns()}"
    sb.mount_image(path, modal.Image.from_id(snapshot_id))
    sync = sb.exec("flock", "/tmp/turn", "rsync", "-a", "--delete", f"{path}/", "/project/")
    if sync.wait(): raise SystemExit(sync.stderr.read())
    sb.unmount_image(path)

def undo(user="alice"):
    turns = turns_of.get(user, [])
    if not turns: return print("nothing to undo")
    sb = boot(user)
    sb.exec("pkill", "-f", "opencode run").wait()   # the last message may still be running
    restore(sb, turns.pop())
    turns_of[user] = turns
    print("turn", len(turns))

def reset(user="alice"):  # back to the template: no Sandbox, no turns
    sb = running(user)
    if sb: sb.terminate(wait=True)
    turns_of.pop(user, None)

if __name__ == "__main__":
    commands = {"deploy": deploy, "chat": chat, "undo": undo, "reset": reset}
    if sys.argv[1:2] == [] or sys.argv[1] not in commands:
        sys.exit("usage: vibecode.py deploy | chat|undo|reset [user]")
    try: commands[sys.argv[1]](*sys.argv[2:])
    except KeyboardInterrupt: print("\nleft; a turn in progress finishes in the Sandbox")
