"""Optional: an address of their own for each user, which stays the same.

With this file beside vibecode.py, `chat` prints the user's address and deploys it the first time.

    uv run link.py alice    # deploys alice's link again, after a change to this file

A connect-token link belongs to one Sandbox, so it changes every time the user's Sandbox wakes.
This deploys a small web Function per user. Modal gives every deployed web Function a host
name, so the user gets an address of their own. For each request the Function finds the user's
Sandbox, or wakes it, and passes the request on. The Sandbox keeps no public port: the Function
presents a connect token, and the token never reaches the browser.

The address is public: anyone who has it can open the user's app and wake their Sandbox.
`modal app stop vibecode-alice` takes it down.
"""

import sys

import modal

import vibecode

# The Function creates Sandboxes with the code the laptop uses, so it carries the same files.
image = (
    modal.Image.debian_slim()
    .pip_install("fastapi[standard]", "httpx")
    .env({"ENDPOINT_URL": "https://" + vibecode.MODEL})  # vibecode.py reads it there too
    .add_local_python_source("vibecode")
    .add_local_dir(vibecode.HERE / "app", "/root/app")
    .add_local_file(vibecode.HERE / "opencode.json", "/root/opencode.json")
)


def link_for(user):
    """An App for one user that holds one web Function: the user's address."""
    app = modal.App(f"{vibecode.APP}-{user}")

    # serialized: the Function is defined here, at run time, once per user
    @app.function(image=image, name="link", serialized=True, timeout=3600)
    @modal.concurrent(max_inputs=100)
    @modal.asgi_app(label=f"{vibecode.APP}-{user}")
    def link():
        import asyncio
        import threading
        import time

        import httpx
        from fastapi import FastAPI, Request, Response

        import vibecode

        web = FastAPI()
        client = httpx.AsyncClient(timeout=60)
        lock = threading.Lock()
        access = None  # a connect token for the user's Sandbox
        checked = 0  # when the Sandbox was last seen running

        def sandbox_access():
            """A connect token for the user's Sandbox, which is woken first when it sleeps."""
            nonlocal access, checked
            with lock:  # one wake at a time: the requests that waited find it running
                if time.time() - checked > 5:  # used a moment ago, so it is still up
                    sandbox = vibecode.boot(user)
                    access = sandbox.create_connect_token(user_metadata={"user": user})
                    checked = time.time()
                return access

        def behind(access, url):
            """The same path and query, on the Sandbox."""
            return access.url + url.path + (f"?{url.query}" if url.query else "")

        @web.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
        async def http(request: Request):
            access = await asyncio.to_thread(sandbox_access)
            headers = {
                name: value
                for name, value in request.headers.items()
                if name not in ("host", "accept-encoding")
            }
            headers["authorization"] = f"Bearer {access.token}"
            response = await client.request(
                request.method,
                behind(access, request.url),
                headers=headers,
                content=await request.body(),
            )
            return Response(
                response.content,
                response.status_code,
                media_type=response.headers.get("content-type"),
            )

        return web

    return app, link


def address(user):
    """The user's address. Their link is deployed the first time it is asked for."""
    try:
        return modal.Function.from_name(f"{vibecode.APP}-{user}", "link").get_web_url()
    except modal.exception.NotFoundError:
        app, link = link_for(user)
        app.deploy()
        return link.get_web_url()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: link.py <user>")
    app, link = link_for(sys.argv[1])
    app.deploy(strategy="recreate")  # the running link is replaced at once
    print("link", link.get_web_url())
