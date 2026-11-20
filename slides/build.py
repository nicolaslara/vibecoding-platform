"""Build the deck from the code: `uv run python slides/build.py` writes dist/index.html.

Nothing here runs the application or calls Modal. The chapter slides (slides/chapters.py) read the chapter
branches of this repository as text; the hidden walkthrough at the end reads slides/vibecode_compact.py.
"""

import base64
import sys
import pathlib
import html as _h

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
from annotated import CSS as ANNOTATED_CSS, annotate
from chapters import CSS as CHAPTER_CSS, REPO, chapter_parts, own_markers, shell, shot
from common.deck import render_deck, slide, title_slide, hl

# The hidden walkthrough slides show slices (substring ranges, searched in order) of the compact, slide-sized
# version of the application. The readable version is code/vibecode.py with the optional code/link.py; the
# compact one is rebuilt from it when the application is settled. Until then those slides stay hidden
# (shown with ?hidden=1): they hold the measured notes the rebuilt slides will reuse.
SRC = "slides/vibecode_compact.py"
SRC_PATH = ROOT / SRC
STEPS = 10  # build slides, for the footer


def shown_lines(src: str):
    """The script minus its header comment, the stdlib imports at the top, timing lines and cleanup lines."""
    lines = src.rstrip().split("\n")
    while lines and lines[0].startswith("#"):
        lines.pop(0)
    out, header = [], True
    for l in lines:
        if header and (l.startswith("import ") or l.startswith("from ")) and not l.startswith("import modal"):
            continue
        if header and l.strip() and not l.startswith(("import ", "from ")):
            header = False
        if l.strip().startswith(("t = time.perf_counter()", "t = time.time()")) or "# cleanup" in l:
            continue
        if not l.strip() and out and not out[-1].strip():
            continue
        out.append(l)
    while out and not out[0].strip():
        out.pop(0)
    return out


LINES = shown_lines(SRC_PATH.read_text())


def _slice(lines, ranges):
    """For each (start, end): the lines from the first one containing `start` to the next one containing `end`, inclusive.
    Each range is searched after the previous one, falling back to the top; a blank line separates ranges."""
    out, cursor = [], 0
    for start, end in ranges:
        i = next((k for k in range(cursor, len(lines)) if start in lines[k]), None)
        if i is None:
            i = next(k for k, l in enumerate(lines) if start in l)
        j = next(k for k in range(i, len(lines)) if end in lines[k])
        out += ([""] if out else []) + lines[i : j + 1]
        cursor = j + 1
    return out


def _step_of(line, steps):
    for k, st in enumerate(steps, 1):
        if any(key in line for key in st[0]):
            return k
    return 0


