# MeekroOS

**Fedora-based GNOME Linux for developers and gamers**

> **Developer preview v0.1.0.** This repository contains experimental installer branding, a GTK4/libadwaita first-run assistant and a Control Center. It is **not yet a bootable ISO** or a fully independent disk installer. **Do not test on disks containing important data.**

## Components

- **Meekro Live Installer:** a branded Live entry point into Fedora Anaconda; the verified Anaconda installer remains responsible for disk partitioning, encryption and bootloader setup.
- **Meekro Welcome:** first-run personalisation, app selection and setup assistance.
- **Meekro Control Center:** user-level GNOME appearance preferences, developer/gaming software catalogue, hardware information and portable settings.
- **Easter egg:** type `eekrob_` while the Meekro window is focused.

## Status

This project has not yet been run through a full Fedora Live ISO/RPM integration test. GNOME Wayland does not offer a universal application-window blur/opacity API; Shell effects can be enabled where supported by GNOME extensions. Drivers and third-party repositories must always be explicitly approved.

## Development

On Fedora GNOME with the required GTK4/libadwaita and Python GI bindings installed, run:

```bash
python3 -m meekro.app
python3 -m meekro.app --first-run
python3 -m unittest discover -s tests -v
```

Build scripts and the full detailed README are included with the source archive available in the original project conversation. The repository will be populated with the source tree separately.

## Attribution

MeekroOS is an independent Fedora-based project, not endorsed by Fedora/Red Hat. Code is MIT-licensed; MeekroOS graphics remain the property of their respective owner and are not automatically covered by MIT.
