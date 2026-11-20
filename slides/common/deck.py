"""Shared runtime for the workshop decks, built on reveal.js (vendored under common/vendor/reveal).

A section folder builds its own deck:

    import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
    from common.deck import render, slide, title_slide, code, pill, chip, hl
    ...
    TITLE, OUT, SLIDES, EXTRA_CSS = "Rightsizing Sandboxes", "rightsizing-slides.html", slides, "..."
    if __name__ == "__main__":
        render(TITLE, SLIDES, OUT, EXTRA_CSS, part="rightsizing")

The root build.py imports every section and composes them with render_deck(): one reveal.js deck in
which each part is a horizontal stack and its slides run vertically.

Keys: left/right (and space, page keys) = previous/next slide, down/up = next/previous part, o = overview
grid, m = jump-to menu, z = zoom card, t = theme, s = speaker view, ? = every key. The menu and the overview
are keyboard-first: arrows move, Enter goes, Esc closes, and the deck ignores keys while one is open.
URL: ?hidden=1 includes the hidden slides, ?zoom=1 opens every zoom card, ?print-pdf then print to export.
"""

import base64
import html as _html
import mimetypes
import pathlib
import re

# ---------- small primitives ----------
from pygments import highlight as _pyg_highlight  # noqa: E402
from pygments.formatters import HtmlFormatter as _HtmlFormatter  # noqa: E402
from pygments.lexers import PythonLexer as _PythonLexer  # noqa: E402

_FORMATTER = _HtmlFormatter(nowrap=True, classprefix="tk-")


def hl(src: str) -> str:
    """Python highlighted by Pygments, one output line per input line, spans closed at every line end."""
    out = _pyg_highlight(src, _PythonLexer(ensurenl=False), _FORMATTER)
    return out[:-1] if out.endswith("\n") and not src.endswith("\n") else out


def _token_css() -> str:
    """Monokai token colours for pre.code; the panel keeps Monokai's dark background in both themes."""
    rules = _HtmlFormatter(style="monokai", classprefix="tk-").get_style_defs("pre.code").split("\n")
    keep = [r for r in rules if r.startswith("pre.code .tk-")]
    return (
        "\n".join("  " + r for r in keep)
        + "\n  pre.code { background: #272822; color: #f8f8f2; border-color: #3a3b32; }\n  pre.code .tk-c, pre.code .tk-c1, pre.code .tk-ch, pre.code .tk-cm, pre.code .tk-cs { color: #9a9a8a; }\n"
    )


def code(src: str, cls: str = "") -> str:
    return '<pre class="code %s">%s</pre>' % (cls, hl(src))


ICON_CHECK = '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/></svg>'
ICON_SPIN = '<svg viewBox="0 0 24 24" class="spin"><path d="M21 12a9 9 0 1 1-6.219-8.56"/></svg>'
ICON_X = '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><path d="m15 9-6 6"/><path d="m9 9 6 6"/></svg>'


def pill(kind: str, text: str) -> str:
    icon = {"success": ICON_CHECK, "danger": ICON_X}.get(kind, ICON_SPIN)
    cls = {
        "running": " md-status-pill--running",
        "success": " md-status-pill--success",
        "danger": " md-status-pill--danger",
    }.get(kind, "")
    return '<span class="md-status-pill%s">%s%s</span>' % (cls, icon, text)


def chip(text: str, kind: str = "") -> str:
    return '<span class="chip chip--%s">%s</span>' % (kind, text)


# ---------- slides ----------
def _notes(notes: str) -> str:
    return ('\n  <aside class="notes">%s</aside>' % notes) if notes else ""


def slide(
    body: str,
    kicker: str = "",
    title: str = "",
    sub: str = "",
    code_line: str = "",
    foot: str = "",
    cls: str = "",
    hidden: bool = False,
    strip: str = "",
    notes: str = "",
) -> str:
    head = ""
    if kicker:
        head += '<p class="kicker">%s</p>' % kicker
    if title:
        head += "<h1>%s</h1>" % title
    if code_line:
        head += code(code_line, "code--line")
    if sub:
        head += '<p class="sub">%s</p>' % sub
    return """<section class="slide %s"%s>
  <header>%s</header>
  <div class="body">%s</div>
  %s
  <footer><span class="src">%s</span><span class="pageno"></span></footer>%s
</section>""" % (
        cls,
        ' data-hidden="1"' if hidden else "",
        head,
        body,
        ('<div class="strip">%s</div>' % strip) if strip else "",
        foot,
        _notes(notes),
    )


def title_slide(kicker: str, title_html: str, sub: str = "", foot: str = "", notes: str = "") -> str:
    return """<section class="slide title">
  <div class="title-block"><p class="kicker">%s</p><h1>%s</h1>%s</div>
  <footer><span class="src">%s</span><span class="pageno"></span></footer>%s
</section>""" % (kicker, title_html, ('<p class="sub">%s</p>' % sub) if sub else "", foot, _notes(notes))


# ---------- composition helpers ----------
def _prep(s: str) -> str:
    """reveal.js owns the <section>; the slide chrome lives in a flex column inside it."""
    s = s.replace(' data-hidden="1"', ' data-visibility="hidden"')
    m = re.match(r"\s*(<section\b[^>]*>)(.*)(</section>)\s*$", s, re.S)
    if not m:
        raise ValueError("a slide must be exactly one <section>: %r" % s[:80])
    return '%s<div class="sl">%s</div>%s' % m.groups()


