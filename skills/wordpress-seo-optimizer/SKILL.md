---
name: wordpress-seo-optimizer
description: >-
  Optimize SEO and structured data on a WordPress site that runs Yoast SEO +
  Elementor Pro + WPCode (and often ACF / custom post types, e.g. GoDaddy or
  Hostinger managed hosting). Use this whenever the user wants to edit meta
  titles or meta descriptions, add or fix image alt text, add JSON-LD / schema
  (LocalBusiness, Service, Article, BlogPosting, FAQ, AggregateRating), improve
  SEO copy for service pages or location/service-area pages, set titles for
  archive or taxonomy-term pages, fill empty ACF image fields, source or
  AI-generate location/service-area images, clean up media titles/captions, or
  otherwise improve a WordPress site's
  search appearance — even if they just say "improve my WordPress SEO",
  "connect to my WP site", "rewrite my meta descriptions", "add schema", or
  paste a wp-json / wp-admin URL. It encodes hard-won workarounds (Yoast meta is
  not REST-writable, a WAF that blocks Python's User-Agent, Elementor's head
  hook not firing on some templates) so future runs don't rediscover them.
---

# WordPress SEO Optimizer

A field guide for editing SEO data and structured data on a **WordPress + Yoast SEO + Elementor Pro + WPCode** stack (commonly with ACF and custom post types, on managed hosts like GoDaddy/Hostinger). It exists because several "obvious" approaches silently fail on this stack — the techniques below are the ones that actually work.

You drive the site two ways, and you'll mix them:
- **REST API** (via `curl`) — fast, scriptable, great for reads, media alt text, and Elementor Custom Code snippets.
- **Browser automation** (Claude-in-Chrome on a logged-in wp-admin) — required for anything Yoast stores that the REST API won't write (meta titles/descriptions, taxonomy-term SEO, Yoast settings) and for WPCode.

## Golden rules (read first — these are the ones that bite)

1. **Writes via Python's `urllib`/`requests` may 403.** Many managed hosts run a WAF that blocks non-browser User-Agents on POST/PUT. Reads (GET) usually pass; **writes fail silently with 403**. Fix: shell out to **`curl`** for every write (a Python script can call `subprocess.run(["curl", ...])`). If a write 403s, this is almost always why.
2. **Yoast meta titles/descriptions are NOT writable through the REST `meta` field.** They're protected and not registered for REST — a POST returns `200` but the value never persists. Use the **Yoast Bulk editor admin-ajax** technique (browser) instead. See `references/writing-yoast-data.md`.
3. **Always verify after writing.** Re-fetch `?_fields=yoast_head_json` (or the live page HTML) and confirm the value actually changed. A `200` is not proof on this stack.
4. **Never fabricate ratings/reviews.** `AggregateRating`/`Review` schema may only use real, user-confirmed numbers (e.g. a screenshot of the Google Business Profile). The harness will (correctly) block publishing rating data it can't verify.
5. **You cannot self-grant permissions.** If a write is blocked by the permission/auto-mode classifier, do NOT try to widen your own Bash rules — that's blocked too. Explain it and let the **user** add the rule, run the command themselves, or approve interactively.
6. **Side-effectful, outward-facing changes need confirmation.** Meta tags and schema are public content. Propose the copy, get a quick "go", then apply.
7. **ACF writes need every required field.** ACF isn't in REST until you enable "Show in REST API" on the field group; once on, a write validates ALL required fields ("X is a required property of acf"). Always read-modify-write the whole `acf` object; image fields take an attachment **ID**. See `references/acf-and-media.md`.
8. **Decorative icons want EMPTY alt — don't "fix" them.** Adding descriptions to decorative/feature icons hurts screen-reader UX, and Elementor inlines SVGs so the field is unused anyway. Only meaningful badges/logos and text-less link-icons get alt. See `references/acf-and-media.md`.
9. **`javascript_tool` output may be blocked** ("Cookie/query string data") when it contains URLs/nonces/query strings. Return compact summaries (counts, parsed keys, booleans) — never raw response bodies, full URLs, or nonces.

## Step 1 — Connect and verify

Ask the user for: **site URL**, **username**, and a Yoast/WP **Application Password** (wp-admin → Users → Profile → Application Passwords; needs WP 5.6+ and HTTPS). Then confirm identity and capabilities:

```bash
AUTH="user:xxxx xxxx xxxx xxxx xxxx xxxx"   # application password (with spaces)
SITE="https://example.com"
curl -s -u "$AUTH" "$SITE/wp-json/wp/v2/users/me?context=edit&_fields=id,name,roles,capabilities" | python3 -m json.tool
```

Then map the site before touching anything — this stack hides content in custom post types and taxonomies:

```bash
curl -s -u "$AUTH" "$SITE/wp-json/wp/v2/types" | python3 -c "import sys,json;[print(k,'->',v.get('rest_base')) for k,v in json.load(sys.stdin).items()]"
# inspect each CPT/taxonomy you find (e.g. service, service_area, project, area_county):
curl -s -u "$AUTH" "$SITE/wp-json/wp/v2/<rest_base>?per_page=100&_fields=id,title,link,yoast_head_json"
```

Note the **active plugins** from `yoast_head_json` / page HTML (Yoast version, Elementor, WPCode, ACF) — they determine which techniques below apply.

