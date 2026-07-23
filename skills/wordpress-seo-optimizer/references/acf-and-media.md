# ACF fields, media fields, icons & sourcing images

Covers everything around images and ACF content on this stack: writing ACF fields (incl. images), the other media-library fields, the accessibility-correct way to treat icons, and how to source or generate the images themselves.

## ACF fields (custom content + image fields)

Custom post types on this stack (e.g. `service`, `service_area`, `project`) keep most of their content in **ACF fields**, not the post body. Two gotchas:

### 1. ACF is not in REST until you switch it on
By default `GET /wp/v2/<cpt>/<id>` returns `"acf": []` — the fields aren't exposed. Enable it once per field group (browser):

- wp-admin → **ACF → Field Groups** → open the group (note its key, e.g. `group_topdog_service_area`).
- It's the **ACF 6 editor** (a full-screen app). The save button is **"Save Changes"** (top-right) — *not* the classic `#publish`. After editing, expect a "Leave site? unsaved changes" guard if it didn't save; re-click and confirm you see "Field group updated."
- The **Show in REST API** toggle is a true/false switch backed by a hidden input `name="...[show_in_rest]"`. You can set it via JS (`hidden.value='1'` + check the sibling checkbox + dispatch `change`) then click **Save Changes**, or just toggle it in the UI under the group's settings.
- Verify: `GET /wp/v2/<cpt>/<id>?_fields=acf` now returns an object.

This exposes ACF for **read and write** via REST — far faster than editing each post in the browser.

### 2. Writing ACF requires ALL required fields in the payload
`POST /wp/v2/<cpt>/<id>` with `{"acf": {...}}` validates **every required field**. A partial update fails:
`rest_invalid_param … "area_h1 is a required property of acf."`

So the safe write pattern is **read-modify-write the whole acf object**:
1. `GET …?_fields=acf` → the current values.
2. Normalize: image/file fields read back as an **object** (`{ID, url, …}`) → resend just the **`ID`** (an integer). Text/textarea/wysiwyg read back as strings → resend as-is. Skip empty arrays / complex repeaters you're not changing.
3. Overwrite the field(s) you want (image fields take an **attachment ID**).
4. `POST` the full object back (via curl — Golden Rule 1).