def scope_css(css: str, prefix: str) -> str:
    """Prefix every top-level selector so one part's rules cannot leak into another part."""
    out = []
    for line in css.split("\n"):
        stripped = line.lstrip()
        if stripped.startswith("@media"):
            raise ValueError("@media blocks are not supported in part CSS")
        if "{" in line and not stripped.startswith("@"):
            sel, rest = line.split("{", 1)
            sel = ", ".join("%s %s" % (prefix, s.strip()) for s in sel.split(",") if s.strip())
            line = "  %s {%s" % (sel, rest)
        out.append(line)
    return "\n".join(out)


def _assets_under(s: str, folder: str) -> str:
    """Relative src/href targets inside a part are relative to that part's folder."""
    return re.sub(r'((?:src|href)=")(?!(?:https?:)?//|/|#|\.\./|data:|mailto:)', r"\g<1>%s/" % folder, s)


# ---------- page ----------
CSS = (
    """
  html, body { height: 100%; background: var(--semantic-background-ground); }
  .reveal-viewport, html.reveal-full-page { background: var(--semantic-background-ground); color: var(--semantic-text-primary); }
  body { font-size: 16px; line-height: 24px; }
  .reveal { font-family: var(--font-sans); font-size: 16px; line-height: 24px; color: var(--semantic-text-primary); }
  .reveal .slides { text-align: left; }
  .reveal .slides > section, .reveal .slides > section > section { padding: 0; height: 720px; box-sizing: border-box; }
  .reveal .slides section.slide { background: var(--semantic-background-ground); }
  .reveal aside.notes { display: none; }
  .reveal .fragment { transition: none; }
  .reveal .controls { color: var(--semantic-text-accent); }
  .reveal .progress { height: 3px; background: var(--semantic-background-secondary); color: var(--semantic-text-accent); }
  .sl { display: flex; flex-direction: column; height: 100%; padding: 40px 56px 24px; box-sizing: border-box; }
  .slide.title .sl { justify-content: center; position: relative; }
  .slide.title footer { position: absolute; left: 56px; right: 56px; bottom: 24px; }
  code { font-family: var(--font-mono); font-size: 0.9em; color: var(--semantic-text-primary); background: var(--semantic-background-secondary); padding: 1px 6px; border-radius: var(--radius-sm); }
  kbd { font-family: var(--font-mono); font-size: 11px; padding: 0 5px; border-radius: var(--radius-sm); background: var(--semantic-background-secondary); color: var(--semantic-text-secondary); border: 1px solid var(--semantic-border-primary); }
  .kicker { margin: 0 0 4px; color: var(--semantic-text-accent); font-weight: 500; font-size: 13px; line-height: 16px; }
  header h1 { margin: 0; font-size: 30px; line-height: 36px; font-weight: 500; color: var(--semantic-text-primary); }
  header h1 .accent { color: var(--semantic-text-accent); }
  header h1 code { font-size: 0.85em; }
  header .sub { margin: 8px 0 0; font-size: 17px; line-height: 24px; color: var(--semantic-text-secondary); max-width: 1040px; }
  .body { flex: 1; min-height: 0; display: flex; flex-direction: column; justify-content: center; margin-top: 10px; overflow: hidden; }
  figure { margin: 0; padding: 8px 12px; border: 1px solid var(--semantic-border-elevated); border-radius: var(--radius-lg); background: var(--semantic-background-elevated); display: flex; align-items: center; justify-content: center; min-height: 0; max-height: 100%; box-sizing: border-box; }
  figure svg { display: block; width: auto; height: auto; max-width: 100%; max-height: 100%; color: var(--semantic-text-primary); font-family: var(--font-sans); }
  .strip { display: flex; justify-content: space-between; align-items: center; gap: 24px; margin-top: 10px; min-height: 40px; }
  .facts { display: flex; gap: 18px; align-items: center; }
  .fact { display: inline-flex; align-items: center; gap: 8px; font-size: 13px; line-height: 18px; color: var(--semantic-text-primary); white-space: nowrap; }
  .fl { font-size: 12px; font-weight: 500; color: var(--semantic-text-secondary); }
  .muted { color: var(--semantic-text-tertiary); }
  footer { display: flex; justify-content: space-between; gap: 24px; margin-top: 8px; font-size: 11px; line-height: 16px; color: var(--semantic-text-tertiary); font-family: var(--font-mono); }
  footer .src { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  footer .repo { flex: none; margin-left: auto; color: inherit; text-decoration: none; }
  footer .pageno { flex: none; }
  .slide.title h1 { font-size: 56px; line-height: 64px; font-weight: 500; margin: 0; color: var(--semantic-text-primary); }
  .slide.title h1 code { font-size: 0.9em; padding: 2px 10px; }
  .slide.title .accent { color: var(--semantic-text-accent); }
  .slide.title .sub { margin-top: 24px; font-size: 20px; line-height: 28px; color: var(--semantic-text-secondary); }
  .slide.title .kicker { font-size: 16px; margin-bottom: 16px; }
  pre.code { margin: 0; padding: 18px 22px; border-radius: var(--radius-lg); border: 1px solid var(--semantic-border-elevated); background: var(--semantic-background-elevated); font-family: var(--font-mono); font-size: 15px; line-height: 24px; color: var(--semantic-text-primary); white-space: pre; overflow: hidden; }
  pre.code .c { color: var(--semantic-text-tertiary); }
  pre.code .kw { color: var(--semantic-text-running); }
  pre.code .fn { color: var(--semantic-text-informational); }
  pre.code .str { color: var(--semantic-text-success); }
  pre.code .num { color: var(--semantic-dataviz-series-2); }
  pre.code--line { padding: 10px 16px; font-size: 18px; line-height: 26px; margin: 2px 0 0; }
  pre.code mark { background: var(--semantic-background-accent-active); color: inherit; border-radius: 3px; outline: 1px solid var(--semantic-border-accent); }
"""
    + _token_css()
    + """
  .md-status-pill { display: inline-flex; align-items: center; gap: 6px; white-space: nowrap; padding: 2px 8px; border-radius: var(--radius-full); font-weight: 500; font-size: 13px; line-height: 18px; --md-pill-bg: var(--semantic-background-secondary); --md-pill-text: var(--semantic-text-secondary); --md-pill-icon: var(--semantic-icon-secondary); color: var(--md-pill-text); background: var(--md-pill-bg); }
  .md-status-pill svg { width: 14px; height: 14px; color: var(--md-pill-icon); fill: none; stroke: currentColor; stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; }
  .md-status-pill--success { --md-pill-bg: var(--semantic-background-success); --md-pill-text: var(--semantic-text-success); --md-pill-icon: var(--semantic-icon-success); }
  .md-status-pill--running { --md-pill-bg: var(--semantic-background-running); --md-pill-text: var(--semantic-text-running); --md-pill-icon: var(--semantic-icon-running); }
  .md-status-pill--danger { --md-pill-bg: var(--semantic-background-danger); --md-pill-text: var(--semantic-text-danger); --md-pill-icon: var(--semantic-icon-danger); }
  .spin { animation: md-spin 1s linear infinite; }
  @keyframes md-spin { to { transform: rotate(360deg); } }
  .chip { display: inline-flex; align-items: center; height: 26px; padding: 0 12px; border-radius: var(--radius-full); background: var(--semantic-background-secondary); color: var(--semantic-text-secondary); font-size: 13px; font-weight: 500; white-space: nowrap; }
  .chip--caution { background: var(--semantic-background-caution); color: var(--semantic-text-caution); }
  .chip--danger { background: var(--semantic-background-danger); color: var(--semantic-text-danger); }
  .chip--success { background: var(--semantic-background-success); color: var(--semantic-text-success); }
  .chip--draft { background: var(--semantic-background-warning); color: var(--semantic-text-warning); }
  ul.plain { margin: 16px 0 0; padding-left: 22px; font-size: 20px; line-height: 32px; color: var(--semantic-text-primary); max-width: 1000px; }
  ul.plain li { margin-bottom: 10px; }
  /* zoom card: a floating overlay per slide, toggled with z or the Zoom in button */
  .details-btn { height: 28px; padding: 0 10px; border-radius: var(--radius-md); border: 1px solid var(--semantic-border-primary); background: var(--semantic-background-elevated); color: var(--semantic-text-primary); font: inherit; font-size: 13px; font-weight: 500; cursor: pointer; display: inline-flex; align-items: center; gap: 6px; }
  .details-btn:hover { background: var(--semantic-background-elevated-hover); }
  .details-btn--quiet { height: 22px; padding: 0 8px; font-size: 12px; font-weight: 400; color: var(--semantic-text-tertiary); background: none; border-color: var(--semantic-border-secondary); }
  .details-btn kbd { font-family: var(--font-mono); font-size: 11px; padding: 0 5px; border-radius: var(--radius-sm); background: var(--semantic-background-secondary); color: var(--semantic-text-secondary); }
  .zoom { position: absolute; left: 72px; right: 72px; top: 104px; padding: 16px 22px 14px; box-sizing: border-box; border-radius: var(--radius-xl); background: var(--semantic-background-informational); border: 1px solid var(--semantic-border-informational); box-shadow: 0 24px 64px rgba(0,0,0,0.45); z-index: 4; }
  .zoom[hidden] { display: none; }
  .zclose { position: absolute; top: 12px; right: 14px; width: 28px; height: 28px; border-radius: var(--radius-md); border: 1px solid var(--semantic-border-primary); background: var(--semantic-background-elevated); color: var(--semantic-text-primary); font: inherit; font-size: 16px; cursor: pointer; z-index: 1; }
  .ztitle { font-size: 18px; line-height: 24px; font-weight: 500; color: var(--semantic-text-primary); margin-bottom: 10px; }
  table.cases { border-collapse: collapse; width: 100%; font-size: 13px; line-height: 18px; }
  table.cases th, table.cases td { text-align: left; vertical-align: top; padding: 7px 10px; border-bottom: 1px solid var(--semantic-border-secondary); color: var(--semantic-text-primary); }
  table.cases th { font-weight: 500; color: var(--semantic-text-secondary); font-size: 12px; }
  table.cases td.who { white-space: nowrap; font-weight: 500; }
  table.cases a { color: var(--semantic-text-accent); text-decoration: none; }
  table.cases a + a { margin-left: 8px; }
  /* steps: fragments light up code lines, output lines and a note */
  .ln { display: block; margin: 0 -10px; padding: 0 10px; border-radius: 4px; transition: opacity .15s, background-color .15s; }
  .stepping .ln { opacity: 0.38; }
  .stepping .ln.on { opacity: 1; background: var(--semantic-background-accent-active); }
  .stepnotes { min-height: 48px; margin-top: 10px; }
  .reveal .slides .stepnote { display: none; font-size: 17px; line-height: 24px; color: var(--semantic-text-primary); }
  .reveal .slides .stepnote.on { display: block; }
  .stepnote .k { display: inline-block; min-width: 22px; height: 22px; margin-right: 8px; border-radius: var(--radius-full); background: var(--semantic-background-accent); color: var(--semantic-text-accent); font-size: 12px; line-height: 22px; text-align: center; font-weight: 500; }
  .stephint { font-size: 12px; color: var(--semantic-text-tertiary); }
  /* two-column code | result */
  .split { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; height: 100%; min-height: 0; }
  .split > * { min-height: 0; }
  .result { display: flex; flex-direction: column; border: 1px solid var(--semantic-border-elevated); border-radius: var(--radius-lg); background: var(--semantic-background-recessed); overflow: hidden; }
  .result-head { display: flex; justify-content: space-between; align-items: center; padding: 8px 14px; border-bottom: 1px solid var(--semantic-border-secondary); font-size: 12px; color: var(--semantic-text-secondary); }
  .result pre { margin: 0; padding: 14px 16px; font-family: var(--font-mono); font-size: 14px; line-height: 22px; color: var(--semantic-text-primary); white-space: pre-wrap; overflow: auto; flex: 1; }
  .result pre .hi { color: var(--semantic-text-accent); font-weight: 500; }
  /* cards grid */
  .cards { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; }
  .card { padding: 16px 18px; border: 1px solid var(--semantic-border-elevated); border-radius: var(--radius-lg); background: var(--semantic-background-elevated); font-size: 15px; line-height: 22px; color: var(--semantic-text-primary); }
  .card h3 { margin: 0 0 6px; font-size: 18px; line-height: 24px; font-weight: 500; }
  .card p { margin: 0 0 8px; color: var(--semantic-text-secondary); }
  .card .big { font-size: 28px; line-height: 32px; font-weight: 500; color: var(--semantic-text-primary); font-variant-numeric: tabular-nums; }
  table.t { border-collapse: collapse; width: 100%; font-size: 16px; border: 1px solid var(--semantic-border-secondary); border-radius: var(--radius-sm); overflow: hidden; }
  table.t th, table.t td { text-align: left; padding: 10px 14px; border-bottom: 1px solid var(--semantic-border-secondary); }
  table.t th { font-weight: 500; color: var(--semantic-text-secondary); background: var(--semantic-background-recessed); font-size: 13px; }
  table.t td.num { font-variant-numeric: tabular-nums; text-align: right; }
  table.t tr:last-child td { border-bottom: 0; }
  /* agenda of a combined deck */
  ol.agenda { list-style: none; margin: 0; padding: 0; display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; }
  ol.agenda a { display: grid; grid-template-columns: 44px 1fr; gap: 4px 16px; align-items: center; padding: 20px 22px; border: 1px solid var(--semantic-border-elevated); border-radius: var(--radius-lg); background: var(--semantic-background-elevated); text-decoration: none; color: var(--semantic-text-primary); }
  ol.agenda a:hover { border-color: var(--semantic-border-accent-hover); }
  ol.agenda .n { grid-row: 1 / 3; width: 44px; height: 44px; border-radius: var(--radius-full); border: 1px solid var(--semantic-border-primary); display: inline-flex; align-items: center; justify-content: center; font-size: 18px; color: var(--semantic-text-secondary); }
  ol.agenda .t { font-size: 24px; line-height: 30px; font-weight: 500; }
  ol.agenda .s { font-size: 15px; line-height: 22px; color: var(--semantic-text-secondary); }
  /* chrome outside the slides */
  #theme { position: fixed; right: 14px; top: 10px; z-index: 50; height: 28px; padding: 0 10px; border-radius: var(--radius-md); border: 1px solid var(--semantic-border-primary); background: var(--semantic-background-elevated); color: var(--semantic-text-secondary); font: inherit; font-size: 12px; cursor: pointer; opacity: 0.6; }
  #theme:hover { opacity: 1; }
  #menu { position: fixed; left: 0; top: 0; bottom: 0; width: 380px; z-index: 60; overflow: auto; padding: 20px 22px; box-sizing: border-box; background: var(--semantic-background-elevated); border-right: 1px solid var(--semantic-border-primary); font-size: 14px; line-height: 20px; }
  #menu[hidden] { display: none; }
  #menu .menu-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; font-weight: 500; color: var(--semantic-text-primary); }
  #menu ol { list-style: none; margin: 0; padding: 0; }
  #menu > ol > li { margin-bottom: 14px; }
  #menu > ol > li > a { font-weight: 500; color: var(--semantic-text-primary); }
  #menu ol ol { margin: 4px 0 0 14px; }
  #menu ol ol a { color: var(--semantic-text-secondary); }
  #menu a { text-decoration: none; display: block; padding: 2px 0; }
  #menu a:hover { color: var(--semantic-text-accent); }
  #menu a:focus { outline: none; color: var(--semantic-text-accent); }
  #overview { position: fixed; inset: 0; z-index: 60; overflow: auto; padding: 18px 28px 28px; box-sizing: border-box; background: var(--semantic-background-ground); }
  #overview[hidden] { display: none; }
  .ov-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; font-weight: 500; color: var(--semantic-text-primary); }
  .ov-keys { display: flex; gap: 8px; align-items: center; font-size: 12px; font-weight: 400; color: var(--semantic-text-secondary); }
  .ov-row { display: grid; grid-template-columns: 170px 1fr; gap: 14px; align-items: start; padding: 12px 0; border-top: 1px solid var(--semantic-border-secondary); }
  .ov-label { font-size: 14px; line-height: 20px; font-weight: 500; color: var(--semantic-text-primary); padding-top: 2px; }
  .ov-cells { display: flex; flex-wrap: wrap; gap: 12px 10px; }
  .ov-cell { display: block; width: 192px; text-decoration: none; color: var(--semantic-text-secondary); border-radius: 4px; outline: 2px solid transparent; outline-offset: 3px; }
  .ov-cell:focus, .ov-cell:hover { outline-color: var(--semantic-border-accent-hover); color: var(--semantic-text-primary); }
  .ov-cell.current .ov-frame { border-color: var(--semantic-text-accent); }
  .ov-cell.ov-off { opacity: 0.35; }
  .ov-cell.ov-off .ov-title::after { content: ' · off'; }
  .ov-row-off .ov-label { opacity: 0.5; }
  .ov-frame { width: 192px; height: 108px; overflow: hidden; border: 1px solid var(--semantic-border-primary); border-radius: 4px; background: var(--semantic-background-ground); pointer-events: none; }
  .ov-frame .sl { width: 1280px; height: 720px; transform: scale(0.15); transform-origin: 0 0; }
  .ov-title { display: block; margin-top: 4px; font-size: 11px; line-height: 14px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  @media print { #theme, #menu, #overview { display: none !important; } }
"""
)