## Step 2 — Pick the technique (decision table)

| You want to change… | Technique | Where |
|---|---|---|
| Image **alt text** | REST `POST /wp/v2/media/<id>` `{"alt_text":...}` (via curl) | this file, below |
| **Meta description / SEO title** of posts, pages, **any CPT** | Yoast **Bulk editor admin-ajax** (browser) | `references/writing-yoast-data.md` |
| **Taxonomy term** SEO (category / county / location term archives) | `term.php` hidden-field submit (browser) | `references/writing-yoast-data.md` |
| **CPT archive** title/desc + **index** toggles, taxonomy index | Yoast **Settings SPA** (browser) | `references/writing-yoast-data.md` |
| Global **LocalBusiness** JSON-LD (site-wide) | **Elementor Custom Code** snippet via REST | `references/schema-injection.md` |
| Per-page **Service / Article / BlogPosting** JSON-LD | **WPCode PHP** snippet (browser) | `references/schema-injection.md` |
| **ACF fields / image fields** on a CPT (read or write) | enable ACF REST, then read-modify-write whole `acf` | `references/acf-and-media.md` |
| Media **title / caption / description** (clean junk slugs) | REST `POST /wp/v2/media/<id>` (via curl) | `references/acf-and-media.md` |
| **Icon** alt text (decorative vs functional) | mostly leave empty — don't add descriptions | `references/acf-and-media.md` |
| **Source or AI-generate** images (fill empty slots) | reuse own media → Wikimedia → AI prompts; webp via Pillow | `references/acf-and-media.md` |
| Writing the actual **titles & descriptions** (copy) | formulas + brand voice | `references/seo-copywriting.md` |

## Image alt text (REST, works directly)

Alt text lives on the media attachment and is REST-writable. List what's missing, then update:

```bash
# list images + alt status
curl -s -u "$AUTH" "$SITE/wp-json/wp/v2/media?per_page=100&media_type=image&_fields=id,alt_text,source_url"
# update one (use curl, not urllib — see Golden Rule 1)
curl -s -u "$AUTH" -X POST "$SITE/wp-json/wp/v2/media/<ID>" \
  -H "Content-Type: application/json" -d '{"alt_text":"Descriptive, keyword-aware alt"}'
```

Derive alt text from the filename + page context — but for empty/ambiguously-named files and before/after pairs, **download and Read the image** (you can view `.webp`/JPG/PNG directly) rather than guessing. **Caveat:** Elementor bakes alt into its page data at insertion time, so images already placed on a page may keep showing empty `alt` until that page is re-saved in Elementor — flag this to the user. Leave genuinely decorative images (icons, spacers, shapes) with empty alt on purpose — see the Icons section of `references/acf-and-media.md` before touching icons, and that file also covers the other media fields (title/caption/description) and how to source or AI-generate images for empty slots.

`scripts/rest_update.py` is a small curl-wrapping helper for batching media (and other simple REST) writes.

## Step 3 — Always verify

After any write, confirm it landed:

```bash
curl -s -u "$AUTH" "$SITE/wp-json/wp/v2/<type>/<id>?_fields=yoast_head_json&nc=$RANDOM" \
 | python3 -c "import sys,json;y=json.load(sys.stdin).get('yoast_head_json',{});print('T:',y.get('title'));print('D:',y.get('description'))"
```

For schema, fetch the live page and parse `<script type="application/ld+json">` blocks — Yoast's block carries a `class` attribute, so match `<script[^>]*application/ld\+json[^>]*>`, not a bare tag. Bust caches with a `?nc=<random>` query param (managed hosts cache hard). **Watch for wrong URLs** — guessing a slug returns the 404 page (identical byte size across "different" URLs is the tell); always pull the real `link` field from the API first.

## Indexing reality check

On a staging/temp domain the whole site is usually **`noindex` site-wide** (Settings → Reading → "Discourage search engines", i.e. `blog_public=false`). That overrides per-page Yoast settings, so everything reads `noindex` even when individual Yoast "Show in search results" toggles are ON. Don't mistake this for a per-page problem — note it as a **launch-day** task (flip it when the real domain goes live), and remember the temp domain's absolute URLs (schema `@id`, canonicals, images) will need a DB search-replace at launch.

## Notes carried from the field

- The **Elementor `elementor_head` hook does not fire on some CPT single templates** (self-contained / canvas templates). A site-wide Elementor Custom Code snippet will be missing there even though it renders everywhere else — that's exactly why per-page schema goes through a WPCode `wp_head` PHP snippet instead. See `references/schema-injection.md`.
- Yoast already emits `WebSite`, `Organization`, `WebPage`, `BreadcrumbList`, and (via Elementor/widgets) sometimes `FAQPage`. Check what's present before adding, to avoid duplicate nodes. Blog-post `Article` schema is often missing on Elementor-templated singles — that's the gap the WPCode snippet fills.
- Keep one authoritative business entity: reference it everywhere via a stable `@id` like `<site>/#localbusiness` so `provider`/`publisher`/`author` link back to it.

Read the relevant `references/*.md` file in full before executing that technique — they contain the exact AJAX action names, field IDs, and a ready PHP template that are easy to get subtly wrong.
