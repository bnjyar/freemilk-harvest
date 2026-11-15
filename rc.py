import json, os, sys, time, urllib.request, base64
REPO = "bnjyar/freemilk-harvest"
TOKEN = os.environ["GH_TOKEN"]
API = "https://api.github.com"
URL = f"{API}/repos/{REPO}/issues/1/comments"

def req(url, method="GET", data=None):
    r = urllib.request.Request(url, method=method, data=json.dumps(data).encode() if data else None)
    r.add_header("Authorization", "Bearer " + TOKEN)
    r.add_header("Accept", "application/vnd.github+json")
    if data: r.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(r, timeout=60) as f:
        return json.loads(f.read() or b"[]")

def all_comments():
    out, page = [], 1
    while True:
        c = req(f"{URL}?per_page=100&page={page}")
        out += c
        if len(c) < 100: return out
        page += 1

cmd = sys.stdin.read().strip()
prev = max([c["id"] for c in all_comments()] or [0])
req(URL, "POST", {"body": "!b64:" + base64.b64encode(cmd.encode()).decode()})
deadline = time.time() + 900
while time.time() < deadline:
    time.sleep(3)
    for c in all_comments():
        if c["id"] > prev and not c["body"].startswith("!"):
            print(c["body"]); sys.exit(0)
print("(timeout)"); sys.exit(1)
