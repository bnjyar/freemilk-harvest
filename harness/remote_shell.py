"""Poll GitHub issue #1 for commands, run them on this macOS runner, post output.

Comment protocol: body "!b64:<base64 of the shell command>".
Special commands: "shot" (screencapture + upload), "open" (launch the app).
"""
import base64, glob, json, os, subprocess, time, traceback, urllib.request

REPO = os.environ.get("GITHUB_REPOSITORY", "bnjyar/freemilk-harvest")
TOKEN = os.environ["GH_TOKEN"]
ISSUE = 1
API = "https://api.github.com"
CURL = f"{API}/repos/{REPO}/issues/{ISSUE}/comments"

def api(path, method="GET", data=None):
    r = urllib.request.Request(API + path, method=method,
        data=json.dumps(data).encode() if data is not None else None)
    r.add_header("Authorization", "Bearer " + TOKEN)
    r.add_header("Accept", "application/vnd.github+json")
    if data is not None:
        r.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(r, timeout=60) as f:
        body = f.read()
        return json.loads(body or b"{}")

def all_comments():
    out, page = [], 1
    while True:
        c = api(f"/repos/{REPO}/issues/{ISSUE}/comments?per_page=100&page={page}")
        out += c
        if len(c) < 100:
            return out
        page += 1

def comment(text):
    api(f"/repos/{REPO}/issues/{ISSUE}/comments", "POST", {"body": text[:60000]})

def say(msg):
    try: comment(msg)
    except Exception: pass

def run(cmd, timeout=600):
    p = subprocess.run(["bash", "-lc", cmd], capture_output=True, text=True, timeout=timeout)
    return ((p.stdout or "") + (p.stderr or "")).strip()

def shot():
    subprocess.run(["screencapture", "-x", "/tmp/shot.png"], capture_output=True, timeout=120)
    subprocess.run(["sips", "-s", "format", "jpeg", "-Z", "1400", "/tmp/shot.png", "--out", "/tmp/shot.jpg"],
                   capture_output=True, timeout=120)
    with open("/tmp/shot.jpg", "rb") as f:
        content = base64.b64encode(f.read()).decode()
    name = "shots/shot-%d.png" % int(time.time())
    api(f"/repos/{REPO}/contents/{name}", "PUT", {"message": "shot", "content": content})
    return "https://raw.githubusercontent.com/%s/HEAD/%s" % (REPO, name)

seen = {c["id"] for c in all_comments()}
say("runner ready: %s / %s" % (run("sw_vers -productVersion"), os.uname().machine))

while True:
    try:
        cs = all_comments()[-200:]
    except Exception:
        time.sleep(10); continue
    for c in cs:
        if c["id"] in seen:
            continue
        seen.add(c["id"])
        body = c["body"].strip()
        if not body.startswith("!"):
            continue
        try:
            cmd = body[1:].strip()
            if cmd.startswith("b64:"):
                cmd = base64.b64decode(cmd[4:]).decode()
            if cmd == "shot":
                say("shot: " + shot()); continue
            if cmd == "open":
                app = (glob.glob("/Applications/*.app") or [None])[0]
                say("open %s" % run("open -a %s" % app)); continue
            out = run(cmd)
        except Exception:
            out = "EXC\n" + traceback.format_exc()
        say("$ %s\n%s" % (cmd, out[:20000] or "(no output)"))
    time.sleep(6)
