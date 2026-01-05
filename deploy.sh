#!/usr/bin/env bash
set -e

cd ~/nba_stats/backend

git fetch
git checkout host
git pull

source venv/bin/activate
pip install -r requirements.txt

python -m py_compile application.py

sudo systemctl restart gunicorn
sudo nginx -t
sudo systemctl reload nginx

echo "Deploy complete"