def show_code(lines, steps) -> str:
    html_lines = hl("\n".join(lines)).split("\n")
    assert len(html_lines) == len(lines)
    out = []
    for raw, h in zip(lines, html_lines):
        k = _step_of(raw, steps)
        out.append('<span class="ln"%s>%s</span>' % ((' data-step="%d"' % k) if k else "", h or " "))
    rows = sum(max(1, -(-len(l) // 92)) for l in lines)  # wrapped rows at the base size, about 92 columns
    size = " code--densest" if rows > 25 else (" code--denser" if rows > 21 else (" code--dense" if rows > 16 else ""))
    return '<pre class="code%s">%s</pre>' % (size, "".join(out))


def notes(step: int, lead: str, feature: str, how: str, also: str = "", fragment: bool = False) -> str:
    """One block of the right column: the step's lead line, then feature, how and (optional) also. Shown on its step only."""
    rows = [("feature", feature), ("how", how)] + ([("also", also)] if also else [])
    head = ('<p class="lead"><span class="n">%d</span>%s</p>' % (step, lead)) if lead else ""
    return '<div class="bnotes%s" data-step="%d">%s%s</div>' % (
        " fragment" if fragment else "",
        step,
        head,
        "".join('<p><span class="k">%s</span>%s</p>' % (k, v) for k, v in rows),
    )


def build_step(n: int, title: str, sub: str, code, summary, steps) -> str:
    """A build slide: slices of the file on the left, lit up step by step; on the right the summary before the first
    step, then that step's own feature, how and also. steps: (line keys, lead, feature, how[, also])."""
    lines = _slice(LINES, code)
    for st in steps:
        for key in st[0]:
            if not any(key in l for l in lines):
                raise SystemExit("slides/build.py: step key %r is not in the slice of step %d" % (key, n))
    right = notes(0, "", *summary) + "".join(notes(k, st[1], *st[2:], fragment=True) for k, st in enumerate(steps, 1))
    hint = '<div class="stepnotes"><span class="stepnote" data-step="0"><span class="stephint">→ walks through it</span></span></div>'
    body = '<div class="vc-ex"><div class="split vc-split">%s<div class="vc-notes">%s</div></div>%s</div>' % (
        show_code(lines, steps),
        right,
        hint,
    )
    return slide(body, "Build · %d" % n, title, sub, foot="%s · step %d of %d" % (SRC, n, STEPS), hidden=True)


# ---------- the diagram of the finished application ----------
def diagram(chapter=None, told=False) -> str:
    """The application. `told`: drawn in the order it is told, each part a step that appears on a key press.
    With a chapter: as it stands at the end of that chapter, with what the chapter adds
    in accent and what later chapters add faint. A chapter built in steps numbers them 2.1, 2.2, …: with
    one of those, as it stands at the end of that step."""

    def box(x, y, w, h, lines, cls="vc-box", tcls="vc-t"):
        o = ['<rect class="%s" x="%d" y="%d" width="%d" height="%d" rx="8"/>' % (cls, x, y, w, h)]
        for k, (t, c) in enumerate(lines):
            o.append('<text class="%s" x="%d" y="%d">%s</text>' % (c or tcls, x + 14, y + 26 + 21 * k, _h.escape(t)))
        return "".join(o)

    def arrow(x1, y1, x2, y2, label="", lx=None, ly=None, cls="vc-a"):
        o = ['<line class="%s" x1="%d" y1="%d" x2="%d" y2="%d" marker-end="url(#vc-head)"/>' % (cls, x1, y1, x2, y2)]
        if label:
            o.append(
                '<text class="vc-s" x="%d" y="%d">%s</text>'
                % (
                    lx if lx is not None else (x1 + x2) // 2,
                    ly if ly is not None else (y1 + y2) // 2 - 6,
                    _h.escape(label),
                )
            )
        return "".join(o)

    def text(x, y, t):
        return '<text class="vc-s" x="%d" y="%d">%s</text>' % (x, y, _h.escape(t))

    o = [
        '<defs><marker id="vc-head" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z" class="vc-head"/></marker>'
        '<marker id="vc-head-new" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z" class="vc-head-new"/></marker></defs>'
    ]

    def put(svg, since, only=False, step=1):
        """Draw a part that exists from chapter `since` on, or in that chapter `only`. `step` is when the
        part appears while the whole application is told; the first step is there from the start."""
        new = '<g class="vc-new">%s</g>' % svg.replace("url(#vc-head)", "url(#vc-head-new)")
        if chapter is not None and chapter == int(chapter):
            since = int(since)  # a whole chapter's picture: a part one of its steps adds is the chapter's
        if chapter is None:
            if not only:
                o.append(
                    '<g class="fragment" data-fragment-index="%d">%s</g>' % (step, svg) if told and step > 1 else svg
                )
        elif only:
            o.append(new if chapter == since else "")
        elif since > chapter:
            o.append('<g class="vc-later">%s</g>' % svg)
        else:
            o.append(new if since == chapter else svg)

    # The order the application is told in, on the slide that builds it up.
    SCRIPT, SANDBOX, APP, SLEEP, AGENT, KEY, TURNS, LINK = range(1, 9)
    at = 99 if chapter is None else chapter + 0.9 if chapter == int(chapter) else chapter  # a whole chapter: its end
    # the left column, read top to bottom: who looks at the app, then who drives it
    put(box(30, 14, 220, 58, [("alice's browser", "vc-t"), ("her app, by a private link", "vc-s")]), 2.4, step=APP)
    put(
        box(30, 92, 220, 62, [("a stable URL", "vc-t"), ("an address of her own", "vc-s")]),
        7.1,
        step=LINK,
    )
    put(box(30, 186, 220, 90, [("uv run vibecode.py", "vc-t"), ("chat", "vc-m")]), 0, step=SCRIPT)
    if at >= 2.2:
        commands = "undo  fork  reset" if at >= 6.3 else "undo  reset" if at >= 6.2 else "reset"
        put('<text class="vc-m" x="44" y="254">%s</text>' % commands, 2.2, step=TURNS)
    # the user's state, kept outside the Sandbox and found by her name: a band around the three stores
    put(
        '<rect class="vc-state" x="18" y="446" width="899" height="90" rx="12"/>'
        '<text class="vc-tag" x="22" y="439">STATE</text>',
        5,
        step=SLEEP,
    )
    put(
        box(30, 462, 220, 58, [("alice → her turns", "vc-t"), ("a list of Snapshot ids", "vc-s")], cls="vc-snap"),
        6.1,
        step=TURNS,
    )
    put(arrow(250, 491, 398, 491), 6.1, step=TURNS)
    # everything right of the left column, drawn in its own coordinates
    o.append('<g transform="translate(60 0)">')
    put(
        '<rect class="vc-sb" x="310" y="40" width="560" height="372" rx="12"/><text class="vc-h" x="330" y="68">Sandbox  alice</text>',
        2.1,
        step=SANDBOX,
    )
    put(box(340, 86, 250, 62, [("npm run dev  :8080", "vc-t"), ("the entrypoint, hot reload", "vc-s")]), 2.3, step=APP)
    put(
        box(340, 178, 250, 62, [("opencode run <message>", "vc-t"), ("the agent, once per message", "vc-s")]),
        3.2,
        step=AGENT,
    )
    put(box(340, 270, 250, 62, [("/project/app", "vc-t"), ("her app, from the template", "vc-s")]), 2.3, step=APP)
    # the key is added to the agent's requests outside the Sandbox, on the way to the model
    # attached to the Sandbox, on its way out: the proxy an outbound policy puts there
    put(
        box(870, 178, 200, 62, [("egress proxy", "vc-t"), ("adds the key on the way out", "vc-s")], cls="vc-side"),
        4,
        step=KEY,
    )
    put(text(630, 96, "sleeps after 30 s idle"), 2.1, step=SLEEP)
    put(
        box(930, 330, 220, 62, [("the model: Kimi K3", "vc-t"), ("inference.us-west.modal.direct", "vc-s")]),
        1,
        step=KEY,
    )
    put(
        box(
            340,
            462,
            250,
            58,
            [("turn 0 · turn 1 · turn 2", "vc-t"), ("her Sandbox, before each message", "vc-s")],
            cls="vc-snap",
        ),
        6.1,
        step=TURNS,
    )
    put(
        box(
            630,
            462,
            215,
            58,
            [("alice → her last Sandbox", "vc-t"), ("the filesystem it ended with", "vc-s")],
            cls="vc-snap",
        ),
        5,
        step=SLEEP,
    )
    put(
        box(930, 462, 220, 58, [("the template", "vc-t"), ("every new user starts here", "vc-s")], cls="vc-snap"),
        2.3,
        step=APP,
    )
    put(arrow(380, 332, 380, 460, "before every message", 388, 372), 6.1, step=TURNS)
    put(
        arrow(540, 460, 540, 414, "undo, fork: start from one" if at >= 6.3 else "undo: start from one", 392, 434),
        6.2,
        step=TURNS,
    )
    put(arrow(700, 412, 700, 460, "when it ends", 616, 434), 5, step=SLEEP)
    put(arrow(790, 460, 790, 414, "wakes from it", 798, 434), 5, step=SLEEP)
    put(arrow(1000, 460, 872, 400, "a new user", 944, 420), 2.3, step=APP)
    put(arrow(590, 209, 868, 209, "calls the model without the key", 606, 201), 4, step=KEY)
    put(arrow(950, 240, 950, 328), 4, step=KEY)
    # chapter 3 alone: the agent holds the key and calls the model itself
    put(arrow(590, 222, 928, 352, "Bearer wk-…, from its own environment", 612, 340), 3.3, only=True)
    o.append("</g>")
    # the left column's arrows, drawn last so they end on the boxes inside the Sandbox
    put(arrow(250, 43, 398, 100), 2.4, step=APP)
    put(arrow(140, 72, 140, 90), 7.1, step=LINK)
    put(arrow(250, 123, 398, 123, "finds or wakes it", 268, 116), 7.1, step=LINK)
    put(arrow(250, 200, 368, 170, "finds or starts it", 118, 181), 2.1, step=SANDBOX)
    put(arrow(250, 226, 398, 209, "a message", 290, 208), 3.2, step=AGENT)
    put(arrow(250, 255, 398, 300, "takes a Snapshot", 200, 314), 6.1, step=TURNS)
    put(arrow(140, 276, 140, 460, "the turn ids", 150, 380), 6.1, step=TURNS)
    return own_markers(
        '<figure class="vc-fig%s"><svg viewBox="0 0 1240 545" role="img" aria-label="The vibecoding app: the script finds or starts one Sandbox per user, runs the agent once per message and saves the project before each; the browser opens the dev server by a private link; Modal adds the model key to its requests outside the Sandbox. Her state is kept outside the Sandbox: her list of turns, the project before each message, and the filesystem her last Sandbox ended with. Every new user starts from one template. A stable URL gives her an address that finds or wakes her Sandbox">%s</svg></figure>'
        % ("" if chapter is None else " vc-staged", "".join(o))
    )


# ---------- the slides ----------
slides = [
    title_slide(
        "Modal Sandboxes",
        "Creating a vibecoding platform",
        foot="October 2026",
    )
]
DEMO = """<div class="ch-steps"><pre class="code">%s</pre>%s</div>""" % (
    shell("""# example session: open the link, then send prompts
$ uv run vibecode.py chat alice
> A cake shop called Le Petit Trianon.
> Give it a royal Versailles theme.
# takes back the last message
$ uv run vibecode.py undo alice
# bob gets a copy of alice's project
$ uv run vibecode.py fork alice bob
# the tab was closed and it slept: back by name, where it ended
$ uv run vibecode.py chat alice"""),
    shot("app", "Le Petit Trianon, from the workshop demo", show_caption=False),
)
slides.append(
    slide(
        DEMO,
        "Feature demo",
        "What we'll build",
        "Create an app, change it, undo a turn, fork it, and pick up where you left off.",
    )
)
# What the line under the title says at each step of the diagram, in the order diagram(told=True) draws it.
TOLD = [
    "A script on the laptop, with a chat prompt.",
    "It finds or starts a Sandbox named after the user.",
    "The Sandbox runs her app from a shared template. She opens it by a private link.",
    "Idle, it goes to sleep. Its filesystem is kept, and the next Sandbox wakes from it.",
    "Each message runs a coding agent once, inside the Sandbox.",
    "The agent calls the model. Modal adds the key to its requests, outside the Sandbox.",
    "A Snapshot is taken before every message. Undo and fork start a Sandbox from one.",
    "A stable URL that finds or wakes her Sandbox.",
]
slides.append(
    slide(
        diagram(told=True),
        "The architecture",
        "Ephemeral Sandboxes per user",
        "".join('<span class="vc-cap" data-step="%d">%s</span>' % (k, _h.escape(line)) for k, line in enumerate(TOLD)),
    )
)
slides.append(
    slide(
        annotate(diagram()),
        "The architecture",
        "The Modal features in it",
    )
)

# The talk, in sections: down and up move between them, left and right walk every slide. The opening section
# shows the product and the whole application; then one section per chapter. Each chapter says what hurts
# and what we build about it, shows the design on the diagram, the Modal features, then the code.
opening = slides[1:]
parts = [dict(name="app", title="The application", label="The application", opener=False, slides=opening)]
parts += chapter_parts(diagram, annotate)

# The earlier walkthrough of the compact version: a hidden section until that version is rebuilt.
intro, slides = slides[:1], []
slides.append(
    build_step(
        1,
        "Serve the app",
        "A Sandbox whose main process is the dev server, ready when the port answers.",
        code=[
            ("recipe = (", 'npm ci")'),
            ("# the base, built", "base = modal.Image.from_name"),
            ("def deploy", 'publish("vibecode-base")'),
            ("    sb = modal.Sandbox.create(", 'outbound_domain_allowlist=["registry'),
            ("sb.wait_until_ready()", "sb.wait_until_ready()"),
        ],
        summary=(
            "Image, Sandbox.create(*entrypoint), readiness_probe",
            "An Image with the template and its deps, a Sandbox whose main process is the dev server, a probe that says when it answers.",
        ),
        steps=[
            (
                ["recipe = (", '.add_local_dir("app"', '.run_commands("cd /project/app && npm ci")'],
                "The Image: a Vite template and its deps, built once.",
                "modal.Image",
                "Built once, cached; every Sandbox starts from it in about 3 s. <code>copy=True</code> because a later layer runs <code>npm ci</code> on the files, which installs exactly what the lockfile names.",
                "A Filesystem Snapshot as the base, when the setup happens in a Sandbox rather than a build.",
            ),
            (
                ["def deploy", 'publish("vibecode-base")', "base = modal.Image.from_name"],
                "deploy builds it and gives it a name; everything else refers to the name.",
                "Image.build, Image.publish, Image.from_name",
                "The recipe reads files on this laptop, so only the laptop can build it. Published under a name, the built Image can be used from anywhere in the environment, code running on Modal included.",
                "<code>name:tag</code> to keep versions side by side.",
            ),
            (
                ["sb = modal.Sandbox.create(", '"npm", "run", "dev"'],
                "The dev server is the entrypoint.",
                "Sandbox.create(*entrypoint)",
                "The command is the Sandbox’s main process; the Sandbox lives while it runs, up to <code>timeout</code>.",
                "No entrypoint: the Sandbox idles until something is exec’d, or it is terminated.",
            ),
            (
                ["readiness_probe=modal.Probe", "sb.wait_until_ready()"],
                "The probe watches port 8080; wait_until_ready returns when it answers.",
                "readiness_probe, wait_until_ready()",
                "The probe runs inside; <code>wait_until_ready()</code> blocks until it passes, about 3 s here with the Image warm.",
                "<code>Probe.with_exec</code> for a command; <code>sb.tunnels()</code> or the token URL is live before the server is.",
            ),
        ],
    )
)

slides.append(
    build_step(
        2,
        "Let the user watch",
        "The dev server in the user’s browser, with no public port, and the page hot-reloads.",
        code=[
            ("# no public port, and the token", "cred = sb.create_connect_token(user_metadata"),
            ("        r = await client.request(", '"authorization": f"Bearer'),
        ],
        summary=(
            "Sandbox connect tokens",
            "A URL and a token for one port of this Sandbox, with the user’s identity inside. No public port; websockets pass, so hot reload works.",
        ),
        steps=[
            (
                ["cred = sb.create_connect_token(user_metadata"],
                "A token that carries the user’s identity, for port 8080.",
                "create_connect_token(user_metadata, port=8080)",
                "Returns a URL and a token, both bound to this one Sandbox. The metadata rides inside the token and reaches the app as <code>X-Verified-User-Data</code>, which it cannot forge.",
                "<code>encrypted_ports</code> plus <code>tunnels()</code> for a public HTTPS URL with no auth.",
            ),
            (
                ['"authorization": f"Bearer'],
                "Whoever holds the token gets in: as a header from code, as a query parameter from a browser.",
                "Presenting the token",
                "<code>Authorization: Bearer</code> from code. In a browser, <code>?_modal_connect_token=</code> once, which sets a cookie. Websocket upgrades pass, so Vite’s hot reload works through it.",
                "The first version of the app prints <code>cred.url/?_modal_connect_token=…</code> and the user opens that. It works until the Sandbox sleeps: the next one has another URL. Steps 9 and 10 put one link in front.",
            ),
        ],
    )
)

slides.append(
    build_step(
        3,
        "Bring the model, keep the key out",
        "The agent needs a model. The key stays in a Sidecar that can reach one host; the Sandbox itself reaches npm only.",
        code=[
            ("# the Model Endpoint", "MODEL = "),
            ('.run_commands("npm install -g opencode', '"in-the-sidecar"})'),
            ("proxy = modal.Image", "proxy = modal.Image"),
            ('outbound_domain_allowlist=["registry', 'outbound_domain_allowlist=["inference'),
        ],
        summary=(
            "Sidecars, outbound_domain_allowlist, Secrets",
            "A second container holds the key and may reach the model host only; the Sandbox may reach the npm registry only. The agent talks to http://tools:8080.",
        ),
        steps=[
            (
                [
                    "MODEL = ",
                    '.run_commands("npm install -g opencode',
                    '.add_local_file("opencode.json"',
                    '.env({"OPENCODE',
                    '"MODAL_PROXY_TOKEN": "in-the-sidecar"',
                ],
                "OpenCode and its config: the model from MODEL, base URL http://tools:8080, and a dummy key inside.",
                "Image.add_local_file, Image.env",
                "<code>MODEL</code> is the host name of your Model Endpoint, the one setting to change. <code>opencode.json</code> reads it from the environment and points its base URL at the Sidecar. <code>MODAL_PROXY_TOKEN</code> inside is a dummy; the real one never enters the Sandbox.",
                "Any OpenAI-compatible endpoint: change the model id and the Sidecar’s <code>--to</code> host.",
            ),
            (
                ["proxy = modal.Image", '"caddy", "reverse-proxy"', '"--to", "https://inference', '"--header-up"'],
                "The Sidecar is stock Caddy, told what to do on its command line.",
                "A prebuilt Sidecar Image",
                "<code>reverse-proxy</code> to the model host, with the <code>Authorization</code> header filled from the Secret’s <code>AUTHORIZATION_BEARER</code>. Sidecar Images must exist before the Sidecar starts: <code>proxy.build(app)</code>. A named Image is refused there.",
                "mitmproxy when a tool needs TLS interception rather than a base URL.",
            ),
            (
                ['outbound_domain_allowlist=["registry'],
                "The Sandbox itself may reach the npm registry, nothing else.",
                "outbound_domain_allowlist",
                "DNS still resolves; connections to any other host are dropped. The agent can <code>npm install</code>, and nothing it writes can leave.",
                "<code>outbound_cidr_allowlist=[]</code> for no egress at all; <code>block_network=True</code> also forbids ports and tokens.",
            ),
            (
                [
                    "# the model key never enters",
                    "sb._experimental_sidecars.create(",
                    'name="tools", image=proxy.build(shop)',
                    'secrets=[modal.Secret.from_name("model-token")]',
                    'outbound_domain_allowlist=["inference',
                ],
                "The Sidecar, reachable as tools, holds the Secret and may reach the model host only.",
                "_experimental_sidecars.create(name, image, secrets, outbound_domain_allowlist)",
                "A second container in the Sandbox, reachable by name, with its own egress rules and its own Secrets. Up in about a second; torn down with the Sandbox.",
                "The key stays out, the use of it does not: anything inside can call the model through the Sidecar, so scope the token to this endpoint.",
            ),
        ],
    )
)

slides.append(
    build_step(
        4,
        "A message is a turn",
        "Each line the user types runs the agent once, and they see it work.",
        code=[
            ("def ask", 'print(); return ""'),
            ("    while msg := ask():", 'else: print(f"turn {len(turns)} {time.time()'),
        ],
        summary=(
            "exec, stdout streaming, returncode",
            "One exec of the agent per message, its stdout streamed to the user as it works, its exit code as the verdict.",
        ),
        steps=[
            (
                ["# one exec of the agent per message", "run = ('exec flock", "'opencode run --auto"],
                "The command: OpenCode once per message, behind a lock and a time limit, continuing its chat with -c.",
                "One turn at a time",
                "<code>flock /tmp/turn</code> holds a lock file for the life of the process: a second chat on the same project waits its turn, and the lock goes when the process does. <code>timeout -k 5 600</code> ends a turn that runs away, with everything it started: a polite signal at ten minutes, a kill 5 s later. <code>--</code> keeps a message that starts with a dash from being read as an option.",
                "OpenCode reads a non-TTY stdin to EOF, hence <code>&lt; /dev/null</code>: an open exec pipe makes it wait forever.",
            ),
            (
                ['p = sb.exec("sh", "-c", run'],
                "One exec per message typed at the prompt.",
                "sb.exec(*cmd)",
                "A process beside the entrypoint, with stdin, stdout and stderr. A running exec holds the idle clock for as long as it runs.",
                "<code>timeout=</code> on the exec stops the process it started and not that process’s children: here that would be <code>flock</code>, and the agent would run on holding the lock. Hence <code>timeout</code> inside.",
            ),
            (
                ["for chunk in p.stdout"],
                "Its stdout streams as it works: the user sees the trace.",
                "p.stdout",
                "Iterating yields chunks as they arrive, not whole lines. OpenCode prints each step (read, write, shell command) on stderr and only its last message on stdout, so <code>2&gt;&amp;1</code> puts both on the one stream: the first line is there about 3 s after the message.",
                "<code>p.stderr</code> read the same way, for the two apart; <code>text=False</code> for bytes.",
            ),
            (
                ['while sb.exec("flock", "-n", "/tmp/turn", "true").wait()', 'print("a turn is still running'],
                "Leave mid-turn and the agent finishes the turn. A chat that comes back waits for it.",
                "An exec outlives its client",
                "The agent runs in the Sandbox, not in this terminal. Ctrl-C or a closed terminal ends the client; the exec runs on and holds the idle clock. The next message probes the lock until it is free, so its Snapshot is of a finished turn.",
                "<code>undo</code> stops a turn that is still running; the ten-minute limit is the backstop, then the idle clock.",
            ),
            (
                ["if p.wait():", 'else: print(f"turn {len(turns)} {time.time()'],
                "wait() ends with the exit code: the proof line, or why it stopped.",
                "p.wait(), p.returncode",
                "Blocks until the process ends and returns the exit code. Zero: the turn and its seconds. Not zero: the turn stopped, and the stream above says why.",
                "<code>opencode serve</code> once and attach per message, about 1.5 s faster per turn.",
            ),
        ],
    )
)

slides.append(
    build_step(
        5,
        "Save every turn",
        "Before the agent touches anything, a Snapshot of the project: the state undo goes back to.",
        code=[
            ("# the app's own record", "turns_of = modal.Dict"),
            ("turns = checkpoint(sb, user)", "turns = checkpoint(sb, user)"),
            ("def checkpoint", "return turns"),
        ],
        summary=(
            "snapshot_directory, modal.Dict",
            "An Image of the project directory before every message, under a second, kept as a list of ids in a Dict.",
        ),
        steps=[
            (
                ["def checkpoint", "sb.snapshot_directory(", "turns_of[user] = turns", "return turns"],
                "A Snapshot of /project: an Image, under a second.",
                "snapshot_directory(path)",
                "An Image of one directory of the running Sandbox, kept 30 days unless <code>ttl=None</code>; the Sandbox keeps running. <code>/project</code> holds the app with its packages and, through <code>XDG_DATA_HOME</code>, the agent’s chat: 0.7 s for 54 MB.",
                "<code>snapshot_filesystem</code> for the whole box, which a new Sandbox can boot from.",
            ),
            (
                ["# the app's own record", "turns_of = modal.Dict"],
                "The turn list lives in a Dict: one list of Image ids per user.",
                "modal.Dict",
                "A named key-value store on Modal. Any process that knows the name reads and writes it, so the turns do not live on this laptop.",
                "Your own database; a Volume when the values are files.",
            ),
            (
                ["turns = checkpoint(sb, user)"],
                "Taken before the message runs, not after.",
                "Before, not after",
                "Whatever happens next (the agent finishes, fails, is stopped, or the terminal closes), the state before the message is already saved. Undo always takes back exactly one message.",
                "A Snapshot after the turn instead: an interrupted turn is then never recorded, and undo skips a step.",
            ),
        ],
    )
)

slides.append(
    build_step(
        6,
        "Undo",
        "Take back the last message: its Snapshot is an Image, mount it beside the project and sync the project to it.",
        code=[("def restore", "sb.unmount_image(path)"), ("def undo", 'print("turn", len(turns))')],
        summary=(
            "mount_image, unmount_image, Image.from_id",
            "A turn’s Image mounted at a path of the running Sandbox, then synced into the project. Hot reload flips the tab.",
        ),
        steps=[
            (
                ['path = f"/history/', "sb.mount_image(path", "sb.unmount_image(path)"],
                "mount_image puts the turn’s Image at a path of the running Sandbox; unmount_image takes it away.",
                "mount_image(path, Image.from_id(id)), unmount_image(path)",
                "Mounts an Image at a path of a running Sandbox, 0.2 s, no restart. Unmounting takes 0.1 s.",
                "Mounting over <code>/project</code> itself: the files are there at once, but the dev server never hears of it.",
            ),
            (
                ['sync = sb.exec("flock"', "if sync.wait()"],
                "rsync makes the project equal to the turn and touches only what differs.",
                "Sync, not mount over",
                "A file watcher gets no events from a mount, so the turn is synced in: changed files rewritten, extra ones deleted, the rest left alone, so Vite reloads the page and does not restart. 0.6 s, under the same lock as a turn.",
                "Packages installed by that message go too, and the agent forgets it: both are inside <code>/project</code>.",
            ),
            (
                [
                    "turns = turns_of.get(user, [])",
                    'if not turns: return print("nothing to undo")',
                    "restore(sb, turns.pop())",
                    "turns_of[user] = turns",
                    'print("turn", len(turns))',
                ],
                "undo restores the state saved before the last message, and drops it from the list.",
                "undo",
                "The last id in the Dict is the project as it was before the last message. Restore it, drop it: one message taken back, however that message ended.",
                "Fork: <code>Sandbox.create(image=snapshot)</code> from a Filesystem Snapshot gives a second Sandbox at that turn.",
            ),
            (
                ["sb = boot(user)", 'sb.exec("pkill"'],
                "Asleep or mid-turn, it still works.",
                "Any state",
                "<code>boot</code> returns the running Sandbox or wakes it from where it ended. A message still running, after the user left say, is killed first: the restore would otherwise wait for its lock.",
            ),
        ],
    )
)

slides.append(
    build_step(
        7,
        "Sleep",
        "Nothing running and no tab open: the Sandbox ends, and Modal keeps its filesystem.",
        code=[
            ("def running", "return None"),
            ("    sb = running(user)", "        return sb"),
            ("name=user, idle_timeout=30", 'experimental_options={"enable_exit_snapshot"'),
        ],
        summary=(
            "idle_timeout, name=, from_name, Exit Snapshots",
            "The open tab holds the idle clock; closing it ends the Sandbox, which leaves its filesystem behind. Named after the user, it is found again while it runs.",
        ),
        steps=[
            (
                ["name=user, idle_timeout=30"],
                "Named after the user; the idle clock at 30 s, held by the open tab.",
                "name=, idle_timeout, timeout",
                "Execs, stdin writes and open token or tunnel connections count as activity; closing the tab starts the 30 s, and an idle end is returncode 0. <code>timeout</code> is the hard cap.",
                "<code>AlreadyExistsError</code> when creating a second one with the name.",
            ),
            (
                ['experimental_options={"enable_exit_snapshot"'],
                "When it ends, for any reason, Modal keeps its filesystem: an Exit Snapshot.",
                'experimental_options={"enable_exit_snapshot": True}',
                "Opt-in at create. Whether the idle clock, the timeout, <code>terminate()</code> or the entrypoint ends the Sandbox, its whole filesystem is saved as an Image.",
                "A Memory Snapshot keeps the processes too, but taking one ends the Sandbox, and one Sandbox cannot enable both.",
            ),
            (
                [
                    "def running",
                    "try:",
                    "sb = modal.Sandbox.from_name(APP, user)",
                    "return sb if sb.poll() is None else None",
                    "except modal.exception.NotFoundError:",
                    "return None",
                    "sb = running(user)",
                    "if sb:",
                    'print("running"',
                    "return sb",
                ],
                "While it runs, from_name returns it: a second chat joins the same Sandbox.",
                "Sandbox.from_name(app_name, name), poll()",
                "One running Sandbox per name, found from any process; <code>NotFoundError</code> once it is gone. <code>poll()</code> is None while it runs: the name may still answer for a moment after the end.",
                "<code>sb.wait()</code> blocks until the end instead.",
            ),
        ],
    )
)

slides.append(
    build_step(
        8,
        "Come back",
        "The next message brings it back by name, with the filesystem it ended with.",
        code=[
            ("def asleep", "return base"),
            ("image=asleep(user)", "image=asleep(user)"),
            ("if sb.poll() is not None", "if sb.poll() is not None"),
        ],
        summary=(
            "from_name(include_terminated=True), _experimental_get_exit_snapshot",
            "The last Sandbox by that name left an Image of its filesystem. A new Sandbox boots from it: the project as it was left.",
        ),
        steps=[
            (
                ["def asleep", "last = modal.Sandbox.from_name(", "return last._experimental_get_exit_snapshot()"],
                "The last Sandbox by that name, ended or not, and the filesystem it ended with.",
                "from_name(include_terminated=True), _experimental_get_exit_snapshot()",
                "<code>include_terminated=True</code> returns the most recent Sandbox by that name after it ended. Its Exit Snapshot is an Image, 0.1 s to get once the Sandbox is gone.",
                "<code>timeout=</code> bounds the wait while the Snapshot is still being taken.",
            ),
            (
                ["except modal.Error:", "return base"],
                "No Sandbox by that name, or nothing kept: the base.",
                "modal.Error",
                "<code>NotFoundError</code> for a name never used, <code>InvalidError</code> when Exit Snapshots were not enabled, <code>SnapshotCreationError</code> when none will come. All are <code>modal.Error</code>.",
            ),
            (
                ["image=asleep(user) if turns_of.get(user) else base"],
                "A user with turns wakes from that Image; a new user starts from the base.",
                "Sandbox.create(image=)",
                "A Sandbox boots from an Exit Snapshot as from any Image, ready in about 1.5 s. It is the project exactly as it was left; the turns are only for going back.",
                "<code>_experimental_from_snapshot</code> restores a Memory Snapshot with the dev server still running: 1.1 s to the first page.",
            ),
            (
                ["if sb.poll() is not None"],
                "Mid-chat too: the next message brings it back.",
                "sb.poll()",
                "None while it runs, the returncode once it ended. The loop boots again. The new Sandbox has a new connect URL, which is what step 9 hides.",
            ),
        ],
    )
)

slides.append(
    build_step(
        9,
        "Optional: one link per user",
        "Every wake is a new Sandbox with a new URL. A Function in front gives each user one address that stays.",
        code=[
            ('"npm", "run", "dev"', '"npm", "run", "dev"'),
            ("@app.function(image=web", "        return cred"),
            ("    app.deploy()", "    app.deploy()"),
            ('print(f"open {modal.Function', 'print(f"open {modal.Function'),
        ],
        summary=(
            "Web Functions: @modal.asgi_app, @modal.concurrent, app.deploy",
            "A deployed Function with a URL. For each request it finds the user’s Sandbox, or wakes it, with the same boot the chat uses.",
        ),
        steps=[
            (
                ["@app.function(image=web", "@modal.concurrent", "@modal.asgi_app()", "def link()", "    app.deploy()"],
                "A Function with a URL: any ASGI app, here FastAPI, deployed once.",
                "@modal.asgi_app(), @modal.concurrent, app.deploy()",
                "Modal gives the Function a URL and runs it on demand: 5.1 and 5.7 s to the first answer when cold, 0.5 s warm. <code>concurrent</code> lets one container serve a page’s many requests at once; <code>timeout</code> bounds how long one tab’s websocket may live.",
                "<code>@modal.fastapi_endpoint</code> for one route; <code>requires_proxy_auth=True</code> when only scripts call it.",
            ),
            (
                [
                    "def door(user)",
                    "if time.time() - checked < 5",
                    "sb = running(user)",
                    "if not turns_of.get(user)",
                    "with waking: sb = boot(user)",
                ],
                "Find the user’s Sandbox, or wake it: the same boot the chat uses.",
                "The state is on Modal, so any code can find it",
                "The name finds the running Sandbox, the Dict says whether this user has a project, the Exit Snapshot is what it wakes from. The Function keeps nothing that matters: it remembers a door for 5 s, which is safe because the idle clock is 30 s, and that halves the time per request. One wake at a time: a second create with the same name is refused by Modal.",
                "A user with no project gets a 404, so guessing names wakes nothing.",
            ),
            (
                ['"npm", "run", "dev"', 'print(f"open {modal.Function'],
                "One Function for everyone: each user lives under /<user>/, and the dev server is told so.",
                "A path per user",
                "<code>--base /alice/</code> makes Vite serve and link everything under that prefix, so paths pass through unchanged.",
                "The link is public by user name. A secret in the path, a login in the Function, or <code>custom_domain=</code> on the Sandbox (Team plan, set up by Modal) are the ways to close or replace it.",
            ),
        ],
    )
)

slides.append(
    build_step(
        10,
        "Optional: pass it through",
        "The Function hands each request and the hot-reload websocket on to the Sandbox, presenting the connect token itself.",
        code=[("    @api.api_route", "    return api")],
        summary=(
            "A proxy in a Function: HTTP and websockets",
            "The address bar keeps the link, the token never reaches the browser, and the Sandbox still has no public port.",
        ),
        steps=[
            (
                [
                    "async def http",
                    "cred = await asyncio.to_thread(door, user)",
                    "r = await client.request(",
                    "return Response(",
                ],
                "Each request goes on to the Sandbox’s connect URL, token in a header.",
                "Proxy, not redirect",
                "The address bar keeps the link, and the token never reaches the browser: the Sandbox still has no public port. Measured from Stockholm, Function in us-east: 0.25 s per request on an open connection, against 0.045 s straight to the Sandbox. Five requests one after another: 2.0 s awake, 4.0 s when it has to wake first.",
                "A redirect to <code>cred.url/?_modal_connect_token=…</code> is five lines, but the address changes with every Sandbox and the token sits in the browser.",
            ),
            (
                [
                    "@api.websocket",
                    "async with websockets.connect(",
                    "await tab.accept(",
                    "async def down()",
                    "async def up()",
                ],
                "Hot reload is a websocket: open one to the Sandbox and pump both ways.",
                "Websockets through a Function",
                "Web Functions accept websockets. An edit in the Sandbox reached a client listening on the link in under 0.1 s: Vite’s update message, through two proxies.",
                "The open socket holds the Sandbox’s idle clock, as a direct tab does.",
            ),
        ],
    )
)

CSS = """
  .vc-ex { display: flex; flex-direction: column; height: 100%; min-height: 0; }
  .vc-ex .split { flex: 1; min-height: 0; }
  .vc-split { grid-template-columns: 1.3fr 0.7fr; align-items: start; }
  .vc-split pre.code { font-size: 13px; line-height: 20px; padding: 12px 16px; white-space: pre-wrap; word-break: break-word; overflow: hidden; }
  .vc-split pre.code--dense { font-size: 12.5px; line-height: 18.5px; padding: 10px 14px; }
  .vc-split pre.code--denser { font-size: 12px; line-height: 17px; padding: 10px 14px; }
  .vc-split pre.code--densest { font-size: 11.5px; line-height: 16px; padding: 8px 12px; }
  .vc-notes { min-height: 0; }
  .vc-notes .bnotes { display: none; flex-direction: column; gap: 14px; padding: 8px 2px; font-size: 16px; line-height: 23px; color: var(--semantic-text-primary); opacity: 1; visibility: visible; }
  .vc-notes .bnotes.on { display: flex; opacity: 1; visibility: visible; }
  .bnotes p { margin: 0; }
  .bnotes .lead { font-size: 17px; line-height: 24px; padding-bottom: 6px; border-bottom: 1px solid var(--semantic-border-secondary); }
  .bnotes .lead .n { display: inline-block; min-width: 22px; height: 22px; margin-right: 8px; border-radius: var(--radius-full); background: var(--semantic-background-accent); color: var(--semantic-text-accent); font-size: 12px; line-height: 22px; text-align: center; font-weight: 500; }
  .bnotes .k { display: block; margin-bottom: 2px; font-size: 11px; letter-spacing: .08em; text-transform: uppercase; font-weight: 600; color: var(--semantic-text-accent); }
  .bnotes code { font-family: var(--font-mono); font-size: 14px; color: var(--semantic-text-secondary); }
  .vc-demo pre.code { font-size: 15px; line-height: 26px; padding: 14px 18px; white-space: pre-wrap; margin-bottom: 18px; }
  .vc-demo pre.code .c { color: #9a9a8a; }
  .vc-demo ul.plain { font-size: 18px; line-height: 28px; }
  .vc-demo code { font-family: var(--font-mono); font-size: 16px; color: var(--semantic-text-secondary); }
  .vc-fig { margin: 0; height: 100%; display: flex; align-items: center; justify-content: center; }
  .vc-fig svg { width: 100%; height: auto; max-height: 100%; }
  .vc-box { fill: var(--semantic-background-elevated); stroke: var(--semantic-border-primary); }
  .vc-sb { fill: var(--semantic-background-recessed); stroke: var(--semantic-border-primary-hover); stroke-width: 1.5; }
  .vc-side { fill: var(--semantic-background-elevated); stroke: var(--semantic-text-accent); }
  .vc-tag { font-size: 10px; font-weight: 600; letter-spacing: .12em; fill: var(--semantic-text-tertiary); }
  .vc-snap { fill: var(--semantic-background-secondary); stroke: var(--semantic-border-secondary); }
  .vc-state { fill: none; stroke: var(--semantic-border-primary); }
  .vc-h { font-size: 17px; font-weight: 600; fill: var(--semantic-text-primary); }
  .vc-t { font-size: 15px; font-weight: 500; fill: var(--semantic-text-primary); }
  .vc-m { font-family: var(--font-mono); font-size: 14px; fill: var(--semantic-text-secondary); }
  .vc-s { font-size: 12.5px; fill: var(--semantic-text-tertiary); }
  .vc-a { fill: none; stroke: var(--semantic-border-primary-hover); stroke-width: 1.5; }
  .vc-head { fill: var(--semantic-border-primary-hover); }
  .vc-head-new { fill: var(--semantic-text-accent); }
  .vc-cap { display: none; }
  .vc-cap.on { display: inline; }
  .vc-later { opacity: .2; }
  .vc-staged .vc-side { stroke: var(--semantic-border-primary); }
  .vc-new .vc-box, .vc-new .vc-snap, .vc-new .vc-sb, .vc-new .vc-side, .vc-new .vc-state { stroke: var(--semantic-text-accent); stroke-width: 2; }
  .vc-new .vc-a { stroke: var(--semantic-text-accent); stroke-width: 2; }
  .vc-new .vc-s { fill: var(--semantic-text-accent); }
  .slide.title:has(.closing) footer { display: none; }
  .closing { display: flex; align-items: center; justify-content: space-between; gap: 80px; width: 100%; }
  .closing .cl-logo { width: 340px; margin-bottom: 48px; }
  .closing .cl-logo svg { display: block; width: 100%; height: auto; }
  .closing .cl-logo .on-light, [data-theme="light"] .closing .cl-logo .on-dark { display: none; }
  [data-theme="light"] .closing .cl-logo .on-light { display: block; }
  .closing .cl-url { margin: 8px 0 0; font-family: var(--font-mono); font-size: 22px; color: var(--semantic-text-primary); }
  .closing .cl-qr { flex: none; width: 320px; padding: 14px; border-radius: var(--radius-lg); background: #fff; }
  .closing .cl-qr svg { display: block; width: 100%; height: auto; }
"""
TITLE = "Creating a vibecoding platform"


def modal_logo(background: str) -> str:
    """Modal's logo for a dark or a light background: the file the Modal site offers for download, as it is.
    Both are on the page, one per theme, so the ids inside each get the background's name."""
    svg = (HERE / "assets" / ("modal-logo-%s-background.svg" % background)).read_text()
    return svg.replace('id="', 'id="%s-' % background).replace("url(#", "url(#%s-" % background)


# The closing slide: the Modal logo, and a QR code to the slides and the code. The code is drawn once, for
# the address below, and kept as a file:
#   uv run --with segno python -c "import segno; segno.make('https://github.com/nicolaslara/vibecoding-platform', error='m').save(
#       'slides/assets/closing-qr.svg', kind='svg', border=2, xmldecl=False, omitsize=True)"
closing = """<section class="slide title">
  <div class="title-block closing">
    <div><div class="cl-logo"><div class="on-dark">%s</div><div class="on-light">%s</div></div><h1>Thank you</h1>
      <p class="sub">The slides and the code:</p><p class="cl-url">%s</p></div>
    <div class="cl-qr">%s</div>
  </div>
  <footer><span class="src"></span><span class="pageno"></span></footer>
</section>""" % (
    modal_logo("dark"),
    modal_logo("light"),
    REPO,
    (HERE / "assets" / "closing-qr.svg").read_text(),
)
parts.append(dict(name="closing", title="Thank you", label="Thank you", opener=False, slides=[closing]))
parts.append(dict(name="walkthrough", title="The compact walkthrough", hidden=True, slides=slides))

# One more hidden slide at the very end: a picture, as large as the slide.
LAST = HERE / "assets" / "shots" / "dont-think.jpg"
picture = '<div class="ch-picture"><img src="data:image/jpeg;base64,%s" alt=""></div>'
last = slide(picture % base64.b64encode(LAST.read_bytes()).decode("ascii"), hidden=True)
parts.append(dict(name="last", title="One more", hidden=True, opener=False, slides=[last]))
SLIDES = intro + [s for p in parts for s in p["slides"]]
EXTRA_CSS = CSS + ANNOTATED_CSS + CHAPTER_CSS
if __name__ == "__main__":
    out = ROOT / "dist" / "index.html"
    out.parent.mkdir(exist_ok=True)
    render_deck(
        TITLE,
        parts,
        out,
        intro,
        tokens_href=str(HERE / "common/modal-tokens.css"),
        vendor_href=str(HERE / "common/vendor/reveal"),
        inline_assets=True,
        extra_css=EXTRA_CSS,
        repo=REPO,
    )
