---
name: qtile-confirm
description: qtile, screenshots, vision, visual-regression, bar-layout
compatibility: Requires a vision-capable agent runtime and an X11 or Wayland screenshot tool; ImageMagick is required for cropping.
---

# Confirm Qtile visually

## Goal

Confirm that the live Qtile desktop matches a requested visual invariant instead
of treating a successful reload or widget callback as visual proof.

## Stop gate

Before taking a screenshot, determine whether the host can return an image that
the agent can inspect visually. If it cannot, tell the user:

> This runtime does not support vision, so I cannot confirm Qtile from a screenshot.

Stop. Do not substitute OCR, pixel metadata, or shell output for visual
confirmation.

## Workflow

1. Discover the configuration root with `QTILE_CONFIG_ROOT`, defaulting to
   `$HOME/.config/qtile`. Do not assume a repository path.
2. Record runtime context before interpreting the image:

   ```sh
   printf 'session=%s display=%s\n' "${XDG_SESSION_TYPE:-unknown}" "${DISPLAY:-${WAYLAND_DISPLAY:-unknown}}"
   xrandr --query 2>/dev/null || true
   systemctl --user is-active qtile.service 2>/dev/null || true
   qtile cmd-obj -o screen 0 -f info 2>/dev/null || true
   ```

3. Capture the whole desktop into a temporary directory. Use `scrot` for X11 or
   `grim` for Wayland. If neither is available, stop and report the missing
   capability rather than claiming confirmation.

   ```sh
   out="$(mktemp -d "${TMPDIR:-/tmp}/qtile-confirm.XXXXXX")"
   full="$out/full.png"
   if command -v scrot >/dev/null 2>&1; then
       scrot -q 100 "$full"
   elif command -v grim >/dev/null 2>&1; then
       grim "$full"
   else
       printf '%s\n' 'No scrot or grim screenshot tool is installed.' >&2
       exit 1
   fi
   identify "$full"
   ```

4. Inspect the full image with the host vision tool. Choose the smallest region
   containing the widget, bar, popup, or monitor boundary under investigation.
5. Crop that region with an image-editing command, not an estimated description:

   ```sh
   crop="${QTILE_CONFIRM_CROP:?set WxH+X+Y after inspecting the full screenshot}"
   roi="$out/roi.png"
   if command -v magick >/dev/null 2>&1; then
       magick "$full" -crop "$crop" +repage "$roi"
   else
       convert "$full" -crop "$crop" +repage "$roi"
   fi
   identify "$roi"
   ```

6. Inspect the cropped image and compare it to the user’s explicit invariant.
   State what is visibly correct, what remains wrong, and the crop geometry.
7. Keep the temporary images for the current investigation only; remove them
   after reporting unless the user asks to retain evidence.

## Rules

- A screenshot is required for claims about spacing, clipping, alignment, color,
  visibility, popup placement, or monitor topology.
- Use runtime commands only to correlate the image with Qtile state; they do not
  replace image inspection.
- Capture another focused crop after any edit or reload that changes layout.
- Never expose raw telemetry or screenshots containing private window titles
  without warning the user.
