#!/usr/bin/env python3
"""
Build a paste-ready AI-image-prompt document for a set of locations (or any
items), each block = fixed style block + per-item scene + a fetched real
reference image URL (with its license) from Wikimedia Commons.

Use when generating a cohesive set of evocative location images in an AI tool
(ChatGPT/GPT-4o etc). The output is original; the reference only guides — prefer
PD/CC0 references when feeding to AI (see references/acf-and-media.md).

Edit STYLE, ITEMS, and OUT_PATH, then run. No API key needed (Commons API).
"""
import subprocess, json, re, time, urllib.parse

UA = "SiteSEO/1.0 (you@example.com)"   # set a real contact UA
API = "https://commons.wikimedia.org/w/api.php"
OUT_PATH = "/tmp/image-prompts.md"

STYLE = ("Photorealistic editorial real-estate photography, natural warm daylight, early-autumn New England, "
         "eye-level, shallow depth of field, crisp and inviting. A well-maintained classic red-brick chimney is "
         "clearly visible on the roof and is structurally correct and realistic — clean mortar joints, proper "
         "brick coursing, a simple metal chimney cap. No text, no logos, no watermarks, no visible faces, no "
         "distorted or impossible architecture. Landscape 3:2, 1536x1024.")

# (item_name, commons_search_term, per-item scene line)
ITEMS = [
    ("Plymouth, MA", "Plymouth Massachusetts waterfront",
     "a historic colonial clapboard saltbox home on Plymouth's waterfront, the harbor softly blurred"),
    # ... add your items
]

def _api(p):
    q = "&".join(f"{k}={v}" for k, v in p.items())
    return json.loads(subprocess.run(["curl", "-s", "-H", f"User-Agent: {UA}", f"{API}?{q}&format=json"],
                                     capture_output=True, text=True, timeout=60).stdout)

def _info(title):
    d = _api({"action": "query", "titles": urllib.parse.quote(title),
              "prop": "imageinfo", "iiprop": "url|size|extmetadata"})
    pg = list(d["query"]["pages"].values())[0]
    ii = (pg.get("imageinfo") or [{}])[0]
    em = ii.get("extmetadata", {}) or {}
    g = lambda k: (em.get(k, {}) or {}).get("value", "")
    return {"url": ii.get("url", ""), "w": ii.get("width", 0),
            "lic": g("LicenseShortName"), "artist": re.sub(r"<[^>]+>", "", g("Artist")).strip()[:60]}

OKLIC = re.compile(r"(CC0|public domain|CC BY)", re.I)
BADLIC = re.compile(r"(NC|ND|non-?commercial|no deriv|all rights)", re.I)
BADT = re.compile(r"(map|logo|seal|diagram|chart|\.svg|\.pdf|engraving|lithograph|postcard|portrait|coat of arms)", re.I)
GOODT = re.compile(r"(downtown|main st|historic|center|common|town hall|harbor|street|house|waterfront|village)", re.I)

def pick_reference(term):
    d = _api({"action": "query", "list": "search", "srsearch": urllib.parse.quote(term),
              "srnamespace": "6", "srlimit": "15"})
    best = None
    for r in d.get("query", {}).get("search", []):
        t = r["title"]
        if BADT.search(t):
            continue
        m = _info(t); time.sleep(0.12)
        if not m["lic"] or BADLIC.search(m["lic"]) or not OKLIC.search(m["lic"]) or m["w"] < 900:
            continue
        s = (3 if GOODT.search(t) else 0) + (2 if re.search(r"CC0|public domain", m["lic"], re.I) else 0)
        if not best or s > best[0]:
            best = (s, m)
    return best[1] if best else None

def build():
    lines = ["# AI Image Prompts", "",
             "Upload one of your OWN photos as a style reference first, then paste a block.", "", "---", ""]
    for name, term, scene in ITEMS:
        ref = pick_reference(term); time.sleep(0.25)
        url = ref["url"] if ref else "(no clean reference found — rely on the text)"
        cred = f"{ref['lic']}{', ' + ref['artist'] if ref and ref['artist'] else ''}" if ref else "n/a"
        prompt = (f"Use the photo at this URL as a reference for the local character of {name}: {url} . "
                  f"Then create an ORIGINAL image (do not copy it): {STYLE} Scene: {scene}.")
        lines += [f"## {name}", "", f"**Reference:** {url}  _( {cred} — AI reference only)_", "",
                  "**Prompt:**", "", f"> {prompt}", "", "---", ""]
    open(OUT_PATH, "w").write("\n".join(lines))
    print("wrote", OUT_PATH)

if __name__ == "__main__":
    build()
