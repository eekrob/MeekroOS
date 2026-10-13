# MeekroOS — Installer, Welcome & Control Center

**Status: v0.1.0 developer preview. Not a finished Live ISO.**

MeekroOS is a Fedora Workstation-based GNOME experience for developers and gamers. It has three intended layers:

1. **Meekro Live Installer:** own branded Live session entrypoint. It launches Fedora's **Anaconda** engine, with the supported Anaconda WebUI branding CSS and Meekro logo. Standard Fedora live Welcome is disabled in the composed image.
2. **Meekro First Run:** user-level GNOME personalization and optional software installation, after account creation and first login.
3. **Meekro Control Center:** rerunnable appearance, package catalog, profile selection, GPU inventory and JSON settings import/export.

The logo was provided for the project by the user (asset from the approved conversation). The code is MIT licensed; **branding artwork is not automatically relicensed by this repository**. Ask the image rights holder before reuse outside MeekroOS.

## What works in the source

- Native GTK4/libadwaita UI built with Python + PyGObject; Fedora/GNOME styled.
- Live session button calls `/usr/bin/liveinst` after checking environment; does not invoke a custom partitioning script.
- Anaconda WebUI CSS at `branding/branding.css` (red, dark and light token overrides) and the project's logo.
- First run with a completion marker in `~/.local/state/meekro/first-run-complete`.
- Four app categories: Developer, Gaming, Everyday, Appearance. Python, Node/npm, IDEs, browsers, Steam, Heroic, Bottles, ProtonUp-Qt, OBS etc.
- DNF5 RPM operations through `pkexec`, Flatpak applications through explicitly consented user-level Flathub. Preview and confirmation before changes.
- Developer, Gamer and Hybrid profiles that **select**, not install, packages.
- GNOME dark/light/system color preference and red accent (if supported by active GNOME schema).
- Optional packaged Blur my Shell (for GNOME overview, panel and shell surfaces). Universal per-window opacity on GNOME Wayland is **not** implemented.
- GPU, CPU and RAM read-only inventory; curated Mesa/Vulkan install choices. NVIDIA proprietary driver installation intentionally remains manual.
- Portable validated JSON settings import/export; hidden Easter egg when typing `eekrob_` while the application has keyboard focus. No system-wide key capture.
- Unit tests, RPM spec and a Kickstart overlay helper for a Fedora live image compose.

## Significant limitations / no false claims

**Disk installation still runs Anaconda WebUI.** We replace the visible Live Welcome and theme its installer; this is **not** a full fork/reimplementation of Anaconda pages (disk, encryption, accounts, progress). A full custom installer workflow would require a separately tested Anaconda WebUI fork or upstream-supported extension mechanism.

**Not built or tested as an ISO on Fedora yet.** Source-level tests run on Python without root. Build an RPM/ISO on a Fedora 44 machine and test in a disposable virtual machine (BIOS, UEFI, encryption, dual boot, disconnected installs) *before* testing on real drives.

Flatpak availability changes, `pkexec` authorization can be denied, and GNOME extensions may need session restart or updates. No promise that every package exists in every Fedora/Flathub configuration. Flatpak IDE sandboxes may require explicit host-toolchain integrations.

Installation cancellation takes effect **between** operations only; in-flight RPM transactions must finish. Export/import does not transfer already installed apps or drivers. No rollback/snapshot mechanism exists yet.

By default neither Flathub nor any third-party RPM source is added without consent. Driver installation never silently configures proprietary repositories.

## Run app on Fedora (development)

Suggested commands on a Fedora 44 workstation with GNOME installed (GUI not tested in the build sandbox):

```bash
sudo dnf install python3 python3-gobject gtk4 libadwaita flatpak dnf5 polkit pciutils
python3 -m meekro.app               # opens Control Center from a checkout
python3 -m meekro.app --first-run   # First Run unless already completed
MEEKRO_DEV_PREVIEW=1 python3 -m meekro.app --live  # UI preview only; disk install is BLOCKED outside real Live
```

Always inspect the plan before clicking **Install**. Test the GUI as a normal GNOME desktop user, **not as root**. If desktop permissions aren't available, run only unit tests.

