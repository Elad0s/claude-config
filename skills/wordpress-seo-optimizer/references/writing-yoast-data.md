# Writing Yoast SEO data (titles, descriptions, term SEO, settings)

Yoast stores its SEO title / meta description as **protected post meta** (`_yoast_wpseo_title`, `_yoast_wpseo_metadesc`) that is **not registered for the REST API**. A `POST /wp/v2/<type>/<id>` with `{"meta":{...}}` returns `200` but the value is silently dropped (the `meta` object comes back as `[]`). So all of the below go through the **browser** on a logged-in wp-admin (Claude-in-Chrome). Confirm which browser to use first.

## A) Posts / Pages / Custom Post Types → Yoast Bulk editor (admin-ajax)

This is the fast path and it covers **every** content type that has SEO fields, including CPTs.

### Reach the page and grab the nonce
The bulk editor lives at `admin.php?page=wpseo_tools&tool=bulk-editor`, but **navigating directly to that URL fails** ("The link you followed has expired") because it needs a nonce. Instead: navigate to `admin.php?page=wpseo_tools`, then **click the "Bulk editor" link**. Once loaded, the nonce is a global JS var:

```js
wpseo_bulk_editor_nonce   // e.g. "f24ac7e698" — read it in-page
```

### The AJAX contract (discovered by capturing a real save)
`POST /wp-admin/admin-ajax.php`, `application/x-www-form-urlencoded`, `credentials: same-origin`, params:

| param | value |
|---|---|
| `action` | `wpseo_save_metadesc` (description) **or** `wpseo_save_title` (SEO title) |
| `_ajax_nonce` | `wpseo_bulk_editor_nonce` |
| `wpseo_post_id` | the post/CPT id |
| `new_value` | the title or description text |
| `existing_value` | `""` |

> The single-row action is **`wpseo_save_metadesc`** — NOT `wpseo_save_description` (that returns `0`). Title is `wpseo_save_title`. "Save all" is `wpseo_save_all`. A response body of `"0"` = action name wrong; `"-1"` = nonce/permission problem; anything else = success.

### Apply in bulk from the page context (run via the browser's JS tool)
Because you're executing in the page, cookies + nonce are already there. Loop all items in one call:

```js
(async function(){
  const nonce = wpseo_bulk_editor_nonce;
  async function save(action,id,val){
    const b=new URLSearchParams({action,_ajax_nonce:nonce,wpseo_post_id:String(id),new_value:val,existing_value:""});
    const r=await fetch("/wp-admin/admin-ajax.php",{method:"POST",headers:{"Content-Type":"application/x-www-form-urlencoded"},body:b.toString(),credentials:"same-origin"});
    const t=await r.text(); return r.status===200 && t!=="0" && t!=="-1";
  }
  const items=[ /* [id,title,desc], ... */ ];
  const res={titleOk:0,descOk:0,fail:[]};
  for(const [id,ti,de] of items){
    (await save("wpseo_save_title",id,ti)) ? res.titleOk++ : res.fail.push("T"+id);
    (await save("wpseo_save_metadesc",id,de)) ? res.descOk++ : res.fail.push("D"+id);
  }
  return JSON.stringify(res);
})()
```

Setting a literal SEO title **overrides** Yoast's `%%title%% %%sep%% %%sitename%%` template for that page (it won't double-append the site name), so include the brand in your string yourself.

The harness may **block** echoing the response body if it looks like query-string/secret data ("BLOCKED: Cookie/query string data"). Don't fight it — return only compact summaries (counts, parsed keys), never raw bodies or nonces.

## B) Taxonomy term SEO (category / county / location-term archives)

Term SEO is **also not REST-writable**. Edit each term on its admin edit screen:

`/wp-admin/term.php?taxonomy=<tax>&tag_ID=<term_id>&post_type=<cpt>`

The Yoast metabox is a React UI, but it syncs into plain **hidden inputs** that the term form actually submits. Set those and submit the form (one navigation per term; wait ~3s for load):

```js
(function(){
  const t=document.getElementById('hidden_wpseo_title');
  const d=document.getElementById('hidden_wpseo_desc');   // note: _desc, not _metadesc, for terms
  if(!t||!d) return 'MISSING';
  t.value="<<TITLE>>"; d.value="<<DESCRIPTION>>";
  document.getElementById('edittag').submit();
  return 'submitted';
})()
```

Other hidden fields exist if needed: `hidden_wpseo_noindex`, `hidden_wpseo_canonical`, `hidden_wpseo_focuskw`, etc. Find the term ids via `GET /wp/v2/<taxonomy_rest_base>?per_page=100&_fields=id,name,slug,link,yoast_head_json`. Verify each afterward via that same endpoint.

## C) CPT-archive title/desc + index toggles → Yoast Settings SPA

These are **global options** (`wpseo_titles`: `title-ptarchive-<cpt>`, `metadesc-ptarchive-<cpt>`, `noindex-ptarchive-<cpt>`, `noindex-tax-<taxonomy>`), set in the Yoast Settings React app at `admin.php?page=wpseo_page_settings`:

- **Content types → <CPT>**: a "Show … in search results" toggle (the per-type index) plus the single-item SEO title/description templates. The page uses Yoast's replacement-variable editors (the "Insert variable" fields).
- **Categories & tags → <taxonomy>**: the same toggle + title/desc template for term archives.

Caveats learned the hard way:
- Hash deep-links (`#/post-type/<cpt>`) don't reliably stick; **click through the left sidebar** instead.
- Fields render per-route (it's a SPA) and are Formik-controlled, so naive `.value=` won't register — drive the **visible UI** (click field, type, toggle, Save) rather than scripting hidden inputs here.
- This modern UI may **not expose a separate CPT-archive title/desc section** at all. Flat CPT archives (`/services/`, `/service-areas/`) are low-value list pages; leaving them `noindex` is a defensible choice — the value lives in the individual item pages and the taxonomy-term archives (handled in A/B). Say so rather than burning time forcing it.