JS = """
(function () {
  var q = location.search, root = document.documentElement;
  try { var saved = localStorage.getItem('sbx-theme'); if (saved) root.setAttribute('data-theme', saved); } catch (e) {}
  function toggleTheme() {
    var next = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    root.setAttribute('data-theme', next);
    try { localStorage.setItem('sbx-theme', next); } catch (e) {}
  }
  var menu = document.getElementById('menu'), grid = document.getElementById('overview');
  var keepZoom = /[?&]zoom/.test(q);
  function zoomCard() { var s = Reveal.getCurrentSlide(); return s && s.querySelector('.zoom'); }
  function toggleZoom(force) { var d = zoomCard(); if (!d) return; var open = force === undefined ? d.hidden : force; d.hidden = !open; }
  function esc(t) { return t.replace(/&/g, '&amp;').replace(/</g, '&lt;'); }

  // ---- hide and show from the overview: h toggles a slide, H its part; remembered per deck in localStorage.
  // reveal.js drops data-visibility="hidden" sections from the DOM at start, so every stack and slide is
  // registered first; "off" means detached from its parent, and showing one puts it back and calls Reveal.sync().
  var HKEY = 'sbx-hidden:' + location.pathname, REG = [];
  (function registry() {
    var top = Array.prototype.slice.call(document.querySelectorAll('.reveal .slides > section'));
    var stacks = top.some(function (t) { return t.querySelector('section'); });   // reveal.js adds .stack only later
    top.forEach(function (t, h) {
      if (!stacks) { REG.push({ key: 'deck/' + h, el: t, parent: t.parentNode, index: h, part: t.getAttribute('data-overview-part') || 'deck' }); return; }
      var cls = (t.className.match(/\\bp-[\\w-]+/) || ['h' + h])[0];
      REG.push({ key: cls + '/*', el: t, parent: t.parentNode, index: h, part: cls });
      Array.prototype.slice.call(t.children).forEach(function (sec, v) {
        if (sec.tagName === 'SECTION') REG.push({ key: cls + '/' + v, el: sec, parent: t, index: v, part: cls });
      });
    });
    var saved = null; try { saved = JSON.parse(localStorage.getItem(HKEY) || 'null'); } catch (e) {}
    if (saved) REG.forEach(function (r) { if (saved.indexOf(r.key) >= 0) r.el.setAttribute('data-visibility', 'hidden'); else r.el.removeAttribute('data-visibility'); });
  })();
  function isOff(r) { return r.el.parentNode !== r.parent; }
  function regOf(key) { return REG.filter(function (o) { return o.key === key; })[0]; }
  function saveHidden() { try { localStorage.setItem(HKEY, JSON.stringify(REG.filter(isOff).map(function (r) { return r.key; }))); } catch (e) {} }
  function setOff(r, off) {
    if (off === isOff(r)) return;
    if (off) r.el.remove();
    else { var next = REG.filter(function (o) { return o.parent === r.parent && o.index > r.index && !isOff(o); })[0]; r.parent.insertBefore(r.el, next ? next.el : null); }
  }
  function toggleOff(key, wholePart) {
    var r = regOf(key); if (!r) return;
    var target = wholePart ? regOf(r.part + '/*') : r;
    if (!target && wholePart) {
      var off = !isOff(r);
      REG.filter(function (item) { return item.part === r.part; }).forEach(function (item) { setOff(item, off); });
      saveHidden(); Reveal.sync(); refresh(); openOverlay(grid); return;
    }
    if (!target) return;
    setOff(target, !isOff(target)); saveHidden(); Reveal.sync(); refresh();
    openOverlay(grid); var a = grid.querySelector('a[data-key="' + key + '"]'); if (a) { a.focus(); a.scrollIntoView({ block: 'nearest' }); }
  }
  function overviewList() {
    var list = [], byPart = {};
    REG.forEach(function (r) {
      if (/\\/\\*$/.test(r.key)) { byPart[r.part] = { title: r.el.getAttribute('data-title') || textOf(r.el), cls: r.part, off: isOff(r), slides: [] }; list.push(byPart[r.part]); return; }
      if (!byPart[r.part]) { byPart[r.part] = { title: r.el.getAttribute('data-overview-part') || document.title, cls: (document.querySelector('.reveal').className.match(/\\bp-[\\w-]+/) || [''])[0], off: false, slides: [] }; list.push(byPart[r.part]); }
      var p = byPart[r.part], off = p.off || isOff(r), i = off ? null : Reveal.getIndices(r.el);
      p.slides.push({ el: r.el, key: r.key, off: off, h: i ? i.h : -1, v: i ? (i.v || 0) : -1, title: textOf(r.el) });
    });
    return list;
  }

  // ---- navigation: left/right walk the slides, down/up jump between parts (a part = one horizontal stack)
  function at() { var i = Reveal.getIndices(); return { h: i.h, v: i.v || 0 }; }
  function parts() { return Reveal.getHorizontalSlides(); }
  function nextPart() { var i = at(); if (i.h < parts().length - 1) Reveal.slide(i.h + 1, 0); }
  function prevPart() { var i = at(); if (i.v > 0) Reveal.slide(i.h, 0); else if (i.h > 0) Reveal.slide(i.h - 1, 0); }
  function next() { if (Reveal.nextFragment()) return; if (Reveal.availableRoutes().down) Reveal.down(); else nextPart(); }
  function prev() { if (Reveal.prevFragment()) return; var i = at(); if (i.v > 0) Reveal.up(); else if (i.h > 0) Reveal.slide(i.h - 1, 10000); }
  // Steps: every shown fragment advances the slide's step; elements with data-step light up when their step is current.
  function syncSteps() {
    var slide = Reveal.getCurrentSlide(); if (!slide) return;
    var f = Reveal.getIndices().f, n = (typeof f === 'number' && f >= 0) ? f + 1 : 0;
    slide.classList.toggle('stepping', n > 0);
    slide.querySelectorAll('[data-step]').forEach(function (el) { el.classList.toggle('on', +el.getAttribute('data-step') === n); });
  }

  // ---- outline, read from the deck once reveal.js has dropped the hidden slides
  function outline() {
    var list = [], byH = {}, top = parts(), stacks = top.some(function (t) { return t.classList.contains('stack'); });
    var deckCls = (document.querySelector('.reveal').className.match(/\\bp-[\\w-]+/) || [''])[0];
    Reveal.getSlides().forEach(function (s) {
      var i = Reveal.getIndices(s), h = i.h, v = i.v || 0, key = stacks ? h : (s.getAttribute('data-overview-part') || 0);
      if (!byH[key]) {
        var t = top[h], title = stacks ? (t.getAttribute('data-title') || textOf(t)) : (s.getAttribute('data-overview-part') || document.title);
        byH[key] = { title: title, cls: (t.className.match(/\\bp-[\\w-]+/) || [deckCls])[0], slides: [] };
        list.push(byH[key]);
      }
      byH[key].slides.push({ h: h, v: v, el: s, title: textOf(s) });
    });
    return list;
  }
  function textOf(el) { var t = el.querySelector('h1') || el.querySelector('.kicker'); return t ? t.textContent.trim() : 'slide'; }
  function href(h, v) { return '#/' + (h + 1) + (v ? '/' + (v + 1) : ''); }
  function link(s, cls, inner) {
    var key = s.key ? ' data-key="' + s.key + '"' : '';
    if (s.off) return '<a class="' + cls + ' ov-off" href="#"' + key + ' tabindex="0">' + inner + '</a>';
    return '<a class="' + cls + '" href="' + href(s.h, s.v) + '" data-h="' + s.h + '" data-v="' + s.v + '"' + key + '>' + inner + '</a>';
  }
  function buildMenu(list) {
    var html = '<div class="menu-head"><span>Jump to</span><kbd>m</kbd></div><ol>';
    list.forEach(function (p) {
      var rest = p.slides.length > 1 ? p.slides.slice(1) : [];
      html += '<li>' + link(p.slides[0], '', esc(p.title || p.slides[0].title));
      if (rest.length) html += '<ol>' + rest.map(function (s) { return '<li>' + link(s, '', esc(s.title)) + '</li>'; }).join('') + '</ol>';
      html += '</li>';
    });
    menu.innerHTML = html + '</ol>';
  }
  function buildOverview(list) {
    var html = '<div class="ov-head"><span>Overview</span><span class="ov-keys"><kbd>←</kbd><kbd>→</kbd> slide <kbd>↑</kbd><kbd>↓</kbd> part <kbd>enter</kbd> go <kbd>h</kbd> hide / show <kbd>H</kbd> the part <kbd>o</kbd> close</span></div>';
    list.forEach(function (p) {
      html += '<div class="ov-row' + (p.off ? ' ov-row-off' : '') + '"><div class="ov-label">' + esc(p.title) + (p.off ? ' · off' : '') + '</div><div class="ov-cells">';
      p.slides.forEach(function (s) { html += link(s, 'ov-cell', '<div class="ov-frame ' + p.cls + '"></div><span class="ov-title">' + esc(s.title) + '</span>'); });
      html += '</div></div>';
    });
    grid.innerHTML = html;
    var frames = grid.querySelectorAll('.ov-frame'), k = 0;
    list.forEach(function (p) { p.slides.forEach(function (s) {
      var sl = s.el.querySelector('.sl'), c = sl && sl.cloneNode(true);
      if (c) { c.querySelectorAll('.zoom').forEach(function (z) { z.hidden = true; }); c.querySelectorAll('a').forEach(function (a) { a.setAttribute('tabindex', '-1'); }); frames[k].appendChild(c); } k++;
    }); });
  }

  // ---- overlays: keyboard first, and the deck does not see keys while one is open
  function openOverlay(el) { closeOverlays(); el.hidden = false; markCurrent(el); var a = current(el); if (a) { a.focus(); a.scrollIntoView({ block: 'center' }); } }
  function closeOverlays() { [menu, grid].forEach(function (el) { el.hidden = true; }); }
  function openOverlayEl() { return !menu.hidden ? menu : !grid.hidden ? grid : null; }
  function toggleOverlay(el) { if (el.hidden) openOverlay(el); else closeOverlays(); }
  function current(el) { var i = at(); return el.querySelector('a[data-h="' + i.h + '"][data-v="' + i.v + '"]') || el.querySelector('a'); }
  function markCurrent(el) { var c = current(el); el.querySelectorAll('a.current').forEach(function (a) { a.classList.remove('current'); }); if (c) c.classList.add('current'); }
  // the stops of an overlay: its own links, one per slide, and never a link inside a slide's thumbnail
  function stops(el) { return Array.prototype.slice.call(el.querySelectorAll('a')).filter(function (a) { return !a.closest('.ov-frame'); }); }
  function moveIn(el, key) {
    var links = stops(el), cur = document.activeElement, i = links.indexOf(cur), target;
    if (i < 0) target = links[0];
    else if (el === grid) {
      var h = +cur.getAttribute('data-h'), v = +cur.getAttribute('data-v'), row = cur.closest('.ov-row');
      if (key === 'ArrowRight') target = links[i + 1] && links[i + 1].closest('.ov-row') === row ? links[i + 1] : null;
      else if (key === 'ArrowLeft') target = links[i - 1] && links[i - 1].closest('.ov-row') === row ? links[i - 1] : null;
      else {
        var rows = Array.prototype.slice.call(grid.querySelectorAll('.ov-row')), r = rows.indexOf(row) + (key === 'ArrowDown' ? 1 : -1);
        if (rows[r]) { var cands = stops(rows[r]); target = cands[Math.min(v, cands.length - 1)]; }
      }
    } else target = links[i + ((key === 'ArrowDown' || key === 'ArrowRight') ? 1 : -1)];
    if (target) { target.focus(); target.scrollIntoView({ block: 'nearest' }); }
  }
  // A key held with a modifier belongs to the browser or the terminal around the deck: Shift with an arrow
  // switches tabs in cmux, for one. The deck lets those pass and does not move.
  window.addEventListener('keydown', function (e) {
    if (e.metaKey || e.ctrlKey || e.altKey || (e.shiftKey && /^Arrow/.test(e.key))) e.stopImmediatePropagation();
  }, true);
  window.addEventListener('keydown', function (e) {
    var el = openOverlayEl(); if (!el || e.metaKey || e.ctrlKey || e.altKey) return;
    var k = e.key;
    if (k === 'Tab') return;
    if (k === 'Escape' || (k === 'm' && el === menu) || (k === 'o' && el === grid)) closeOverlays();
    else if (k === 'm') openOverlay(menu);
    else if (k === 'o') openOverlay(grid);
    else if (/^Arrow/.test(k)) moveIn(el, k);
    else if (el === grid && (k === 'h' || k === 'H')) { var f = document.activeElement, key = f && f.getAttribute('data-key'); if (key) toggleOff(key, k === 'H'); }
    else if (k === 'Enter' || k === ' ') { var a = document.activeElement; if (a && el.contains(a) && !a.classList.contains('ov-off')) a.click(); }
    else if (k === 'Home') el.querySelector('a').focus();
    else if (k === 'End') { var all = stops(el); all[all.length - 1].focus(); }
    e.preventDefault(); e.stopPropagation();
  }, true);
  document.addEventListener('click', function (e) {
    var b = e.target.closest('button'); if (b) b.blur();
    if (e.target.closest('.details-btn')) toggleZoom(true);
    else if (e.target.closest('.zclose')) toggleZoom(false);
    else if (e.target.closest('#theme')) toggleTheme();
    else if (e.target.closest('#overview a.ov-off')) e.preventDefault();
    else if (e.target.closest('#menu a, #overview a')) closeOverlays();
  });

  Reveal.initialize({
    width: 1280, height: 720, margin: 0, minScale: 0.05, maxScale: 4, center: false,
    hash: true, hashOneBasedIndex: true, transition: 'none', backgroundTransition: 'none',
    controls: false, progress: true, slideNumber: false, overview: false, help: true,
    showHiddenSlides: /[?&]hidden/.test(q),
    keyboard: {
      39: next, 76: next, 78: next, 34: next, 32: next,
      37: prev, 72: prev, 80: prev, 33: prev,
      40: nextPart, 74: nextPart,
      38: prevPart, 75: prevPart,
      35: function () { Reveal.slide(parts().length - 1, 10000); },
      90: function () { toggleZoom(); },
      84: toggleTheme,
      77: function () { toggleOverlay(menu); },
      79: function () { toggleOverlay(grid); },
      27: function () { var d = zoomCard(); if (d && !d.hidden) toggleZoom(false); }
    },
    plugins: [RevealNotes]
  }).then(function () {
    refresh();
    Reveal.registerKeyboardShortcut('← →  SPACE', 'Previous / next slide');
    Reveal.registerKeyboardShortcut('↓ ↑', 'Next / previous part');
    Reveal.registerKeyboardShortcut('O', 'Overview grid; h / H there hide or show a slide / a part');
    Reveal.registerKeyboardShortcut('M', 'Jump-to menu');
    Reveal.registerKeyboardShortcut('Z', 'Zoom card on this slide');
    Reveal.registerKeyboardShortcut('T', 'Light / dark theme');
    if (keepZoom) document.querySelectorAll('.zoom').forEach(function (d) { d.hidden = false; });
  });
  function refresh() {
    var all = Reveal.getSlides();
    all.forEach(function (s, k) { var n = s.querySelector('.pageno'); if (n) n.textContent = (k + 1) + ' / ' + all.length; });
    buildMenu(outline()); buildOverview(overviewList());
  }
  Reveal.on('slidechanged', function () { if (!keepZoom) document.querySelectorAll('.zoom').forEach(function (d) { d.hidden = true; }); syncSteps(); });
  Reveal.on('fragmentshown', syncSteps); Reveal.on('fragmenthidden', syncSteps); Reveal.on('ready', syncSteps);
})();
"""