### Unit tests

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q meekro scripts
```

## Fedora RPM package

Build on Fedora (build dependencies: `rpm-build`, `tar`, `python3`):

```bash
sudo dnf install rpm-build tar
./scripts/build-rpm.sh
# Output: ~/rpmbuild/RPMS/noarch/meekro-welcome-0.1.0-1.fc44.noarch.rpm
```

This RPM places the application in `/usr/libexec/meekro`, a launcher in `/usr/bin`, `.desktop` autostart records and branded Cockpit/Anaconda CSS in `/etc/cockpit/branding`. The normal installed system ignores the Live welcome autostart because `--live` returns unless a Live environment is detected.

To install the RPM on a **throwaway test VM**:

```bash
sudo dnf install ~/rpmbuild/RPMS/noarch/meekro-welcome-*.rpm
meekro-welcome
```

Do **not** delete `anaconda-live`, `anaconda-webui` or the Anaconda backend from the Live image. They power the actual installation.

## Fedora GNOME Live ISO integration

The official image has its own GNOME/Fedora Live Welcome. We prevent that autostart and mask the stock `liveinst.desktop` desktop menu entry (without deleting the actual Anaconda installer), then launch `Meekro Live Installer` instead; web installer pages receive the branded CSS/logo.

1. Start from the **official Fedora 44 Workstation Live Kickstart template** matching your compose target. Obtain it from the Fedora Kickstarts repository and run `ksflatten` first; don't build from an unrelated old version.
2. Build `meekro-welcome` RPM. Publish it into a **local RPM repository that livemedia-creator can reach** during compose (`createrepo_c`), then add that repository to the compose Kickstart using a `repo --name=... --baseurl=...` directive. The path depends on your builder/container networking; test it inside that environment. Do not assume `file:///home/...` on the host will be available inside a mock chroot.
3. Patch the flattened template:

   ```bash
   python3 scripts/patch-kickstart.py fedora-workstation-flat.ks meekro-live.ks
   ```

   This adds Meekro dependencies to `%packages` and a `%post` to disable Fedora's *per-liveuser* autostart entry, which otherwise has precedence over `/etc/xdg/autostart`.

4. Inspect `meekro-live.ks`, verify the repository and root filesystem configuration, validate with `ksvalidator`, then build with the official `livemedia-creator` workflow. Example **reference invocation** (not tested with this project):

   ```bash
   sudo livemedia-creator --ks meekro-live.ks --no-virt \
     --resultdir /var/tmp/meekro-compose --make-iso \
     --project MeekroOS --iso-only --iso-name MeekroOS-Live-x86_64.iso \
     --releasever 44
   ```

   See [Fedora Live image documentation](https://fedoraproject.org/wiki/Livemedia-creator-_How_to_create_and_use_a_Live_CD).

5. Boot the result in **QEMU or GNOME Boxes** and inspect `/etc/cockpit/branding/branding.css` and `logo.png`. Confirm Fedora Welcome is masked, Meekro Live starts, Anaconda is styled and installation completes in a disposable VM disk.
6. Reboot that VM; GNOME Initial Setup may ask to create a user. When the user logs in, Meekro First Run must appear. Test a Fedora update and app installation before sharing the ISO.

The resulting ISO has not been generated in the current environment. Never test unverified install images on a disk with valuable data.

## Packaging improvements before beta

- Isolate installation privileges with **narrow polkit service methods** rather than launching a general privileged package manager.
- Install missing Flatpak/GUI dependencies inside RPM packaging and validate all catalog IDs against live Fedora 44 / Flathub metadata.
- Create robust on-disk run state, support per-step retry and a richer progress UI.
- Improve GNOME styling through versioned and tested Shell extension settings; *do not* promise universal Wayland window opacity.
- Implement optional user-confirmed NVIDIA/RPM Fusion setup with Secure Boot signing guidance.
- Test branded Anaconda WebUI styling against its supported asset paths on a composed image. Fully custom disk pages require an independent upstream-supported integration.
- Add `fedora-release` replacement and distro identification **only after** checking release package conflicts, updates, distribution naming, trademark and repository management. This v0.1 preview intentionally leaves `ID=fedora` so system package management stays reliable.

## Repository creation

The GitHub account linked in the conversation is `eekrob`, but the connected GitHub operations cannot create a new repository. An empty repository named `MeekroOS` must be created at GitHub first. Then from your extracted project:

```bash
git init -b main
git add .
git commit -m "Initial MeekroOS installer and control center preview"
git remote add origin https://github.com/eekrob/MeekroOS.git
git push -u origin main
```

Alternatively, once the empty repository exists, a connected GitHub tool with write access can upload files. Never commit generated ISO or package build artifacts into source control.

## Project layout

- `meekro/` — Python GTK4 application, catalog, planning, preferences, hardware checks and Easter egg.
- `desktop/` — app launchers and autostart policies.
- `branding/` — Anaconda WebUI-compatible Cockpit branding.
- `assets/` — MeekroOS icon supplied by project owner.
- `packaging/` — RPM specification.
- `scripts/` — build and Fedora Kickstart patching helpers.
- `tests/` — unit tests; GitHub Actions.

## Attribution

MeekroOS is an independent Fedora-derived work, not endorsed by Fedora or Red Hat. Fedora, GNOME, Anaconda, Flatpak, other names and trademarks belong to their respective owners. Package distributions have their own licenses.
