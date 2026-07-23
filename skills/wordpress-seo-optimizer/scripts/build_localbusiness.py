#!/usr/bin/env python3
"""
Build a LocalBusiness JSON-LD @graph and the Elementor Custom Code snippet
payload to inject it site-wide. See references/schema-injection.md (A).

Fill in CONFIG, then either:
  python3 build_localbusiness.py           # prints the snippet payload JSON
  python3 build_localbusiness.py --graph   # prints just the @graph (to eyeball)

Then create/update the snippet (use curl — Golden Rule 1):
  curl -s -u "$AUTH" -X POST "$SITE/wp-json/wp/v2/elementor_snippet" \
    -H "Content-Type: application/json" \
    --data-binary "$(python3 build_localbusiness.py)"
  # update later: POST .../elementor_snippet/<id> with {"meta":{"_elementor_code": <code>}}

Use ABSOLUTE PRODUCTION URLs (the real domain) so @id/url/logo are correct at launch.
aggregateRating/review: include ONLY with real, user-confirmed numbers.
"""
import json, sys

CONFIG = {
    "base": "https://example.com",                 # production domain, no trailing slash
    "name": "Example Business",
    "telephone": "+1-555-555-5555",
    "email": "info@example.com",
    "logo": "https://example.com/wp-content/uploads/logo.webp",
    "description": "What the business does, where it serves.",
    "counties": ["Middlesex County", "Essex County"],         # AdministrativeArea, ", STATE" appended
    "cities":   ["Burlington", "Lexington"],                  # City, ", STATE" appended
    "state": "MA",
    "services": [   # (name, path-relative-to-base)
        ("Chimney Repointing", "services/chimney-repointing/"),
    ],
    # Optional — only with real data:
    # "aggregateRating": {"ratingValue": "5.0", "reviewCount": "55"},
    # "reviews": [{"author": "Jane D.", "rating": "5", "body": "Great service."}],
}


def build_graph(c):
    base = c["base"].rstrip("/")
    site = base + "/"
    biz = {
        "@type": ["LocalBusiness", "HomeAndConstructionBusiness"],
        "@id": site + "#localbusiness",
        "name": c["name"], "url": site,
        "telephone": c["telephone"], "email": c["email"],
        "image": c["logo"], "logo": c["logo"],
        "description": c["description"],
        "areaServed": (
            [{"@type": "AdministrativeArea", "name": f"{x}, {c['state']}"} for x in c["counties"]]
            + [{"@type": "City", "name": f"{x}, {c['state']}"} for x in c["cities"]]
        ),
        "hasOfferCatalog": {
            "@type": "OfferCatalog", "name": "Services",
            "itemListElement": [
                {"@type": "Offer", "itemOffered": {
                    "@type": "Service", "name": n,
                    "url": base + "/" + p, "provider": {"@id": site + "#localbusiness"}}}
                for n, p in c["services"]
            ],
        },
    }
    if c.get("aggregateRating"):
        ar = c["aggregateRating"]
        biz["aggregateRating"] = {"@type": "AggregateRating", "bestRating": "5",
                                  "worstRating": "1", **ar}
    if c.get("reviews"):
        biz["review"] = [{"@type": "Review",
                          "reviewRating": {"@type": "Rating", "ratingValue": r["rating"], "bestRating": "5"},
                          "author": {"@type": "Person", "name": r["author"]},
                          "reviewBody": r["body"]} for r in c["reviews"]]
    return {"@context": "https://schema.org", "@graph": [biz]}


if __name__ == "__main__":
    graph = build_graph(CONFIG)
    if "--graph" in sys.argv:
        print(json.dumps(graph, ensure_ascii=False, indent=1)); sys.exit(0)
    code = ('<script type="application/ld+json">\n'
            + json.dumps(graph, ensure_ascii=False, indent=1) + "\n</script>")
    payload = {"title": f"{CONFIG['name']} – LocalBusiness Schema (JSON-LD)",
               "status": "publish",
               "meta": {"_elementor_code": code,
                        "_elementor_location": "elementor_head",
                        "_elementor_priority": 10}}
    print(json.dumps(payload, ensure_ascii=False))