PAGE = """<!doctype html>
<html lang="en" data-theme="dark">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%(title)s</title>
<link rel="stylesheet" href="%(tokens)s">
<link rel="stylesheet" href="%(vendor)s/reveal.css">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fira+Mono:wght@400;500&display=swap">
<style>%(css)s%(extra)s</style>
</head>
<body>
<div class="reveal%(cls)s"><div class="slides">
%(slides)s
</div></div>
<nav id="menu" hidden></nav>
<div id="overview" hidden></div>
<button type="button" id="theme" title="Theme (t)">Theme</button>
<script src="%(vendor)s/reveal.js"></script>
<script src="%(vendor)s/notes.js"></script>
<script>%(js)s</script>
</body>
</html>"""


def _write(out_path, title, body, extra_css, cls, tokens_href, vendor_href, count, inline_assets=False):
    page = PAGE % dict(
        title=_html.escape(title),
        tokens=tokens_href,
        vendor=vendor_href,
        css=CSS,
        extra=extra_css,
        cls=cls,
        slides=body,
        js=JS,
    )
    if inline_assets:
        page = _inline(page, pathlib.Path(out_path).resolve().parent, tokens_href, vendor_href)
    pathlib.Path(out_path).write_text(page)
    print("written", out_path, count, "slides")


