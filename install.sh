#!/usr/bin/env bash
# Install the Claude Code skill, the kompas-nested launcher and its menu entry for the current user.
# Usage: ./install.sh [--link]    --link symlinks the skill and launcher instead of copying them
#                                 (handy if you edit this repo). Existing files are moved to
#                                 ~/.claude/backups/kompas-3d-install-<timestamp>/.
# Env:   CLAUDE_CONFIG_DIR (default ~/.claude), BIN_DIR (default ~/.local/bin),
#        XDG_DATA_HOME (default ~/.local/share) for the menu entry.
set -euo pipefail
cd "$(dirname "$0")"

mode='copy'
[[ ${1:-} == --link ]] && mode='link'

claude_dir=${CLAUDE_CONFIG_DIR:-$HOME/.claude}
skills=$claude_dir/skills
bin=${BIN_DIR:-$HOME/.local/bin}
apps=${XDG_DATA_HOME:-$HOME/.local/share}/applications
# Backups go outside skills/: a copy left there would load as a second kompas-3d skill.
backup=$claude_dir/backups/kompas-3d-install-$(date +%Y%m%d%H%M%S)
mkdir -p "$skills" "$bin" "$apps"

# place SRC DST: copy or symlink SRC to DST, moving anything already at DST to $backup first
place() {
  local src=$1 dst=$2
  if [[ -e $dst || -L $dst ]]; then
    mkdir -p "$backup"
    mv "$dst" "$backup/"
    echo "backed up $dst -> $backup/"
  fi
  if [[ $mode == link ]]; then ln -s "$PWD/$src" "$dst"; else cp -r "$src" "$dst"; fi
  echo "installed $dst"
}

place skill/kompas-3d "$skills/kompas-3d"
place launcher/kompas-nested "$bin/kompas-nested"
# menu entries don't search ~/.local/bin on every desktop, so use the absolute path
sed "s|^Exec=.*|Exec=$bin/kompas-nested|" launcher/kompas-nested.desktop > "$apps/kompas-nested.desktop"
echo "installed $apps/kompas-nested.desktop"

cat <<EOF

Done. Next:
  1. Start KOMPAS with: kompas-nested
  2. Smoke-test the helpers: $skills/kompas-3d/scripts/run.sh $PWD/examples/selftest.py
  3. On sway, see launcher/sway.conf.
EOF
