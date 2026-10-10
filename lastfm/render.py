#!/usr/bin/env python3
"""Draws lastfm.svg (recent scrobbles) for the profile README. Stdlib only.
Env: LASTFM_API_KEY (required), LASTFM_USER (default madgeeked), MOCK=path.json for offline tests."""
import base64, json, os, sys, urllib.parse, urllib.request
from html import escape

USER = os.environ.get("LASTFM_USER", "madgeeked")
KEY = os.environ.get("LASTFM_API_KEY", "")
N = 5
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lastfm.svg")

def api(method, **p):
    q = urllib.parse.urlencode(dict(method=method, user=USER, api_key=KEY, format="json", **p))
    with urllib.request.urlopen("https://ws.audioscrobbler.com/2.0/?" + q, timeout=20) as r:
        return json.load(r)

def fetch(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "madgeeked-profile"})
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.read(), r.headers.get_content_type()
    except Exception:
        return None, None

def clip(s, n): return s if len(s) <= n else s[: n - 1].rstrip() + "…"

def load():
    if os.environ.get("MOCK"):
        return json.load(open(os.environ["MOCK"]))
    if not KEY: sys.exit("LASTFM_API_KEY is not set")
    rt = api("user.getrecenttracks", limit=N + 1)["recenttracks"]
    info = api("user.getinfo")["user"]
    return {"tracks": rt["track"], "plays": info.get("playcount", "")}

def main():
    d = load(); tr = d["tracks"][:N]
    W, row, top = 480, 54, 58
    H = top + row * len(tr) + 14
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="Poppins,Outfit,Helvetica,Arial,sans-serif">',
         '<defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ff9a5c"/><stop offset="1" stop-color="#ffc178"/></linearGradient>'
         f'<clipPath id="r"><rect width="{W}" height="{H}" rx="14"/></clipPath><clipPath id="a"><rect width="40" height="40" rx="7"/></clipPath></defs>',
         f'<g clip-path="url(#r)"><rect width="{W}" height="{H}" fill="url(#g)"/><rect y="46" width="{W}" height="{H-46}" fill="#3a2410" fill-opacity=".72"/>',
         '<text x="18" y="30" font-size="17" font-weight="600" fill="#fff">last.fm</text>']
    if d.get("plays"):
        o.append(f'<text x="{W-18}" y="30" font-size="13" fill="#fff" fill-opacity=".85" text-anchor="end">{int(d["plays"]):,} scrobbles</text>')
    for i, t in enumerate(tr):
        y = top + i * row
        live = (t.get("@attr") or {}).get("nowplaying") == "true"
        img = next((x["#text"] for x in t.get("image", []) if x.get("size") == "medium" and x.get("#text")), "")
        data, mime = fetch(img) if img else (None, None)
        o.append(f'<g transform="translate(18,{y})">')
        if data and mime and mime.startswith("image/"):
            o.append(f'<image width="40" height="40" clip-path="url(#a)" xlink:href="data:{mime};base64,{base64.b64encode(data).decode()}"/>')
        else:
            o.append('<rect width="40" height="40" rx="7" fill="#f2b33d"/>')
        name = escape(clip(t["name"], 38)); art = escape(clip(t["artist"].get("#text", t["artist"].get("name", "")), 42))
        o.append(f'<text x="52" y="17" font-size="14" font-weight="600" fill="#fff">{name}</text>'
                 f'<text x="52" y="35" font-size="12" fill="#ffd9a8">{art}</text>')
        if live:
            o.append(f'<text x="{W-36}" y="24" font-size="12" font-weight="600" fill="#ffd23f" text-anchor="end">now playing</text>')
        o.append('</g>')
    o.append('</g></svg>')
    open(OUT, "w", encoding="utf-8").write("".join(o))
    print("wrote", os.path.abspath(OUT), len(tr), "tracks")

main()