def _inline(page: str, base: pathlib.Path, tokens_href: str, vendor_href: str) -> str:
    """Embed the token CSS and reveal.js in the page so the file stands alone.

    A deck that references ../common does not render in a viewer that only reads below the file's own folder,
    and cannot be mailed or copied on its own; a self-contained file can. The hrefs are resolved the way the
    browser would, relative to the HTML file.
    """

    def read(href):
        return (base / href).resolve().read_text()

    def embed_image(match):
        prefix, source, suffix = match.groups()
        if source.startswith(("data:", "http:", "https:", "//")):
            return match.group(0)
        image_path = (base / source).resolve()
        media_type = mimetypes.guess_type(image_path.name)[0] or "application/octet-stream"
        encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
        return f"{prefix}data:{media_type};base64,{encoded}{suffix}"

    page = re.sub(r"""(<img\b[^>]*\bsrc=["'])([^"']+)(["'])""", embed_image, page)
    page = page.replace('<link rel="stylesheet" href="%s">' % tokens_href, "<style>%s</style>" % read(tokens_href))
    page = page.replace(
        '<link rel="stylesheet" href="%s/reveal.css">' % vendor_href,
        "<style>%s</style>" % read(vendor_href + "/reveal.css"),
    )
    for name in ("reveal.js", "notes.js"):
        js = read("%s/%s" % (vendor_href, name)).replace("</script>", "<\\/script>")
        page = page.replace('<script src="%s/%s"></script>' % (vendor_href, name), "<script>%s</script>" % js)
    return page


