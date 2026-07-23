#!/usr/bin/env python3
"""
Generic WordPress REST writer that shells out to curl (NOT urllib/requests),
because managed-host WAFs commonly 403 Python's User-Agent on POST/PUT while
letting curl through. See SKILL.md Golden Rule 1.

Use for any REST-writable field: media alt_text, elementor_snippet meta, etc.
NOT for Yoast post/term titles & descriptions (those aren't REST-writable —
use the Yoast bulk-editor / term.php techniques in references/writing-yoast-data.md).

Edit AUTH / SITE below or pass via env (WP_AUTH, WP_SITE), then edit ITEMS.
"""
import subprocess, json, os, sys

AUTH = os.environ.get("WP_AUTH", "user:xxxx xxxx xxxx xxxx xxxx xxxx")
SITE = os.environ.get("WP_SITE", "https://example.com").rstrip("/")


def rest_post(path, payload):
    """POST JSON to a REST path; returns (http_status:str, parsed_or_text)."""
    url = f"{SITE}/wp-json/wp/v2/{path.lstrip('/')}"
    out = subprocess.run(
        ["curl", "-s", "-u", AUTH, "-X", "POST", url,
         "-H", "Content-Type: application/json",
         "--data-binary", json.dumps(payload, ensure_ascii=False),
         "-w", "\n%{http_code}"],
        capture_output=True, text=True, timeout=60).stdout
    body, _, code = out.rpartition("\n")
    try:
        return code, json.loads(body)
    except Exception:
        return code, body


def rest_get(path):
    url = f"{SITE}/wp-json/wp/v2/{path.lstrip('/')}"
    out = subprocess.run(["curl", "-s", "-u", AUTH, url],
                         capture_output=True, text=True, timeout=60).stdout
    return json.loads(out)


# ---- Example: batch image alt text ----------------------------------------
# Map media id -> alt text (derive alt from filename + page context first).
ITEMS = {
    # 342: "Before and after chimney waterproofing in Burlington, MA by Top Dog Chimney",
}

if __name__ == "__main__":
    ok = fail = 0
    for mid, alt in ITEMS.items():
        code, res = rest_post(f"media/{mid}", {"alt_text": alt})
        got = (res.get("alt_text") if isinstance(res, dict) else "") or ""
        if code == "200" and got.strip() == alt:
            print(f"OK  {mid}"); ok += 1
        else:
            print(f"FAIL {mid} (HTTP {code})"); fail += 1
    print(f"\nUpdated: {ok} | Failed: {fail}")
    if not ITEMS:
        print("(ITEMS is empty — fill it in, or import rest_post/rest_get from this module.)")
