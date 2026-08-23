# Desktop authentication boundary

This skill uses desktop-mediated authorization, not credential handling by the agent.

## Standard Linux path

XDG Desktop Portal exposes D-Bus interfaces for desktop capabilities such as file access, URI opening, printing, screen capture, and secrets. It does not define a general portal for authorizing arbitrary root commands.

Use this one-liner to determine whether the common portal broker is reachable through either of the usual Linux D-Bus clients:

```sh
portal="$(if command -v busctl >/dev/null 2>&1 && busctl --user --quiet --no-pager status org.freedesktop.portal.Desktop >/dev/null 2>&1; then printf xdg-desktop-portal; elif command -v gdbus >/dev/null 2>&1 && gdbus call --session --dest org.freedesktop.portal.Desktop --object-path /org/freedesktop/portal/desktop --method org.freedesktop.DBus.Peer.Ping >/dev/null 2>&1; then printf xdg-desktop-portal; fi)"
```

An available broker is necessary for this skill's desktop requirement, but it is not proof that a polkit authentication agent is registered. The `pkexec --disable-internal-agent` invocation is the fail-closed authentication check.

For privileged operations, the standard desktop boundary is polkit:

1. the polkit authority evaluates the action;
2. the graphical session registers an authentication agent;
3. `pkexec` requests authorization and uses that registered agent;
4. `--disable-internal-agent` makes the request fail if no graphical agent is available instead of opening a textual prompt.

Do not pass a password from an XDG Secret portal into `sudo` or `pkexec`. Secret storage and privilege authorization are different capabilities.

Authoritative references:

- [XDG Desktop Portal documentation](https://flatpak.github.io/xdg-desktop-portal/docs/)
- [polkit architecture and authentication agents](https://polkit.pages.freedesktop.org/polkit/polkit.8.html)
- [`pkexec` authentication-agent behavior](https://polkit.pages.freedesktop.org/polkit/pkexec.1.html)
