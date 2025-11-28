#!/usr/bin/env bash
set -euo pipefail

SRC=/home/admin/campus-lost-found/frontend/dist/
DST=/var/www/lost-found-frontend/dist/

sudo mkdir -p "$DST"
sudo rsync -a --delete "$SRC" "$DST"

sudo nginx -t
sudo systemctl restart nginx
echo "Synced frontend dist to $DST and reloaded nginx."
