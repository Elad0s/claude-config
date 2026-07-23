---
name: hostinger-new-project-server
description: SSH access to the main Hostinger shared-hosting account (u694051539) and the domains it hosts
metadata:
  node_type: memory
  type: project
  originSessionId: 20637168-73b9-4dc7-a9fe-e7a6e18374d4
  modified: 2026-07-22T22:10:20.062Z
---

Main Hostinger shared-hosting account. `ssh -p 65002 u694051539@147.93.74.187`

- **Key auth works** as of 2026-07-23 — key at `~/.ssh/id_ed25519`, installed via hPanel → Advanced → SSH Access → SSH Keys (password auth kept failing; Claude cannot type passwords anyway).
- Host: `lt-bnk-web1164.main-hosting.eu`. PHP 8.2.30 CLI, WP-CLI 2.12.0 at `/usr/local/bin/wp`.
- `~/public_html` symlinks to `domains/silviabumper.co.il/public_html` — always work under explicit `~/domains/<site>/` paths, not `public_html`.
- Domains on this account: 3pines.studio, avshalom-oren.co.il, bleaumed.com, eladoren.com, eranelster.com, pelaozen.com, pinepx.com, rosenberglaw.co.il, sharir-kayam.co.il, silviabumper.co.il, tutiaviran.co.il, plus three `*.hostingersite.com` staging domains.

Related: [[3pines-studio-site]]
