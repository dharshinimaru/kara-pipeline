#!/bin/zsh
# Turn the weekly automatic run on or off.
#
#   ./scripts/schedule.sh on      install and start the weekly schedule
#   ./scripts/schedule.sh off     stop it
#   ./scripts/schedule.sh status  is it on, when did it last run
#   ./scripts/schedule.sh now     run it immediately through launchd

set -e
LABEL=com.karalabs.pipeline
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
REPO="$(cd "$(dirname "$0")/.." && pwd)"
UID_=$(id -u)

case "${1:-status}" in
  on)
    cp "$REPO/launchd/$LABEL.plist" "$PLIST"
    launchctl bootout "gui/$UID_/$LABEL" 2>/dev/null || true
    launchctl bootstrap "gui/$UID_" "$PLIST"
    echo "on. Runs Mondays at 09:00."
    ;;
  off)
    launchctl bootout "gui/$UID_/$LABEL" 2>/dev/null || true
    echo "off."
    ;;
  now)
    launchctl kickstart -p "gui/$UID_/$LABEL"
    ;;
  status)
    if launchctl print "gui/$UID_/$LABEL" >/dev/null 2>&1; then
      echo "on"
      launchctl print "gui/$UID_/$LABEL" | grep -E "runs|last exit code" || true
    else
      echo "off"
    fi
    ;;
  *)
    echo "usage: $0 [on|off|status|now]" >&2
    exit 1
    ;;
esac
