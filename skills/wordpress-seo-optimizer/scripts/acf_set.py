#!/usr/bin/env python3
"""
Set ACF fields (incl. image fields) on a post/CPT via REST, safely.

Two prerequisites (see references/acf-and-media.md):
  1. The field group must have "Show in REST API" enabled (browser, ACF editor).
  2. ACF validates ALL required fields on write — so we read the full acf object,
     modify only what we want, and POST everything back.

Image fields take an attachment ID (integer). On read they come back as an
object {ID,url,...}; this script resends just the ID. Uses curl (Golden Rule 1).

Edit AUTH/SITE (or env WP_AUTH/WP_SITE), then call set_fields().
"""
import subprocess, json, os

AUTH = os.environ.get("WP_AUTH", "user:xxxx xxxx xxxx xxxx xxxx xxxx")
SITE = os.environ.get("WP_SITE", "https://example.com").rstrip("/")


def _curl(args):
    return subprocess.run(["curl", "-s", "-u", AUTH] + args,
                          capture_output=True, text=True, timeout=90).stdout


def get_acf(post_type, pid):
    out = _curl([f"{SITE}/wp-json/wp/v2/{post_type}/{pid}?_fields=acf&nc=x"])
    return json.loads(out).get("acf", {})


def set_fields(post_type, pid, changes):
    """changes: dict of {field_name: value}. Image fields -> attachment ID (int)."""
    acf = get_acf(post_type, pid)
    if not isinstance(acf, dict):
        return (pid, "ERR", "acf not exposed in REST — enable 'Show in REST API' on the field group")
    payload = {}
    for k, v in acf.items():
        if isinstance(v, dict) and "ID" in v:      # image/file already set -> send ID
            payload[k] = v["ID"]
        elif isinstance(v, (list, dict)):
            continue                                # skip empty/complex we're not touching
        else:
            payload[k] = v                          # text/textarea/wysiwyg -> as-is
    payload.update(changes)
    body = json.dumps({"acf": payload}, ensure_ascii=False)
    out = _curl(["-X", "POST", f"{SITE}/wp-json/wp/v2/{post_type}/{pid}",
                 "-H", "Content-Type: application/json", "--data-binary", body,
                 "-w", "\n%{http_code}"])
    bd, _, code = out.rpartition("\n")
    if code == "200":
        return (pid, "200", "ok")
    try:
        return (pid, code, json.loads(bd).get("message"))
    except Exception:
        return (pid, code, bd[:160])


if __name__ == "__main__":
    # Example: set both image fields on a service_area post (both required -> send together)
    # print(set_fields("service_area", 735, {"area_about_image": 467, "area_why_image": 900}))
    print("Edit the __main__ block: set_fields('<cpt>', <id>, {'<field>': <attachment_id>, ...})")
