"""Chapter 7, optional: each user has an address of their own, and a visit wakes their Sandbox.

    uv run checks/ch7_link.py

The script:

    $ uv run vibecode.py reset alice
    $ uv run vibecode.py chat alice        # "open https://…--vibecode-alice.modal.run": no token in it
    > Change the heading to say Linked.
    >                                      # leave and close the tab: 30 s later the Sandbox ends
    $ uv run vibecode.py chat alice        # the same address
                                           # or just open the address: the visit wakes the Sandbox

This check plays a user of its own, deploys their link, opens it while the Sandbox is up, listens on
the hot-reload websocket while a file changes, waits for the Sandbox to end, and opens the same
address again. It stops that user's link App at the end.

Done when the address is the same before and after the sleep, and a visit alone brought the Sandbox back.
"""

import json
import re
import subprocess
import sys
import time
import urllib.request

from websockets.sync.client import connect

import stage  # first: it puts code/ on the import path

# isort: split
import link as link_module
import vibecode

USER = "linkcheck"


def page(url):
    """The page as a browser loads it: the document, then the scripts it names. Status, seconds, heading."""
    started = time.time()
    status, html = stage.visit(url)
    for path in re.findall(r'src="([^"]+)"', html):
        stage.visit(urllib.request.urljoin(url, path))
    heading = re.search(r'children: "([^"]*)"', stage.visit(url + "src/App.jsx")[1])
    return status, f"{time.time() - started:.1f} s", f"heading {heading[1]!r}" if heading else "no heading"


def hot_reload(url, sandbox):
    """Listen where the page's Vite client listens, change a file in the Sandbox, return what arrives."""
    token = re.search(r'wsToken = "([^"]+)"', stage.visit(url + "@vite/client")[1])[1]
    with connect(url.replace("https", "wss") + "?token=" + token, subprotocols=["vite-hmr"]) as tab:
        first = json.loads(tab.recv(timeout=20))["type"]
        sandbox.exec("sh", "-c", "echo '/* touched */' >> /project/app/src/App.css").wait()
        started = time.time()
        while (message := json.loads(tab.recv(timeout=20)))["type"] == "ping":
            pass
        return f"{first}, then {message['type']} {message['updates'][0]['path']} {time.time() - started:.1f} s after the edit"


vibecode.reset(USER)
started = time.time()
app, function = link_module.link_for(USER)
app.deploy()
address = function.get_web_url() + "/"
print(f"$ uv run link.py {USER}")
stage.note(f"{address} deployed in {time.time() - started:.1f} s\n")

new = page(address)
first = vibecode.running(USER)
stage.note("a first visit   ", *new, getattr(first, "object_id", "no Sandbox"), "<- made by the visit")
vibecode.checkpoint(first, USER)  # a first turn: from here the user has a project to come back to
awake = page(address)
stage.note("awake           ", *awake)
reload = hot_reload(address, first)
stage.note("hot reload      ", reload)

started = time.time()
while first.poll() is None:
    time.sleep(5)
stage.note(f"asleep           the Sandbox ended {time.time() - started:.0f} s after the socket closed")
woken = page(address)
second = vibecode.running(USER)
stage.note("the same address", *woken, getattr(second, "object_id", "no Sandbox"), "<- woken by the visit\n")

vibecode.reset(USER)
subprocess.run([sys.executable, "-m", "modal", "app", "stop", f"{vibecode.APP}-{USER}", "-y"], capture_output=True)

stage.expect("the address has no token in it", "_modal_connect_token" not in address)
stage.expect("a visit made the user's first Sandbox", new[0] == 200 and first is not None)
stage.expect("the page loads through the address", awake[0] == 200 and "heading" in awake[2])
stage.expect("hot reload passes through", "update" in reload)
stage.expect(
    "after the sleep, the same address woke another Sandbox",
    woken[0] == 200 and second is not None and second.object_id != first.object_id,
)
stage.done()
