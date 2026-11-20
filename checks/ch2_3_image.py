"""Chapter 2, step 3: the Sandbox starts from our Image, and its main process is the app's dev server.

    uv run checks/ch2_3_image.py [user]

The script:

    $ uv run vibecode.py reset alice
    $ uv run vibecode.py chat alice      # "new alice sb-…", then the dev server's own line: where it listens
    >

The first run builds the Image: the template is copied in and its packages are installed. Later runs
find it built.

Done when the template is inside the Sandbox and its main process says it serves on port 8080.
"""

import stage
from stage import USER

stage.run("reset")
said = stage.run("chat")
files = stage.inside(USER, "ls", "/project/app")[1].split()
stage.note("in the Sandbox, /project/app holds", " ".join(files), "\n")
stage.run("reset")

stage.expect(
    "the Sandbox started from the Image: the template and its packages are inside",
    {"package.json", "node_modules"} <= set(files),
)
stage.expect("its main process is the dev server, on port 8080", "http://localhost:8080/" in said)
stage.done()
