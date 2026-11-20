"""Build the deck from the code: `uv run python slides/build.py` writes dist/index.html.

Nothing here runs the application or calls Modal. The chapter slides (slides/chapters.py) read the chapter
branches of this repository as text.
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
from common.deck import render_deck, slide, title_slide


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

intro = slides[:1]

CSS = """
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
