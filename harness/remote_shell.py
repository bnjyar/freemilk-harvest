"""Poll GitHub issue #1 for commands (comments starting with '!'), run them, post output.

Special commands:
  !shot            -> screencapture, upload PNG to repo path shots/latest.png, comment raw URL
  !open            -> open -a the installed app
"""
import json, os, subprocess, time, urllib.request, base64, glob

REPO = os.environ.get("GITHUB_REPOSITORY", "bnjyar/freemilk-harvest")
TOKEN = os.environ["GH_TOKEN"]
ISSUE = 1
API = "https://api.github.com"

def api(path, method="GET", data=None, raw=False):
    req = urllib.request.Request(API + path, method=method,
        data=json.dumps(data).encode() if data is not None else None)
    req.add_header("Authorization", "Bearer " + TOKEN)
    req.add_header("Accept", "application/vnd.github+json")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read() if raw else json.loads(r.read() or b"{}")

def comment(body):
    api(f"/repos/{REPO}/issues/{ISSUE}/comments", "POST", {"body": body[:60000]})

def upload_shot(path):
    with open(path, "rb") as f:
        content = base64.b64encode(f.read()).decode()
    api(f"/repos/{REPO}/contents/shots/latest.png", "PUT",
        {"message": "shot", "content": content})

def app_path():
    c = glob.glob("/Applications/*.app")
    return c[0] if c else None

seen = set()
c0 = api(f"/repos/{REPO}/issues/{ISSUE}/comments?per_page=100")
for c in c0:
    seen.add(c["id"])
comment("runner ready: %s / %s" % (subprocess.run(["sw_vers","-productVersion"],capture_output=True,text=True).stdout.strip(), os.uname().machine))

while True:
    try:
        cs = api(f"/repos/{REPO}/issues/{ISSUE}/comments?per_page=100")
    except Exception as e:
        time.sleep(10); continue
    for c in cs:
        if c["id"] in seen:
            continue
        seen.add(c["id"])
        body = c["body"].strip()
        if not body.startswith("!"):
            continue
        cmd = body[1:].strip()
        if cmd == "shot":
            subprocess.run(["screencapture", "-x", "/tmp/shot.png"], capture_output=True)
            subprocess.run(["sips", "-s", "format", "jpeg", "-Z", "1400", "/tmp/shot.png", "--out", "/tmp/shot.jpg"], capture_output=True)
            upload_shot("/tmp/shot.jpg")
            comment("shot: https://raw.githubusercontent.com/%s/HEAD/shots/latest.png" % REPO)
            continue
        if cmd == "open":
            a = app_path()
            comment("opening %s" % a)
            subprocess.run(["open", "-a", a], capture_output=True)
            continue
        try:
            p = subprocess.run(["bash", "-lc", cmd], capture_output=True, text=True, timeout=600)
            out = (p.stdout + "\n" + p.stderr).strip()
        except Exception as e:
            out = "ERR %r" % e
        comment("$ %s\n%s" % (cmd, out[:20000] or "(no output)"))
    time.sleep(6)
