"""Renders assets/feed.svg: a pixel-art event log of the latest public commits."""
import datetime as dt
import json
import os
import urllib.request
from xml.sax.saxutils import escape

USER = "arinjaysaxena"
SKIP_REPOS = {f"{USER}/{USER}".lower()} | {
    f"{USER}/{name.strip().lower()}" for name in os.environ.get("FEED_SKIP", "").split(",") if name.strip()}
ROWS = 5
OUT = os.environ.get("FEED_OUT") or os.path.join(os.path.dirname(__file__), "..", "..", "assets", "feed.svg")
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))

W = 880
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"
INK, PANEL, HI, LO = "#0a0618", "#1b1238", "#2c1f57", "#120b28"
TEXT, MUTED, PINK, MINT, YELLOW = "#f3eaff", "#a99bd1", "#ff5a7a", "#8bf5cf", "#ffcf5a"
F = {
    "E": ["#####", "#    ", "#    ", "#### ", "#    ", "#    ", "#####"],
    "V": ["#   #", "#   #", "#   #", "#   #", "#   #", " # # ", "  #  "],
    "N": ["#   #", "##  #", "# # #", "#  ##", "#   #", "#   #", "#   #"],
    "T": ["#####", "  #  ", "  #  ", "  #  ", "  #  ", "  #  ", "  #  "],
    "L": ["#    ", "#    ", "#    ", "#    ", "#    ", "#    ", "#####"],
    "O": [" ### ", "#   #", "#   #", "#   #", "#   #", "#   #", " ### "],
    "G": [" ### ", "#   #", "#    ", "# ###", "#   #", "#   #", " ####"],
    " ": ["     "] * 7,
}


def esc(s):
    return escape(s, {'"': "&quot;"})


def api(path):
    req = urllib.request.Request(f"https://api.github.com{path}", headers={
        "Accept": "application/vnd.github+json", "User-Agent": "profile-feed"})
    token = os.environ.get("GH_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def first_line(s, n):
    s = (s or "").strip()
    s = s.splitlines()[0] if s else ""
    return s if len(s) <= n else s[: n - 1] + "…"


def collect():
    found = []
    for repo in api(f"/users/{USER}/repos?sort=pushed&per_page=8&type=owner"):
        full = repo["full_name"]
        if full.lower() in SKIP_REPOS or repo.get("fork"):
            continue
        try:
            commits = api(f"/repos/{full}/commits?per_page={ROWS}")
        except Exception:
            continue
        for c in commits:
            when = dt.datetime.fromisoformat(c["commit"]["author"]["date"].replace("Z", "+00:00"))
            found.append((when, repo["name"], c["commit"]["message"]))
    found.sort(key=lambda r: r[0], reverse=True)
    return [(w.astimezone(IST).strftime("%d %b %H:%M").upper(), name, msg) for w, name, msg in found[:ROWS]]


def ptext(t, x0, y0, s, color, shadow):
    out = []
    for dx, col in ((s, shadow), (0, color)):
        ci, rects = 0, []
        for ch in t:
            for c in range(5):
                for r in range(7):
                    if F[ch][r][c] == "#":
                        rects.append(f'<rect x="{x0 + ci * s + dx}" y="{y0 + r * s + dx}" width="{s}" height="{s}"/>')
                ci += 1
            ci += 1
        out.append(f'<g fill="{col}">{"".join(rects)}</g>')
    return "".join(out)


def render(rows):
    top, rp = 92, 30
    H = top + rp * max(len(rows), 1) + 14
    b = [f'<rect x="4" y="0" width="{W - 8}" height="{H}" fill="{INK}"/><rect x="0" y="4" width="{W}" height="{H - 8}" fill="{INK}"/>'
         f'<rect x="8" y="4" width="{W - 16}" height="{H - 8}" fill="{PANEL}"/><rect x="4" y="8" width="{W - 8}" height="{H - 16}" fill="{PANEL}"/>'
         f'<rect x="8" y="4" width="{W - 16}" height="4" fill="{HI}"/><rect x="8" y="{H - 8}" width="{W - 16}" height="4" fill="{LO}"/>',
         ptext("EVENT LOG", 32, 26, 3, "#fff", PINK),
         f'<g class="blink"><rect x="{32 + 53 * 3 + 14}" y="32" width="8" height="8" fill="{MINT}"/></g>'
         f'<text x="{32 + 53 * 3 + 28}" y="41" font-family="{MONO}" font-size="10" font-weight="700" letter-spacing="2" fill="{MINT}">LIVE</text>'
         f'<text x="{W - 32}" y="44" text-anchor="end" font-family="{MONO}" font-size="10.5" font-weight="700" letter-spacing="2" '
         f'fill="{MUTED}">LATEST COMMITS · AUTO-SAVED</text>'
         f'<rect x="28" y="62" width="{W - 56}" height="4" fill="{LO}"/>']
    if not rows:
        rows = [("-- --- --:--", "system", "no new transmissions yet")]
    style = ["@keyframes blink{0%,49%{opacity:1}50%,100%{opacity:0}}.blink{animation:blink 1s steps(1) infinite}"]
    t = 0.4
    for i, (when, repo, msg) in enumerate(rows):
        y = top + i * rp
        stamp, rname, text = f"[{when}]", repo, first_line(msg, 52)
        line = f"{stamp} ★ {rname}: {text}"
        n = len(line)
        w = n * 7.6
        b.append(f'<text x="32" y="{y}" font-family="{MONO}" font-size="12.5" font-weight="700" textLength="{w:.1f}" '
                 f'lengthAdjust="spacingAndGlyphs" xml:space="preserve">'
                 f'<tspan fill="{MINT}">{esc(stamp)}</tspan> <tspan fill="{YELLOW}">★</tspan> '
                 f'<tspan fill="{PINK}">{esc(rname)}</tspan><tspan fill="{MUTED}">:</tspan> <tspan fill="{TEXT}">{esc(text)}</tspan></text>')
        dur = n * 0.012
        style.append(f"@keyframes ty{i}{{from{{transform:scaleX(1)}}to{{transform:scaleX(0)}}}}"
                     f".ty{i}{{transform-box:fill-box;transform-origin:right;transform:scaleX(0);animation:ty{i} {dur:.2f}s steps({n}) {t:.2f}s backwards}}")
        b.append(f'<rect class="ty{i}" x="31" y="{y - 14}" width="{w + 4:.1f}" height="20" fill="{PANEL}"/>')
        t += dur + 0.15
    label = "Event log of latest commits. " + " ".join(f"{w}: {r}, {esc(first_line(m, 80))}." for w, r, m in rows)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" '
            f'aria-label="{label}" shape-rendering="crispEdges"><title>{label}</title><style>{"".join(style)}</style>'
            f'{"".join(b)}</svg>')


if __name__ == "__main__":
    svg = render(collect())
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(svg)
    print(f"wrote {OUT} ({len(svg) / 1024:.1f} KB)")
