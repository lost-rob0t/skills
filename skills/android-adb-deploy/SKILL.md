---
name: android-adb-deploy
description: android, adb, wireless-debugging, apk, build, deploy, wearos
compatibility: Requires Android platform-tools and the target project's declared build dependencies.
---

# Deploy Android with ADB

## Goal

Build, test, install, and verify an Android application on the intended phone, tablet, emulator, TV, or Wear OS device.

## Input

A project checkout, deployment intent, optional ADB serial or wireless-debugging endpoints, and the expected package IDs.

## Output

Verified build artifacts and package installations, or a precise build, pairing, target-selection, install, or verification failure.

## Select the target

1. Read the project's instructions and maintained build/deploy entry points before constructing commands.
2. Run `adb devices -l` and consider only entries whose state is exactly `device`.
3. Preserve the complete serial left of the first tab before the device state as one quoted argument. Wireless mDNS serials can contain spaces and need not resemble `HOST:PORT`.
4. Confirm candidates with properties such as `ro.product.model`, `ro.product.name`, and `ro.build.characteristics`. Match the requested device class instead of guessing from its address.
5. Use a supplied serial only after confirming that exact target is online. If multiple candidates remain, ask the user which one to use.

## Wireless debugging

1. Prefer a project's maintained pairing helper when one exists. Otherwise use fresh endpoints shown by Android's Wireless debugging screen:

   ```sh
   adb pair HOST:PAIR_PORT
   adb connect HOST:ADB_PORT
   ```

2. Treat the pairing port and normal ADB port as distinct. Enter the pairing code only at ADB's interactive prompt.
3. Diagnose discovery with `adb mdns services`, `adb devices -l`, and `adb server-status`. Restart the local daemon only when its state is stale.
4. If trust was removed on the device, pair again. Do not delete ADB keys or alter network security settings without explicit approval.

## Build and install

1. Run the project's required tests and maintained debug or deployment build. Stop on any failed contract, test, or build.
2. Identify artifacts and package IDs from build configuration or manifests; do not infer them solely from filenames.
3. Prefer a maintained deployment command that verifies its work. Otherwise install a single APK with:

   ```sh
   adb -s "$serial" install -r "$apk"
   ```

4. Use `install-multiple -r` for a validated split-APK set. An Android App Bundle is not directly installable; use the project's supported APK-generation path.
5. Verify every expected package independently:

   ```sh
   adb -s "$serial" shell pm path "$package_id"
   ```

6. Launch or configure the app only when requested. Report the target model, build/test result, artifact, install result, and package verification.

## StarIntel Wear OS recipe

When the checkout exposes the StarIntel Nix apps, build all modules and let the maintained installer deploy and verify the Wear app plus watch face:

```sh
nix run .#build-all
nix run .#install-watch -- "$serial"
```

The expected watch packages are `actor.starintel.wear` and `actor.starintel.watchface`. Never install the phone APK on a watch.

## Rules

- Never hard-code a serial, private address, port, pairing code, APK path, or package ID as a universal default.
- Prefer an exact online serial from `adb devices` over a stale remembered endpoint.
- Preserve user data with `-r` unless the user explicitly requests a clean reinstall.
- After source updates or a request to deploy "again," rebuild before installing.
- Do not report success from pairing, an open TCP port, or `adb install` alone; verify the expected packages.
