---
name: zara-phone-pair
description: zara, phone, pairing, adb, wireless-debugging, curve, enrollment, android
compatibility: Requires android-tools (adb), the zara-adb-pair script (zara.workflows), and a running zara-server with a remote listener.
---

# Pair the Zara phone app to this zara-server

## Goal

The Zarathushtra Android app (`ai.zara.app`) authenticated to this host's
zara-server over CURVE, with the turn path verified end to end.

## Input

An adb-reachable phone, the desktop LAN IP of the server (default port 6060),
and the security state dir (default `~/.local/state/zarathushtra/security`).

## Output

A connected/authenticated phone session, or the precise blocked step
(locked screen, foreign focused app, stale endpoint, enrollment rejection).

## Fast path (preferred)

Run the maintained tool; it is guarded and idempotent:

```sh
zara-adb-pair                 # guarded: aborts if another app has focus
zara-adb-pair --takeover      # bring Zara to the foreground and pair
zara-adb-pair --check         # report state only, inject nothing
```

It reads the client key from the app UI, enrolls it server-side, pins the
server key, fills the endpoint, taps Connect, and verifies AUTHENTICATED.

## Manual fallback (no script)

1. Server side (while `zara-server` runs with
   `--remote-endpoint tcp://0.0.0.0:6060 --security-dir <DIR>`):
   - public key: `zara-server --security-dir <DIR> --security-show-public-key`
   - enroll phone: `zara-server --security-dir <DIR> --security-enroll-key <Z85> --security-device-id <ID>`
2. Phone side (Settings → Connection):
   - read CLIENT PUBLIC KEY (40-char Z85); enroll it server-side
   - paste server key into *Server CURVE public key* → *Pin server key*
   - *SERVER* section: `tcp://<LAN-IP>:6060` → *Connect*
3. Verify: app footer shows `REMOTE • AUTHENTICATED • SYMBOLIC`; server shows
   `ESTAB <ip>:6060` in `ss -tn`; submit a turn and watch
   `journalctl --user -u zara-server` for `[TurnCoordinator] started turn`.

## Hard rules

- Never inject input while another app owns `mCurrentFocus`. Check
  `adb shell dumpsys window | grep mCurrentFocus` before every tap/type;
  a stray keystroke lands in whatever the user is doing (this has really
  happened: an Amazon search got typed into).
- A locked phone shows `Bouncer` focus. Stop and ask the user to unlock;
  never attempt PIN entry.
- `adb shell input text` runs through the device shell: wrap the payload in
  embedded single quotes, e.g. send the single argv token
  `input text 'KEY'` — Z85 keys contain `$ & ( ) { } # ? %`.
- The pairing port and the connect port of wireless debugging are distinct;
  prefer an already-established TLS adb transport (`adb devices -l`, state
  exactly `device`).
- uiautomator dumps can return empty or the wrong window in split-screen;
  retry, and tap the Zara half first to steal focus back.
- "enrollment ready" on the phone only means local identity + server pin;
  server-side enrollment and a live connection are separate facts.
- Fail closed on server key changes: re-pinning requires the explicit
  *Change trusted server key* flow.

## Troubleshooting

- `protocol_error` bubbles after a turn reaches the server: the desktop
  build is older than the app. Rebuild/switch home-manager from the current
  zara pin, then reconnect.
- Auto-reconnect: with Chat Backend `Auto`, the app reconnects by itself
  after a server restart once the endpoint is saved.
- Server binds `0.0.0.0:6060`; use the host's LAN address
  (`ip route get 1.1.1.1` → `src`), not localhost, on the phone.
