# inbox-bar

A macOS menu bar icon that shows unread counts across the Gmail inboxes, Slack workspaces and chat apps I keep open in Chrome, so I can stop cycling through windows to check whether I'm missing something.

The icon is a tray. When something is unread it gets a red badge with the total. Click it for a list grouped however you like (personal, work, side project), with each inbox's count. Click a line to jump straight to that tab.

It runs as a [SwiftBar](https://swiftbar.app) plugin and checks every 30 seconds. There are no logins or API keys. It reads what's already on screen:

- **Gmail** puts the inbox count in the tab title ("Inbox (3) - ..."), so it reads Chrome's tab titles over AppleScript.
- **Slack** does the same ("... - 2 new items - Slack").
- **Google Chat** doesn't, so it reads the red badge on the Google Chat app's Dock icon instead (install Chat as a Chrome app for that).

## Setup

1. `brew install --cask swiftbar`
2. Clone this repo and copy `config.example.json` to `config.json`. List your inboxes there. For Gmail, `match` is text from that account's tab title, usually its address.
3. Point SwiftBar's plugin folder at `plugins/`.
4. For Dock badges (Google Chat): System Settings > Privacy & Security > Accessibility, add SwiftBar.

The first run will ask to let SwiftBar control Chrome. Say yes.

## Limits

- The tab has to be open. That's the whole trick.
- Gmail drops the count from the title while you're reading an email, so it shows the last count it saw, marked "(last seen)".
- Chrome only. Safari or Arc would need their own AppleScript.

## Files

- `plugins/inbox.30s.py`: the plugin. The `30s` in the name is SwiftBar's refresh interval.
- `focus.sh`: brings a Chrome tab to the front when you click a line.
- `make_icons.swift`: draws the badge and row icons in `icons/`. Run `swift make_icons.swift` to regenerate.

## SwiftBar quirks I hit

- Using `color=` on a menu line, or SwiftBar's built-in `sfimage` icons, made the line's icon vanish after hovering over it. Lines use pre-drawn `image=` icons and ANSI codes for color instead.
- 24-bit ANSI colors don't render. The basic codes (`31` red, `90` gray) do.
- `sfcolor=gray` draws nothing. Use a hex color.
