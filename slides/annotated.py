"""Hand-written callouts over the application diagram: which Modal feature each box and arrow is."""

import base64
from pathlib import Path

FONT = base64.b64encode((Path(__file__).parent / "assets/annotation-hand.ttf").read_bytes()).decode()
CSS = """
  @font-face { font-family: AnnotationHand; src: url(data:font/ttf;base64,FONTDATA); }
  .arch-notes { height: 100%; }
  .arch-notes .vc-fig { height: 100%; border: 0; background: none; padding: 0; }
  .arch-notes .vc-fig svg { width: 100%; height: 100%; }
  .arch-notes .annotation { stroke: var(--semantic-text-accent); stroke-width: 4; fill: none; stroke-linecap: round; }
  .arch-notes .hand { font-family: AnnotationHand, cursive; fill: var(--semantic-text-accent); font-size: 30px; }
""".replace("FONTDATA", FONT)

# Each callout: the chapter that adds the part it names, whether it sits in the diagram's shifted group
# (everything right of the left column), and its SVG. In a chapter built in steps, a callout also names the
# step that adds it, and one that a later step redraws names the last step it is drawn for. Coordinates are in the diagram's own viewBox
# (0 0 1240 545), which annotate() widens so the callouts fit. They are placed by hand: after any change to
# diagram() in build.py, render the slides that use them and move them.
OUTER, INNER = False, True
MARKS = [
    (2, OUTER, """<text class="hand" x="256" y="6" transform="rotate(-3 256 6)">connect token</text>
<path class="annotation" d="M306 14 Q313 38 311 62 M311 62 L303 50 M311 62 L319 51"/>""", 4),
    (7, OUTER, """<path class="annotation" d="M21 86 Q140 77 259 87 L261 157 Q140 165 22 158 Z"/>
<text class="hand" style="font-size:24px" x="266" y="158" transform="rotate(-3 266 158)">Function</text>""", 1),
    (3, OUTER, """<text class="hand" x="262" y="386" transform="rotate(-6 262 386)">exec</text>
<path class="annotation" d="M292 356 Q318 300 322 228 M322 228 L314 242 M322 228 L331 241"/>""", 2),
    (6, OUTER, """<path class="annotation" d="M92 558 Q84 544 96 527 M96 527 L88 537 M96 527 L104 536"/>
<text class="hand" x="104" y="568" transform="rotate(-2 104 568)">Dict</text>""", 1),
    (2, INNER, """<text class="hand" x="480" y="12" transform="rotate(-3 480 12)">Sandbox, by name</text>
<path class="annotation" d="M478 22 Q590 33 716 23 M320 35 Q592 19 881 38 L882 164 M883 254 L882 414"/>""", 2),
    (2, INNER, """<text class="hand" x="496" y="72" transform="rotate(-3 496 72)">Probe</text>
<path class="annotation" d="M486 78 Q470 80 462 88"/>""", 5),
    (2, INNER, """<path class="annotation" d="M627 102 Q740 107 852 100"/>
<text class="hand" x="900" y="114" transform="rotate(-3 900 114)">idle_timeout</text>
<path class="annotation" d="M894 110 Q876 106 860 101"/>""", 1),
    (4, INNER, """<text class="hand" style="font-size:26px" x="896" y="164" transform="rotate(-2 896 164)">outbound policy</text>
<path class="annotation" d="M862 171 Q970 161 1079 172 L1082 248 Q970 258 863 249 Z"/>"""),
    (6, INNER, """<path class="annotation" d="M578 398 Q562 404 550 422 M550 422 L551 409 M550 422 L562 416"/>
<text class="hand" style="font-size:26px" x="584" y="396" transform="rotate(-2 584 396)">create(image=…)</text>""", 2),
    (6, INNER, """<path class="annotation" d="M354 558 Q346 544 358 527 M358 527 L350 537 M358 527 L366 536"/>
<text class="hand" x="366" y="568" transform="rotate(-2 366 568)">snapshot_filesystem</text>""", 1),
    (5, INNER, """<path class="annotation" d="M644 558 Q636 544 648 527 M648 527 L640 537 M648 527 L656 536"/>
<text class="hand" x="656" y="568" transform="rotate(-2 656 568)">Exit Snapshot</text>"""),
    (2, INNER, """<path class="annotation" d="M921 455 Q1040 443 1160 456 L1163 528 Q1040 536 922 527 Z"/>
<text class="hand" x="1000" y="566" transform="rotate(-2 1000 566)">Image</text>""", 3),
    (1, INNER, """<path class="annotation" d="M921 323 Q1040 312 1160 324 L1163 400 Q1040 410 922 400 Z"/>
<text class="hand" style="font-size:26px" x="986" y="306" transform="rotate(-3 986 306)">Model Endpoint</text>"""),
]  # fmt: skip

