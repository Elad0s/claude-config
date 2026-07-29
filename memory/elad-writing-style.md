---
name: elad-writing-style
description: "Elad's preferences for Hebrew copy I write for him — punctuation, tone, and what to avoid"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: ce39da92-f498-4ea1-8986-2802c0ca4def
  modified: 2026-07-23T08:47:56.709Z
---

**Use plain short hyphens (`-`) only.** Never en dashes (`–`) or em dashes (`—`) in Hebrew copy — titles, meta descriptions, body text, anywhere.

**Why:** stated 2026-07-23 — he finds the short hyphen simply looks better in Hebrew. It is a standing preference, not a one-off.

**How to apply:** write `-` from the start rather than producing `–` and correcting it later. **In WordPress body content this is not enough** — `wptexturize()` silently rewrites a bare `" - "` into `" – "` on render, so a literal hyphen typed into Elementor never reaches the page. Write it as the numeric entity `&#45;` instead: texturize has no bare hyphen pattern to match, and the browser renders a plain short hyphen. Yoast title/meta fields are not texturized, so a literal `-` is fine there. Applies to everything authored for him, not just [[3pines-studio-site]]. He did not ask for a retroactive sweep of existing site content — only fix dashes in copy I wrote myself.

**Tone he picked when given options:** concrete and slightly blunt over polished marketing language. Given three hero paragraphs he chose *"בונים לעסקים אתרים שנראים מדויק, נטענים מהר ומביאים פניות - לא רק מחמאות."* over safer phrasings — he wants a point of view and a real outcome, not "אתרים מנצחים"-style filler.
