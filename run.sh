#!/bin/bash
# run.sh <GH_TOKEN> [REPO_NAME]
# buat repo private, push workflow, trigger, tunggu, cetak baris ssh tmate
set -eu
T=${1:?usage: run.sh <gh-token> [repo]}
REPO=${2:-freemilk-harvest}
USER=$(curl -fsS -H "Authorization: Bearer $T" https://api.github.com/user | python3 -c 'import sys,json;print(json.load(sys.stdin)["login"])')
echo "user=$USER repo=$REPO"
curl -fsS -X POST -H "Authorization: Bearer $T" -H 'Accept: application/vnd.github+json' \
  https://api.github.com/user/repos \
  -d "{\"name\":\"$REPO\",\"private\":true,\"auto_init\":false}" >/dev/null 2>&1 || echo "repo sudah ada"
cd "$(dirname "$0")"
rm -rf .git
git init -q -b main
git add -A
git -c user.name="$USER" -c user.email="$USER@users.noreply.github.com" commit -qm "harvest"
git remote add origin "https://x-access-token:$T@github.com/$USER/$REPO.git"
git push -q -u origin main
curl -fsS -X POST -H "Authorization: Bearer $T" -H 'Accept: application/vnd.github+json' \
  "https://api.github.com/repos/$USER/$REPO/actions/workflows/mac-harvest.yml/dispatches" \
  -d '{"ref":"main"}' && echo dispatched
for i in $(seq 1 40); do
  sleep 15
  RUN=$(curl -fsS -H "Authorization: Bearer $T" "https://api.github.com/repos/$USER/$REPO/actions/runs?per_page=1" \
    | python3 -c 'import sys,json;r=json.load(sys.stdin)["workflow_runs"];print(r[0]["id"] if r else "")')
  [ -z "$RUN" ] && continue
  LOG=$(curl -fsSL -H "Authorization: Bearer $T" "https://api.github.com/repos/$USER/$REPO/actions/runs/$RUN/logs" -o /tmp/run.log 2>/dev/null; unzip -p /tmp/run.log 2>/dev/null | grep -aoE 'ssh [A-Za-z0-9]+@[a-z0-9.]+' | head -1)
  [ -n "$LOG" ] && { echo "TMATE: $LOG"; exit 0; }
  echo "... menunggu runner ($i)"
done
echo "timeout"; exit 1
