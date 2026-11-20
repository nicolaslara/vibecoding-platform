"""Chapter 1: a model answers, with your key and not without it.

    uv run checks/ch1_endpoint.py

The script:

    $ export ENDPOINT_URL=$(modal endpoint info kimi-k3 --json | jq -r .service_url)   # vibecode.py reads it
    $ modal secret list                  # model-token is there

Then this check starts a Sandbox that holds the Secret and calls the model from inside it, once with
the key and once without. The key is read where it lives: it never comes to the laptop.

Done when the first call answers 200 and the second 401.
"""

import modal

import stage
import vibecode

GATEWAY = "inference.us-west.modal.direct"  # the Model Endpoints of a region are called through it

# One chat completion from inside the Sandbox: prints the status, then the start of the reply.
CALL = """
import json, os, sys, urllib.error, urllib.request
host, model, key = sys.argv[1], sys.argv[2], sys.argv[3] == "with-key"
body = {"model": model, "max_tokens": 200, "messages": [{"role": "user", "content": "Reply with one word: pong"}]}
headers = {"Content-Type": "application/json"}
if key:
    headers["Authorization"] = "Bearer " + os.environ["AUTHORIZATION_BEARER"]
request = urllib.request.Request(f"https://{host}/v1/chat/completions", json.dumps(body).encode(), headers)
try:
    reply = json.load(urllib.request.urlopen(request, timeout=120))
    print(200, (reply["choices"][0]["message"]["content"] or "").strip()[:60])
except urllib.error.HTTPError as error:
    print(error.code, error.read().decode()[:60])
"""

print("model     ", vibecode.MODEL)
print("called at ", f"https://{GATEWAY}/v1")
try:
    key = modal.Secret.from_name("model-token")
    key.hydrate()
except modal.exception.NotFoundError as error:
    stage.expect(f"the Secret model-token exists ({error})", False)
    stage.done()

print("\na Sandbox that holds the Secret, calling the model")
app = modal.App.lookup("vibecode", create_if_missing=True)
sandbox = modal.Sandbox.create(app=app, secrets=[key], timeout=300)
answers = {}
for how in ("with-key", "without-key"):
    call = sandbox.exec("python", "-c", CALL, GATEWAY, vibecode.MODEL, how)
    answers[how] = call.stdout.read().strip() or call.stderr.read().strip()[-200:]
    call.wait()
    stage.note(f"{how:12}", answers[how])
sandbox.terminate()
print()

stage.expect("the Secret model-token exists in this Environment", True)
stage.expect("with the key, the model answers 200", answers["with-key"].startswith("200"))
stage.expect("without the key, the gateway answers 401", answers["without-key"].startswith("401"))
stage.done()
