#!/usr/bin/python3
# <swiftbar.title>Inbox Bar</swiftbar.title>
# <swiftbar.hideAbout>true</swiftbar.hideAbout>
# <swiftbar.hideRunInTerminal>true</swiftbar.hideRunInTerminal>
# <swiftbar.hideLastUpdated>true</swiftbar.hideLastUpdated>
# <swiftbar.hideDisappearPlugin>true</swiftbar.hideDisappearPlugin>
"""Menu bar unread counts, read from open Chrome tabs. Refreshes every 30s."""
import os
import re
import subprocess
import sys
import io
import base64
import json
import time

_out = io.StringIO()
_real = sys.stdout
sys.stdout = _out

ALERT = "#FF3B30"
HERE = os.path.dirname(os.path.realpath(__file__))
ROOT = os.path.join(HERE, "..")

# Your inboxes live in config.json (copy config.example.json). Types:
#   gmail     a Gmail tab; "match" is text in its tab title, usually the account's address
#   slack     a Slack tab; optional "match" is text in its tab title, e.g. the workspace name
#   dock_app  an installed app's Dock badge; "app" is its name, e.g. "Google Chat"
with open(os.path.join(ROOT, "config.json")) as f:
    CONFIG = json.load(f)
GROUPS = CONFIG["groups"]
# Optional global hotkey that opens the menu, e.g. "CMD+OPTION+CTRL+I"
HOTKEY = f" shortcut={CONFIG['shortcut']}" if CONFIG.get("shortcut") else ""
SURFACES = [i for g in GROUPS for i in g["inboxes"]]


def matches(inbox, title, url):
    host = {"gmail": "mail.google.com", "slack": "app.slack.com"}.get(inbox["type"])
    return bool(host) and host in url and inbox.get("match", "") in title


SCRIPT = '''
tell application "Google Chrome"
  set out to ""
  repeat with w in windows
    try
      set wid to id of w
      set us to URL of every tab of w
      set ts to title of every tab of w
      repeat with i from 1 to count of us
        set out to out & wid & (character id 9) & i & (character id 9) & (item i of us) & (character id 9) & (item i of ts) & linefeed
      end repeat
    end try
  end repeat
  return out
end tell
'''
LOG = os.path.join(ROOT, ".errors.log")


def tabs():
    """Every Chrome tab as (window id, tab index, url, title). Retries once; a failed read is logged."""
    for attempt in range(2):
        try:
            r = subprocess.run(["osascript", "-e", SCRIPT], capture_output=True, text=True, timeout=20)
            if r.returncode == 0 and r.stdout.strip():
                return [p for p in (l.split("\t", 3) for l in r.stdout.splitlines()) if len(p) == 4]
            err = f"rc={r.returncode} {r.stderr.strip()[:200]}"
        except subprocess.TimeoutExpired:
            err = "timeout"
        with open(LOG, "a") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} attempt {attempt + 1}: {err}\n")
    return None


def dock_count(app):
    """Read an app's Dock badge (e.g. Google Chat, which doesn't put unread in its title).
    Needs SwiftBar in System Settings > Privacy & Security > Accessibility."""
    script = ('tell application "System Events" to tell process "Dock" to '
              f'get value of attribute "AXStatusLabel" of UI element "{app}" of list 1')
    r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=10)
    if r.returncode:
        return None  # no permission, or Chat not in the Dock
    v = r.stdout.strip()
    if v in ("", "missing value"):
        return 0
    return int(v) if v.isdigit() else "•"


def read_count(title, url, wid, ti):
    """Returns an int, '•' (unread, no number), or None (can't tell from this view)."""
    if "mail.google.com" in url:
        m = re.match(r"^Inbox \(([\d,]+)\)", title)
        if m:
            return int(m.group(1).replace(",", ""))
        return 0 if title.startswith("Inbox ") else None  # reading a thread hides the count
    m = re.search(r"(\d+) new items?", title) or re.search(r"\((\d+)\)", title)  # Slack: "- 2 new items -"
    if m:
        return int(m.group(1))
    if title.startswith(("*", "!", "•")):
        return "•"
    return 0


