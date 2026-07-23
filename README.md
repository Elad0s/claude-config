# claude-config

Shared Claude Code configuration for Elad's machines: accumulated project memory,
the custom WordPress SEO skill, and the permission allowlist.

The real files live here. `~/.claude` holds symlinks pointing at them, so editing
through Claude Code writes straight into this repo.

## What's in here

| Path | Symlinked to |
|---|---|
| `memory/` | `~/.claude/projects/-Users-eladoren/memory` |
| `skills/wordpress-seo-optimizer/` | `~/.claude/skills/wordpress-seo-optimizer` |
| `skills/wordpress-seo-optimizer-workspace/` | `~/.claude/skills/wordpress-seo-optimizer-workspace` |
| `settings.local.json` | `~/.claude/settings.local.json` |

## Setting up a second machine

```bash
git clone <this-repo-url> ~/claude-config
cd ~/claude-config && ./install.sh
```

`install.sh` backs up whatever is already there, then lays down the symlinks.

## Daily use

`git pull` before a work session, `git push` after. If both machines edited the
same memory file you get a normal merge conflict — resolve it like any other file.

## Two things that do NOT sync, by design

**SSH keys.** Never copy a private key between machines. Generate a fresh one on
each and register the public half:

```bash
ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519 -N ''
```

Then add `~/.ssh/id_ed25519.pub` in Hostinger hPanel → Advanced → SSH Access →
SSH Keys. (Password auth on that account does not work.)

**MCP connectors** (Search Console, Analytics, and the rest) are authorised per
machine through claude.ai connector settings. Authorise them again on the new
machine.

## The path gotcha

`memory/` is symlinked into `~/.claude/projects/-Users-eladoren/` — a slug derived
from the working directory, which encodes the macOS username `eladoren`. If the
second machine uses a different username the slug differs and the memory will not
load. `install.sh` detects this and tells you the directory it actually used.
