#!/bin/bash
# Bring Chrome window $1 (window id) to front with tab $2 active.
osascript -e "tell application \"Google Chrome\"
  set w to (first window whose id is $1)
  set active tab index of w to $2
  set index of w to 1
  activate
end tell"
