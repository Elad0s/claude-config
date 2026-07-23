# Injecting JSON-LD structured data

Two complementary techniques. Use **both**: the Elementor snippet for the one global business entity, and the WPCode PHP snippet for per-page item schema. They link together via a shared `@id`.

Before adding anything, fetch a few representative pages and list existing `@type`s (match `<script[^>]*application/ld\+json[^>]*>` because Yoast's tag has a `class`). Yoast already supplies `WebSite`, `Organization`, `WebPage`, `BreadcrumbList`; widgets sometimes add `FAQPage`. Don't duplicate those.

## A) Global LocalBusiness — Elementor Custom Code snippet (REST-writable)

Elementor Pro's "Custom Code" is the CPT `elementor_snippet`, and unlike Yoast meta it **is** writable via REST. Build the JSON-LD `@graph` (one `LocalBusiness`/`HomeAndConstructionBusiness` node with `@id` = `<site>/#localbusiness`, NAP, `areaServed`, `hasOfferCatalog` of services, and `aggregateRating`/`review` ONLY with real data), then:

```bash
# create
curl -s -u "$AUTH" -X POST "$SITE/wp-json/wp/v2/elementor_snippet" \
  -H "Content-Type: application/json" \
  --data-binary "$(python3 build_payload.py)"   # payload below
# payload shape:
# { "title":"... Schema (JSON-LD)", "status":"publish",
#   "meta": { "_elementor_code": "<script type=\"application/ld+json\">{...}</script>",
#             "_elementor_location": "elementor_head", "_elementor_priority": 10 } }
# update later: POST .../elementor_snippet/<id> with just {"meta":{"_elementor_code":"..."}}
```

Build `_elementor_code` and the payload with `json.dumps` in Python (don't hand-escape). Send with `curl --data-binary` (Golden Rule 1).

Gotchas:
- `_elementor_conditions` (the "display everywhere" condition) often **won't persist** via REST, yet the snippet still renders site-wide from `elementor_head`. Verify on the live page; only fall back to the Elementor UI if it truly doesn't show.
- **`elementor_head` does NOT fire on some CPT single templates** (self-contained / canvas single templates). The global node will be missing there. Don't try to patch those in Elementor — that's what (B) is for.
- Use absolute production URLs in the schema (the user's real domain) so `@id`/`url`/`logo`/service URLs are correct at launch even while on a temp domain.

`scripts/build_localbusiness.py` is a template that emits the `@graph` and the snippet payload from a small config dict.

## B) Per-page Service / Article / BlogPosting — WPCode PHP snippet

For per-page schema built from real post data, a PHP snippet on `wp_head` is the robust choice: it fires on every front-end template (sidestepping the Elementor-hook gap) and pulls live data. WPCode (menu label often "Code Snippets", post type `wpcode`) is not cleanly REST-writable, so create it in the **browser**.

`scripts/wpcode_schema_snippet.php` is a ready, generic template: it detects `is_singular(['service','post','project'])`, builds `Service` / `BlogPosting` / `Article` accordingly, pulls the Yoast meta description → excerpt → trimmed content, includes the featured image when present, and links `provider`/`author`/`publisher` to `<base>/#localbusiness`. Edit the `$base`, the post-type list, and the `areaServed` list for the site.

### Creating it in WPCode (browser steps)
1. `admin.php?page=wpcode-snippet-manager` → "Add Your Custom Code" / "create your own" → choose **PHP Snippet**.
2. Set a title. **Inject the code via the CodeMirror API**, not by typing (typing into CodeMirror auto-indents/auto-closes and corrupts code). Base64-encode the PHP to dodge escaping, then:
   ```js
   (function(){
     const code = atob("<<BASE64>>");                 // PHP without the <?php tag
     document.querySelector('.CodeMirror').CodeMirror.setValue(code);
     // set the title input via the native setter so React notices:
     const ti=document.querySelector('input[placeholder*="title" i]');
     const set=Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set;
     set.call(ti,"Site – Service / Article Schema (JSON-LD)");
     ti.dispatchEvent(new Event('input',{bubbles:true}));
     return 'set';
   })()
   ```
3. Insert Method = **Auto Insert**, Location = **Run Everywhere** (the snippet's own `is_singular` guard scopes output). Toggle **Active**. Click **Save Snippet**.
4. Verify on the real permalinks (pull `link` from the API — a wrong slug hits the 404 page and looks like "no schema").

## AggregateRating / Review

Only with **real, user-confirmed** numbers (e.g. a Google Business Profile screenshot). Add to the LocalBusiness node:
```json
"aggregateRating": {"@type":"AggregateRating","ratingValue":"5.0","reviewCount":"55","bestRating":"5","worstRating":"1"}
```
and optionally a real `review` (author + body). Two things to expect: (1) the auto-mode classifier may block publishing rating numbers it can't independently verify, and (2) it will block you from self-granting Bash permissions to get around that. Both are correct. Surface the exact JSON you intend to publish and let the **user** approve interactively, add the permission rule themselves, or run the `curl` in their own terminal. Tell them the count is a snapshot (no live sync) and that Google prefers aggregate ratings backed by on-page reviews.