def render(
    title: str,
    slides: list,
    out_path,
    extra_css: str = "",
    tokens_href: str = "../common/modal-tokens.css",
    part: str = "",
    vendor_href: str = "../common/vendor/reveal",
    inline_assets: bool = False,
) -> None:
    """One flat deck for a single section: left/right walk every slide. inline_assets embeds the CSS and JS."""
    css = scope_css(extra_css, ".p-" + part) if part else extra_css
    _write(
        out_path,
        title,
        "\n".join(_prep(s) for s in slides),
        css,
        (" p-" + part) if part else "",
        tokens_href,
        vendor_href,
        len(slides),
        inline_assets,
    )


def render_deck(
    title: str,
    parts: list,
    out_path,
    intro: list,
    tokens_href: str = "common/modal-tokens.css",
    vendor_href: str = "common/vendor/reveal",
    inline_assets: bool = False,
    extra_css: str = "",
    repo: str = "",
) -> None:
    """The combined deck. `intro` slides come first, one per horizontal step; each part is a vertical stack.

    parts: dicts with name (folder), title, sub, slides, extra_css. A part's own leading title slide is
    replaced by one that names it as Part n, so every stack opens the same way; a part with opener=False
    opens with its own first slide. label is the part's name in the jump menu. extra_css applies to the
    whole deck, unscoped. repo is where the deck's code lives, as host and path (github.com/owner/name):
    every slide's footer links to it.
    """
    sections, css, count = [], [], 0
    for s in intro:
        sections.append(_prep(s))
        count += 1
    for n, p in enumerate(parts, 1):
        slides = list(p["slides"])
        if p.get("opener", True):
            if slides and 'class="slide title"' in slides[0]:
                slides = slides[1:]
            slides.insert(0, title_slide("Part %d" % n, p["title"], p.get("sub", ""), p.get("foot", "")))
        stack = "\n".join(_assets_under(_prep(s), p["name"]) for s in slides)
        sections.append(
            '<section class="part p-%s" data-title="%s"%s>\n%s\n</section>'
            % (
                p["name"],
                _html.escape(p.get("label", "%d · %s" % (n, p["title"]))),
                ' data-visibility="hidden"' if p.get("hidden") else "",
                stack,
            )
        )
        css.append(scope_css(p.get("extra_css", ""), ".p-" + p["name"]))
        count += len(slides)
    body = "\n".join(sections)
    if repo:
        pageno = '<span class="pageno"></span>'
        body = body.replace(pageno, '<a class="repo" href="https://%s">%s</a>%s' % (repo, repo, pageno))
    _write(
        out_path,
        title,
        body,
        extra_css + "".join(css),
        "",
        tokens_href,
        vendor_href,
        count,
        inline_assets,
    )


def agenda(parts: list, first_section: int) -> str:
    """The agenda slide of a combined deck: one card per part, each a link into its stack."""
    items = "".join(
        '<li><a href="#/%d"><span class="n">%d</span><span class="t">%s</span><span class="s">%s</span></a></li>'
        % (first_section + k, k + 1, p["title"], p.get("sub", ""))
        for k, p in enumerate(parts)
    )
    return '<ol class="agenda">%s</ol>' % items