found = {}
all_tabs = tabs()
for wid, ti, url, title in all_tabs or []:
    for inbox in SURFACES:
        if inbox["label"] not in found and matches(inbox, title, url):
            found[inbox["label"]] = (read_count(title, url, wid, ti), wid, ti)
for inbox in SURFACES:
    if inbox["type"] == "dock_app":
        found[inbox["label"]] = (dock_count(inbox["app"]), None, None)

# Gmail drops the count from the title while you're on an email: fall back to the last count seen.
STATE = os.path.join(ROOT, ".last-counts.json")
try:
    with open(STATE) as f:
        last = json.load(f)
except (OSError, ValueError):
    last = {}
stale = set()
if all_tabs is None:  # Chrome didn't answer this round: keep showing the last counts
    for label in (i["label"] for i in SURFACES):
        if label not in found and label in last:
            found[label] = (None, None, None)
for label, (c, wid, ti) in list(found.items()):
    if c is None and label in last:
        found[label] = (last[label], wid, ti)
        stale.add(label)
    elif c is not None:
        last[label] = c
try:
    with open(STATE, "w") as f:
        json.dump(last, f)
except OSError:
    pass

counts = [found.get(i["label"], (0,))[0] for i in SURFACES]
unread = [c for c in counts if c]
total = sum(c for c in unread if isinstance(c, int))

if unread:
    name = "dot" if not total else (str(total) if total <= 99 else "99+")
    dark = subprocess.run(["defaults", "read", "-g", "AppleInterfaceStyle"], capture_output=True, text=True).stdout.strip() == "Dark"
    icons = os.path.join(ROOT, "icons", "dark" if dark else "light")
    with open(os.path.join(icons, f"{name}.png"), "rb") as f:  # tray with red count badge (make_icons.swift)
        print(f"| image={base64.b64encode(f.read()).decode()}{HOTKEY}")
else:
    print(f"| sfimage=tray{HOTKEY}")
print("---")

def row_icon(name, on):
    """Pre-rendered row icon (make_icons.swift); SwiftBar's own colored symbols vanish after hover."""
    path = os.path.join(ROOT, "icons", "rows", f"{name}-{'on' if on else 'off'}.png")
    with open(path, "rb") as f:
        return "image=" + base64.b64encode(f.read()).decode()


focus = os.path.join(ROOT, "focus.sh")
for gi, group in enumerate(GROUPS):
    if gi:
        print("---")
    print(f"{group['heading']} | size=11 color=gray")
    for inbox in group["inboxes"]:
        label = inbox["label"]
        icon = {"gmail": "gmail", "slack": "slack", "dock_app": "chat"}[inbox["type"]]
        if label not in found:
            print(f"\033[90m{label}  ·  tab not open\033[0m | ansi=true {row_icon(icon, False)}")  # ANSI gray: color= makes the icon vanish on hover
            continue
        c, wid, ti = found[label]
        if inbox["type"] == "dock_app":
            app_id = subprocess.run(["osascript", "-e", f'id of app "{inbox["app"]}"'], capture_output=True, text=True).stdout.strip()
            click = f"bash=/usr/bin/open param1=-b param2={app_id} terminal=false" if app_id else ""
        else:
            click = f"bash={focus} param1={wid} param2={ti} terminal=false" if wid else ""
        note = "  (last seen)" if label in stale else ""
        if c is None:
            print(f"\033[90m{label}  ·  ?\033[0m | ansi=true {row_icon(icon, True)} {click}")
        elif c:
            red = "\033[1;31m"  # standard red, bold; bright red was too harsh and 24-bit color did not render
            print(f"\033[1m{label}\033[0m  {red}{c}\033[0m{note} | ansi=true {row_icon(icon, True)} {click}")
        else:
            print(f"\033[90m{label}  ·  0{note}\033[0m | ansi=true {row_icon(icon, False)} {click}")
print("---")
print("Refresh | refresh=true")

sys.stdout = _real
print(_out.getvalue(), end="")
try:  # last run's output, for debugging
    with open(os.path.join(ROOT, ".last-output"), "w") as f:
        f.write(_out.getvalue())
except OSError:
    pass