# Callouts that belong to one chapter's own drawing and not to the finished picture.
ONLY = [
    (0, OUTER, """<path class="annotation" d="M21 179 Q140 170 259 180 L262 283 Q140 292 22 284 Z"/>
<text class="hand" x="34" y="330" transform="rotate(-3 34 330)">a prompt, on the laptop</text>"""),
    (1, INNER, """<text class="hand" x="944" y="442" transform="rotate(-3 944 442)">its key: a Secret</text>"""),
    (2, INNER, """<text class="hand" x="480" y="12" transform="rotate(-3 480 12)">Sandbox</text>
<path class="annotation" d="M478 22 Q530 29 588 22 M320 35 Q592 19 881 38 L882 164 M883 254 L882 414"/>""", 1, 1),
    (3, INNER, """<text class="hand" x="530" y="398" transform="rotate(-2 530 398)">the key is inside, for now</text>""", 3),
    (3, INNER, """<path class="annotation" d="M921 455 Q1040 443 1160 456 L1163 528 Q1040 536 922 527 Z"/>
<text class="hand" style="font-size:26px" x="930" y="566" transform="rotate(-2 930 566)">Image, with the agent</text>""", 1, 3),
]  # fmt: skip

LABEL = (
    "Every Modal feature in the application: connect token, web Function, exec, Dict, Sandbox by "
    "name, readiness probe, idle timeout, outbound policy, a Sandbox from a Snapshot, "
    "snapshot_filesystem, Exit Snapshot, Image, Model Endpoint"
)


def shown_at(mark, step) -> bool:
    """Whether a callout is drawn at a step of its chapter. With no step, the chapter's finished picture."""
    first = mark[3] if len(mark) > 3 else 1
    last = mark[4] if len(mark) > 4 else None
    return last is None if step is None else first <= step <= (last or step)


def annotate(diagram: str, chapter=None, step=None) -> str:
    """The diagram's SVG with callouts drawn on top: all of them, those of the parts one chapter adds, or
    those of that chapter's steps up to one of them."""
    viewbox = 'viewBox="0 0 1240 545"'
    if viewbox not in diagram or "</svg>" not in diagram:
        raise SystemExit("slides/annotated.py: the diagram's viewBox changed, the callout coordinates need a pass")
    marks = MARKS if chapter is None else [m for m in MARKS + ONLY if m[0] == chapter]
    if chapter is not None:
        marks = [m for m in marks if shown_at(m, step)]
    drawn = '<g aria-label="%s">%s<g transform="translate(60 0)">%s</g></g>' % (
        LABEL if chapter is None else "The Modal features this chapter adds",
        "".join(m[2] for m in marks if not m[1]),
        "".join(m[2] for m in marks if m[1]),
    )
    diagram = diagram.replace(viewbox, 'viewBox="0 -24 1270 604"')
    return '<div class="arch-notes">' + diagram.replace("</svg>", drawn + "</svg>") + "</div>"