`scripts/acf_set.py` implements exactly this (`get_acf` + `set_images`). Note: if an image field is itself *required* and currently empty, you must supply it on the same write (you can't set only one of two required images).

ACF image fields render in the post editor as an `.acf-image-uploader` that **always contains an `<img>` element even when empty** — so "is there an `<img>`?" is a false-positive test for "has an image." Trust the REST value, not the DOM.

## The other media-library fields (title / caption / description / filename)

For any attachment, `title`, `caption`, and `description` **are** REST-writable (unlike Yoast meta): `POST /wp/v2/media/<id> {"title": "...", "caption": "...", "description": "..."}`.

Importance, highest first:
- **Alt text** — accessibility (screen readers, ADA) + image SEO. The one that matters. Empty for decorative images (see Icons).
- **Filename** — a real image-SEO signal; keep descriptive, lowercase, hyphenated. Can't change post-upload without re-upload + redirects.
- **Caption** — visible *under the image* **if** the layout renders it. WordPress/bulk-imports often auto-fill caption with the **filename slug** (junk like `topdog-chimney-Our-Story`). Clear it (`"caption": ""`) or write a real caption; never leave the slug.
- **Title** — mostly an admin label + a hover `title` tooltip on some themes; near-zero SEO weight. Worth tidying to human-readable, low priority.
- **Description** — only shown on the **attachment page**. If those are disabled (a `301` on `?attachment_id=<id>` means yes — common via Yoast/WPCode), the field is never public → ignore it.

> Caveat: a `POST` response may echo a **stale** `caption.rendered`. Verify with a fresh `GET …?context=edit&_fields=caption` and check `caption.raw`.

## Icons & decorative images — the accessibility-correct call

Counterintuitive but important: **most icons should have EMPTY alt, and adding descriptions is wrong.**

- **Decorative icons** (feature/benefit/trust/contact icons, dividers, shapes): alt must be **empty** so screen readers skip them. Also, Elementor usually renders chosen SVG icons as **inline `<svg>`**, so the media `alt_text` field isn't even used for them — accessibility comes from `aria-hidden` + the adjacent text. Don't "fix" these.
- **Meaningful images/badges** (certification badges, a Google-rating badge, the company logo): these convey information → **descriptive alt** is warranted.
- **Functional icon-links** (a social icon that's a link with no text): need an accessible name (`aria-label` / non-empty alt). Elementor's Social-Icons widget adds this itself. But first check the link actually has no visible text — an icon-in-link next to a phone number / "Free Quote" text is fine with empty alt (the text is the link's name; empty alt is correct, and a non-empty one would be redundant).

How to audit: list media by mime/size (`GET /media?_fields=id,mime_type,media_details,source_url`) to spot SVGs and tiny icons. To judge decorative-vs-functional, fetch the live page and check whether the icon renders as `<img>` inside an `<a>` and whether that link has visible text.

## Viewing images to write accurate alt

You can **Read `.webp`/JPG/PNG directly** — so don't guess from filenames. Download (`curl <source_url> -o /tmp/x.webp`) and Read to see the real content; this is the only way to (a) describe empty/ambiguously-named files and (b) confirm a "before/after" pair actually matches its filename. Verify by re-checking `alt_text` via the API after writing.

Brand-name policy in alt: include the brand naturally in work/team/result photos; **keep it out of "before"/damage shots** (crediting a brand for damage is misleading and hurts the description). Don't stuff the brand into every decorative file.

## Sourcing or generating the images themselves

When ACF/featured-image slots are empty, options in order of authenticity:

1. **Reuse the site's own existing media** — already optimized, on-brand, zero licensing. Best for "why choose us"/team slots (use real team/work photos) and any town that already has a real photo. Always check the library first.
2. **Real location photos from Wikimedia Commons** — for "about {town}" slots. Use the MediaWiki API (no key):
   - search files: `commons.wikimedia.org/w/api.php?action=query&list=search&srsearch=<term>&srnamespace=6&format=json`
   - license + author: `…&action=query&titles=File:<name>&prop=imageinfo&iiprop=url|size|extmetadata` → `extmetadata.LicenseShortName`, `.Artist`, `.UsageTerms`.
   - **Commercial-OK** = CC0 / Public Domain / CC BY / CC BY-SA. Exclude NC / ND / "all rights". **Prefer PD/CC0** (no attribution = zero risk); CC-BY/SA need a visible credit to be compliant.
   - Reality check: good *modern* town photos are usually **CC-BY-SA**; the **PD** ones are often archival (old maps, engravings, postcards) — pretty but useless as a clean reference. Send `User-Agent` on requests.
3. **AI-generated images** (e.g. ChatGPT/GPT-4o) — best for a cohesive, unique, license-free set of *evocative* (not literal) scenes. Pattern that works:
   - A fixed **style block** (medium, lighting, season, framing, "no text/logos/faces/distortion", aspect ratio) prepended to every prompt, then a per-item **scene** line capturing the real local character (the model knows most towns).
   - **Style consistency:** have the user upload one of *their own* photos as a style reference (zero risk — they own it).
   - **Local reference:** a real town photo can guide character. If feeding a Wikimedia image as an AI input, prefer **PD/CC0** — using CC-BY-SA as a generation input is a ShareAlike/derivative gray area. The *output* is original, so licensing risk lives in the *input*.
   - **Domain realism:** for a trade audience, emphasize the trade detail must look correct (e.g. "a structurally correct, realistic brick chimney — clean mortar, proper coursing") and **review every image for artifacts** before publishing.
   - `scripts/build_prompts.py` builds a paste-ready prompt doc (style block + per-item scene + a fetched reference URL with its license) — adapt the town/scene list.

## webp conversion & upload

No `cwebp`/`sips`-webp on macOS by default. Install **Pillow** (`python3 -m pip install --user pillow`) — its wheel bundles libwebp, so `Image.open(...).save(out, "WEBP", quality=80)` works; resize to ~1200px wide first to keep files < ~150 KB. Upload via REST with curl:

```bash
curl -s -u "$AUTH" -X POST "$SITE/wp-json/wp/v2/media" \
  -H "Content-Disposition: attachment; filename=town-name.webp" \
  -H "Content-Type: image/webp" --data-binary @town-name.webp
```

Then set `alt_text` (and a real `caption` if it'll show), and assign the returned attachment **ID** into the ACF image field (read-modify-write pattern above).
