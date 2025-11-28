#!/usr/bin/env bash
set -euo pipefail

APP_DIR=/opt/lost-found-system
cd "$APP_DIR"

python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r backend/requirements.txt

sed -i 's/debug=True/debug=False/g' backend/app.py || true

venv/bin/python backend/app.py
