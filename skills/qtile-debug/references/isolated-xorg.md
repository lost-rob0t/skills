# Isolated Qtile X11 Test

Use this procedure for visual or Emacs-frame regressions that should not
disturb the active X session. `QTILE_CONFIG_ROOT` defaults to
`$HOME/.config/qtile`; choose an unused display if `:1` is occupied.

```sh
out="$(mktemp -d "${TMPDIR:-/tmp}/qtile-xorg.XXXXXX")"
display="${QTILE_TEST_DISPLAY:-:1}"
screen="${QTILE_TEST_SCREEN:-1920x1080}"
socket="$out/qtile.sock"
server="qtile-debug-$$"
qpid=""
xpid=""

cleanup() {
    DISPLAY="$display" emacsclient -s "$server" -a false \
        --eval '(kill-emacs)' >/dev/null 2>&1 || true
    [ -z "$qpid" ] || kill "$qpid" 2>/dev/null || true
    [ -z "$xpid" ] || kill "$xpid" 2>/dev/null || true
}
trap cleanup EXIT

Xephyr "$display" -screen "$screen" -ac -br -reset >"$out/xorg.log" 2>&1 &
xpid=$!
sleep 2

DISPLAY="$display" emacs --daemon="$server" >"$out/emacs.log" 2>&1 &
for _ in $(seq 1 30); do
    DISPLAY="$display" emacsclient -s "$server" -a false --eval t >/dev/null 2>&1 && break
    sleep 1
done

QTILE_CONFIG_ROOT="${QTILE_CONFIG_ROOT:-$HOME/.config/qtile}"
DISPLAY="$display" QTILE_EMACS_SERVER="$server" \
    qtile start -c "$QTILE_CONFIG_ROOT/config.py" --no-spawn \
    --backend x11 --socket "$socket" --log-path "$out/qtile.log" &
qpid=$!
sleep 3

DISPLAY="$display" qtile cmd-obj --socket "$socket" -o root -f info
DISPLAY="$display" scrot -q 100 "$out/full.png"
```

Pass `DISPLAY="$display"` and `--socket "$socket"` to any additional Qtile
or Emacs command. Never use the active session's Emacs server name. If testing
an Emacs popup, use the unique `$server` and inspect for both the popup frame
and any unexpected `*Minibuf-*` frame.

`Xephyr` opens a nested X display inside the current desktop. It is safer than
starting a second physical Xorg seat for an interactive visual test and still
exercises a separate X11 server, Qtile instance, and Emacs daemon.
