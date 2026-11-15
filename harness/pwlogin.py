"""Drive Google sign-in headlessly and print the OAuth redirect URL.

usage: python3 pwlogin.py <authorize-url> <email> <password>
Prints progress to stdout; the redirect URL is printed as "REDIRECT <url>".
"""
import sys, time
from playwright.sync_api import sync_playwright

url, email, password = sys.argv[1], sys.argv[2], sys.argv[3]
REDIRECT = "com.googleusercontent.apps.311745113120-"

def log(*a):
    print(*a, flush=True)

with sync_playwright() as p:
    b = p.chromium.launch(headless=True, args=[
        "--no-sandbox", "--disable-blink-features=AutomationControlled",
        "--disable-dev-shm-usage"])
    ctx = b.new_context(
        locale="en-US",
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/159.0.0.0 Safari/537.36",
        viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    caught = []

    def on_req(r):
        if r.url.startswith(REDIRECT):
            caught.append(r.url)

    page.on("request", on_req)
    page.on("framenavigated", lambda f: on_req(type("R", (), {"url": f.url})()))

    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    log("STATE 0", page.url)

    # email step
    for sel in ['input[type="email"]', "#identifierId", 'input[name="identifier"]']:
        try:
            page.wait_for_selector(sel, timeout=15000)
            page.fill(sel, email)
            log("filled email with", sel)
            break
        except Exception:
            continue
    for sel in ["#identifierNext", 'button:has-text("Next")']:
        try:
            page.click(sel, timeout=5000); break
        except Exception:
            pass
    page.wait_for_timeout(4000)
    log("STATE 1", page.url)

    # password step
    for sel in ['input[type="password"]', 'input[name="Passwd"]']:
        try:
            page.wait_for_selector(sel, timeout=30000)
            page.fill(sel, password)
            log("filled password")
            break
        except Exception:
            log("no password field yet")
    for sel in ["#passwordNext", 'button:has-text("Next")']:
        try:
            page.click(sel, timeout=5000); break
        except Exception:
            pass
    page.wait_for_timeout(4000)
    log("STATE 2", page.url)

    # wait for either the redirect or a challenge
    deadline = time.time() + 420
    seen = set()
    while time.time() < deadline:
        if caught:
            log("REDIRECT", caught[0]); break
        u = page.url
        if u not in seen:
            seen.add(u); log("STATE 3", u)
        try:
            body = page.inner_text("body")[:400].replace("\n", " | ")
            if body and body not in seen:
                seen.add(body); log("TEXT", body)
        except Exception:
            pass
        # press "Continue"/"Allow" if a consent screen is up
        for sel in ['button:has-text("Continue")', 'button:has-text("Allow")', 'button:has-text("Next")']:
            try:
                el = page.query_selector(sel)
                if el:
                    el.click(); log("clicked", sel); page.wait_for_timeout(2500)
                    try:
                        page.click('button:has-text("Continue")', timeout=3000)
                        log("clicked Continue again")
                    except Exception:
                        pass
                    break
            except Exception:
                pass
        page.wait_for_timeout(4000)
    if not caught:
        try:
            page.screenshot(path="/tmp/pw.png")
            log("SHOT /tmp/pw.png")
        except Exception:
            pass
        log("NO_REDIRECT url=" + page.url)
    b.close()
