#!/usr/bin/env bash
#
# Point ~/.claude at the files in this repo. Safe to re-run: anything already
# in place is backed up first, and existing correct symlinks are left alone.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE="$HOME/.claude"
BACKUP="$HOME/.claude-backup-$(date +%Y%m%d-%H%M%S)"

# The memory directory is namespaced by a slug derived from the working
# directory Claude Code runs in — which contains the macOS username.
PROJECT_SLUG="-Users-$(id -un)"
MEMORY_DEST="$CLAUDE/projects/$PROJECT_SLUG/memory"

link() {
	local src="$1" dest="$2"

	if [ -L "$dest" ] && [ "$(readlink "$dest")" = "$src" ]; then
		echo "  ok       $dest"
		return
	fi

	if [ -e "$dest" ] || [ -L "$dest" ]; then
		mkdir -p "$BACKUP/$(dirname "${dest#"$CLAUDE"/}")"
		mv "$dest" "$BACKUP/${dest#"$CLAUDE"/}"
		echo "  backed up $dest"
	fi

	mkdir -p "$(dirname "$dest")"
	ln -s "$src" "$dest"
	echo "  linked   $dest"
}

echo "Linking Claude Code config from $REPO"
echo

link "$REPO/memory" "$MEMORY_DEST"
link "$REPO/settings.local.json" "$CLAUDE/settings.local.json"

for skill in "$REPO"/skills/*/; do
	[ -d "$skill" ] || continue
	link "${skill%/}" "$CLAUDE/skills/$(basename "$skill")"
done

echo
echo "Memory directory: $MEMORY_DEST"
if [ "$PROJECT_SLUG" != "-Users-eladoren" ]; then
	cat <<-WARN

	NOTE: this machine's username is "$(id -un)", not "eladoren", so memory was
	linked into $PROJECT_SLUG. That is the right place for THIS machine, but the
	two machines now use different project slugs — which is fine, since both
	slugs point at the same shared memory/ directory in this repo.
	WARN
fi

[ -d "$BACKUP" ] && echo "Replaced files saved in: $BACKUP"

echo
echo "Done. Remember: generate a machine-local SSH key and re-authorise MCP connectors."
