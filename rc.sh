#!/bin/bash
# rc.sh 'command' -> kirim ke runner macOS (base64), tunggu, cetak balasan
set -eu
R=bnjyar/freemilk-harvest
API=https://api.github.com/repos/$R/issues/1/comments
g() { curl -sS -H "Authorization: Bearer $GH_TOKEN" -H 'Accept: application/vnd.github+json' "$@"; }
last=$(g "$API?per_page=100&sort=created&direction=desc" | python3 -c 'import sys,json;c=json.load(sys.stdin);print(max([x["id"] for x in c]) if c else 0)')
cmd=$(cat)
body=$(CMD="$cmd" python3 -c 'import os,json,base64;print(json.dumps({"body":"!b64:"+base64.b64encode(os.environ["CMD"].encode()).decode()}))')
g -X POST "$API" -d "$body" >/dev/null
for i in $(seq 1 200); do
  sleep 3
  out=$(g "$API?per_page=50&sort=created&direction=desc" | LAST="$last" python3 -c '
import sys,json,os
last=int(os.environ["LAST"]); cs=json.load(sys.stdin)
for c in cs:
    if c["id"]>last and not c["body"].startswith("!"):
        print(c["body"]); break
')
  if [ -n "${out:-}" ]; then echo "$out"; exit 0; fi
done
echo "(timeout)"; exit 1
