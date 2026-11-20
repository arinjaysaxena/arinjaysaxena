"""Renders assets/feed.svg: a split-flap board of recent public GitHub activity."""
import datetime as dt
import json
import os
import random
import urllib.request
from xml.sax.saxutils import escape

USER = "arinjaysaxena"
SKIP_REPOS = {f"{USER}/{USER}"}
ROWS = 5
OUT = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "feed.svg")
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))

BG, STROKE, AMBER, TILE = "#0d0c0a", "#2a251d", "#ffb13b", "#17140f"
GREEN, MUTED, TEXT = "#62e28f", "#8a7f70", "#ece3d4"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"
SCRAMBLE = "ABCDEFGHJKLMNPRSTUVWXYZ0123456789#%"
FONT = {
    "L": ["#    "] * 6 + ["#####"],
    "I": [" ### "] + ["  #  "] * 5 + [" ### "],
    "V": ["#   #"] * 5 + [" # # ", "  #  "],
    "E": ["#####", "#    ", "#    ", "#### ", "#    ", "#    ", "#####"],
    "F": ["#####", "#    ", "#    ", "#### ", "#    ", "#    ", "#    "],
    "D": ["#### ", "#   #", "#   #", "#   #", "#   #", "#   #", "#### "],
    " ": ["     "] * 7,
}


def api(path):
    req = urllib.request.Request(f"https://api.github.com{path}", headers={
        "Accept": "application/vnd.github+json", "User-Agent": "profile-feed"})
    token = os.environ.get("GH_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def first_line(s, n):
    s = (s or "").strip().splitlines()[0] if (s or "").strip() else ""
    return s if len(s) <= n else s[: n - 1] + "…"


def collect():
    """Latest commits across the user's most recently pushed public repos."""
    found = []
    repos = api(f"/users/{USER}/repos?sort=pushed&per_page=8&type=owner")
    for repo in repos:
        full = repo["full_name"]
        if full in SKIP_REPOS or repo.get("fork"):
            continue
        try:
            commits = api(f"/repos/{full}/commits?per_page={ROWS}")
        except Exception:
            continue
        for c in commits:
            when = dt.datetime.fromisoformat(c["commit"]["author"]["date"].replace("Z", "+00:00"))
            found.append((when, repo["name"], c["commit"]["message"]))
    found.sort(key=lambda r: r[0], reverse=True)
    return [(w.astimezone(IST).strftime("%d%b %H:%M").upper(), name.upper()[:14], "COMMIT", msg)
            for w, name, msg in found[:ROWS]]


def led(text, x0, y0, p, r):
    out, ci = [], 0
    for ch in text:
        g = FONT[ch]
        for c in range(5):
            out += [f'<circle cx="{x0 + ci * p:.1f}" cy="{y0 + rr * p:.1f}" r="{r}"/>' for rr in range(7) if g[rr][c] == "#"]
            ci += 1
        ci += 1
    return "".join(out)


def render(rows):
    W, tw, th, pitch = 880, 12, 22, 14
    widths = [11, 14, 6]
    starts, c = [], 0
    for wd in widths:
        starts.append(c)
        c += wd + 1
    x0, top, rp = 30, 92, 36
    msg_x = x0 + c * pitch + 6
    H = top + rp * max(len(rows), 1) + 22
    rnd = random.Random(repr(rows))
    parts = [
        f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="14" fill="{BG}" stroke="{STROKE}"/>',
        f'<g fill="{AMBER}" filter="url(#glow)">{led("LIVE FEED", 31.5, 26, 3, 1.15)}</g>',
        f'<circle class="blink" cx="{31.5 + 9 * 18 + 6}" cy="35" r="3.4" fill="{GREEN}"/>',
        f'<text x="{W - 30}" y="38" text-anchor="end" font-family="{MONO}" font-size="10.5" letter-spacing="1.8" '
        f'fill="{MUTED}">AUTO-UPDATED FROM GITHUB</text>',
        f'<line x1="30" y1="54" x2="{W - 30}" y2="54" stroke="{STROKE}"/>',
    ]
    for lab, s in zip(["WHEN (IST)", "REPO", "EVENT"], starts):
        parts.append(f'<text x="{x0 + s * pitch}" y="78" font-family="{MONO}" font-size="10" letter-spacing="1.6" fill="{MUTED}">{lab}</text>')
    parts.append(f'<text x="{msg_x}" y="78" font-family="{MONO}" font-size="10" letter-spacing="1.6" fill="{MUTED}">DETAIL</text>')
    if not rows:
        rows = [("--", "NO SIGNAL", "--", "waiting for the next transmission")]
    for ri, (when, repo, kind, msg) in enumerate(rows):
        y = top + ri * rp
        for fi, field in enumerate((when, repo, kind)):
            color = GREEN if fi == 2 else AMBER
            for k in range(widths[fi]):
                col = starts[fi] + k
                x = x0 + col * pitch
                ch = field[k] if k < len(field) else " "
                parts.append(f'<rect x="{x}" y="{y}" width="{tw}" height="{th}" rx="2" fill="{TILE}"/>')
                if ch != " ":
                    d = 0.3 + ri * 0.28 + col * 0.02 + rnd.random() * 0.1
                    a, b = rnd.choice(SCRAMBLE), rnd.choice(SCRAMBLE)
                    common = f'x="{x + tw / 2}" y="{y + 16}" text-anchor="middle" style="animation-delay:{d:.2f}s"'
                    parts.append(f'<text {common} class="r1" fill="{AMBER}">{escape(a)}</text>')
                    parts.append(f'<text {common} class="r2" fill="{AMBER}">{escape(b)}</text>')
                    parts.append(f'<text {common} class="fn" fill="{color}">{escape(ch)}</text>')
                parts.append(f'<line x1="{x}" y1="{y + th / 2}" x2="{x + tw}" y2="{y + th / 2}" stroke="#050403"/>')
        parts.append(f'<text x="{msg_x}" y="{y + 15.5}" font-family="{MONO}" font-size="12" font-weight="400" '
                     f'fill="{TEXT}" fill-opacity=".85">{escape(first_line(msg, 44))}</text>')
    style = (
        ".r1,.r2{opacity:0}.r1,.r2,.fn{animation-duration:.3s;animation-fill-mode:backwards;animation-timing-function:steps(1,end)}"
        "@keyframes r1{0%{opacity:1}33%,100%{opacity:0}}.r1{animation-name:r1}"
        "@keyframes r2{0%{opacity:0}33%{opacity:1}66%,100%{opacity:0}}.r2{animation-name:r2}"
        "@keyframes fn{0%{opacity:0}66%,100%{opacity:1}}.fn{animation-name:fn}"
        "@keyframes blink{0%,55%{opacity:1}56%,100%{opacity:.15}}.blink{animation:blink 1.6s infinite}"
    )
    glow = ('<filter id="glow" x="-5%" y="-40%" width="110%" height="180%"><feGaussianBlur in="SourceGraphic" '
            'stdDeviation="2.6" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>')
    label = "Live feed of recent public activity. " + " ".join(f"{w}: {k} {r}, {escape(first_line(m, 80), {chr(34): '&quot;'})}." for w, r, k, m in rows)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" '
            f'aria-label="{label}"><title>{label}</title><style>{style}</style><defs>{glow}</defs>'
            f'<g font-family="{MONO}" font-size="15" font-weight="700">{"".join(parts)}</g></svg>')


if __name__ == "__main__":
    svg = render(collect())
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(svg)
    print(f"wrote {OUT} ({len(svg) / 1024:.1f} KB)")
