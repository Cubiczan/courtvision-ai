from playwright.sync_api import sync_playwright
import subprocess
import time
import os
import signal
import sys

SCREENSHOTS_DIR = "/home/z/my-project/courtvision-ai/dashboard/screenshots"
BASE_URL = "http://localhost:3456"
DASHBOARD_DIR = "/home/z/my-project/courtvision-ai/dashboard"

os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

# Start the server
print("Starting Next.js server...")
server_proc = subprocess.Popen(
    ["npx", "next", "start", "-p", "3456"],
    cwd=DASHBOARD_DIR,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
    preexec_fn=os.setpgrp
)

# Wait for server to be ready
print("Waiting for server...")
for i in range(30):
    try:
        import urllib.request
        req = urllib.request.urlopen(BASE_URL, timeout=2)
        if req.status == 200:
            print("Server is ready!")
            break
    except:
        pass
    time.sleep(1)
else:
    print("Server failed to start!")
    os.killpg(os.getpgid(server_proc.pid), signal.SIGTERM)
    sys.exit(1)

TAB_CONFIG = [
    ("games", "Games", "01-games.png"),
    ("predictions", "Predictions", "02-predictions.png"),
    ("markets", "Markets", "03-markets.png"),
    ("leaderboard", "Leaderboard", "04-leaderboard.png"),
]

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(
        viewport={"width": 1440, "height": 1024},
        device_scale_factor=2,
    )

    # Navigate to the page
    print("Loading page...")
    page.goto(BASE_URL, wait_until="domcontentloaded")
    time.sleep(3)

    for tab_name, label, filename in TAB_CONFIG:
        print(f"Taking screenshot: {tab_name}...")
        # Click the tab
        page.click(f"button:has-text('{label}')")
        time.sleep(2)

        # Scroll to bottom
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(0.5)
        # Scroll back to top
        page.evaluate("window.scrollTo(0, 0)")
        time.sleep(0.5)

        # Take full-page screenshot
        filepath = os.path.join(SCREENSHOTS_DIR, filename)
        page.screenshot(path=filepath, full_page=True, type="png")
        print(f"  Saved: {filepath}")

    browser.close()
    print("All screenshots taken!")

# Kill the server
os.killpg(os.getpgid(server_proc.pid), signal.SIGTERM)
print("Server stopped.")
