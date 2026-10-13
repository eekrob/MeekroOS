"""Meekro Welcome / Control Center (GTK4 + libadwaita)."""
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gtk, Gdk, GLib, Gio  # noqa: E402
from . import __version__
from .catalog import CATALOG, PRESETS
from .backend import build_plan, missing_programs, run_plan, installed, InstallError
from .settings import read, write, is_complete, mark_complete, SettingsError
from .appearance import apply_theme, enable_blur
from .hardware import collect, driver_advice
from .easter import EasterEgg

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ASSETS = Path("/usr/share/meekro/assets") if Path("/usr/share/meekro/assets").exists() else PROJECT_ROOT / "assets"

CSS = """
.meekro-title { font-size: 29px; font-weight: 800; }
.meekro-subtitle { color: alpha(currentColor, .70); }
.meekro-accent { color: #e93442; font-weight: 700; }
.meekro-panel { background: alpha(currentColor, .035); border-radius: 18px; padding: 18px; }
.meekro-section { font-weight: 750; font-size: 18px; }
.meekro-start { background: #e93442; color: white; }
.meekro-start:hover { background: #d22536; }
.meekro-log { font-family: monospace; font-size: 12px; }
"""

def live_environment():
    if Path("/run/initramfs/live").exists() or Path("/run/live/medium").exists():
        return True
    try:
        return "rd.live.image" in Path("/proc/cmdline").read_text()
    except OSError:
        return False

class Window(Adw.ApplicationWindow):
    def __init__(self, application, *, mode):
        super().__init__(application=application, title="MeekroOS", default_width=1100, default_height=760)
        self.mode = mode
        self.settings = read()
        self.selected = set(self.settings["selected"])
        self.easter = EasterEgg()
        self.installing = False
        self.stop_after_step = False
        self.log_text = []
        self.checks = {}
        self.grouping = {}
        self.toast = Adw.ToastOverlay()
        self.set_content(self.toast)
        self.base = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.toast.set_child(self.base)
        self._setup_style()
        self._build_shell()
        self.connect("close-request", self._protect_install)
        controller = Gtk.EventControllerKey()
        controller.connect("key-pressed", self._on_key)
        self.add_controller(controller)

    def _protect_install(self, *_):
        if self.installing:
            self._notify("Wait for the current package transaction to finish before closing.")
            return True
        return False

    def _setup_style(self):
        prov = Gtk.CssProvider()
        prov.load_from_data(CSS.encode())
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), prov, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    def _build_shell(self):
        header = Gtk.HeaderBar()
        self.base.append(header)
        title = Gtk.Label(label="MeekroOS  •  " + ("Live Installer" if self.mode == "live" else "Control Center"))
        title.add_css_class("meekro-accent")
        header.set_title_widget(title)
        self.stack = Gtk.Stack(transition_type=Gtk.StackTransitionType.SLIDE_LEFT_RIGHT, transition_duration=180)
        self.stack.set_hexpand(True)
        self.stack.set_vexpand(True)
        sidebar = Gtk.StackSidebar(stack=self.stack)
        sidebar.set_size_request(215, -1)
        wrapper = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        wrapper.append(sidebar)
        wrapper.append(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL))
        wrapper.append(self.stack)
        self.base.append(wrapper)
        if self.mode == "live":
            self._add_page("install", "Install MeekroOS", self._page_live())
        else:
            self._add_page("welcome", "Welcome", self._page_welcome())
            self._add_page("appearance", "Appearance", self._page_appearance())
            self._add_page("software", "Software", self._page_software())
            self._add_page("hardware", "Hardware", self._page_hardware())
            self._add_page("profiles", "Profiles & Export", self._page_profiles())
            self._add_page("about", "About", self._page_about())
        self.stack.set_visible_child_name("install" if self.mode == "live" else "welcome")

    def _add_page(self, ident, title, widget):
        scr = Gtk.ScrolledWindow(hscrollbar_policy=Gtk.PolicyType.NEVER, vscrollbar_policy=Gtk.PolicyType.AUTOMATIC)
        scr.set_child(widget)
        self.stack.add_titled(scr, ident, title)

    def _page(self):
        b = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=17)
        b.set_margin_top(32)
        b.set_margin_bottom(38)
        b.set_margin_start(38)
        b.set_margin_end(38)
        return b

    def _label(self, s, css=None, wrap=True):
        l = Gtk.Label(label=s, xalign=0)
        l.set_wrap(wrap)
        if css:
            l.add_css_class(css)
        return l

    def _button(self, label, callback, prominent=False):
        b = Gtk.Button(label=label)
        b.add_css_class("pill")
        if prominent:
            b.add_css_class("meekro-start")
        b.connect("clicked", callback)
        return b

    def _hero(self, text, subtitle):
        line = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=22)
        icon = ASSETS / "meekro-logo-128.png"
        if icon.exists():
            line.append(Gtk.Image.new_from_file(str(icon)))
        labels = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=7)
        labels.set_valign(Gtk.Align.CENTER)
        labels.append(self._label(text, "meekro-title"))
        labels.append(self._label(subtitle, "meekro-subtitle"))
        line.append(labels)
        return line

    def _page_live(self):
        b=self._page()
        b.append(self._hero("Install MeekroOS", "A Fedora-based workstation for developers and gamers."))
        b.append(Gtk.Separator())
        b.append(self._label("Your MeekroOS installer", "meekro-section"))
        b.append(self._label("The installer uses the Fedora Anaconda engine for disk selection, partitioning, encryption and bootloader setup. MeekroOS customizes its welcome experience and Anaconda WebUI branding."))
        b.append(self._label("WARNING: Installation can erase the selected drive. Back up important files before continuing."))
        b.append(self._button("Start disk installation", self._launch_installer, True))
        b.append(self._button("Try MeekroOS without installing", lambda *_: self.toast.add_toast(Adw.Toast.new("You're already in the Live environment."))))
        b.append(self._label("After installing and rebooting, Meekro Welcome will offer programs, themes, gaming tools and hardware information."))
        return b

    def _launch_installer(self, *_):
        if not live_environment():
            self._notify("Disk installation is only available in a genuine Live ISO session.")
            return
        exe=Path("/usr/bin/liveinst")
        if not exe.exists():
            self._notify("Anaconda Live installer is missing: anaconda-live package required.")
            return
        try:
            subprocess.Popen([str(exe)], start_new_session=True, close_fds=True)
            self._notify("Launching Anaconda installer…")
        except OSError as exc:
            self._notify(f"Cannot launch installer: {exc}")

    def _page_welcome(self):
        b=self._page()
        b.append(self._hero("Welcome to MeekroOS", "Build. Play. Make it yours."))
        b.append(Gtk.Separator())
        b.append(self._label("First-run setup", "meekro-section"))
        b.append(self._label("1. Choose your GNOME appearance.\n2. Pick a developer, gaming or hybrid profile.\n3. Select apps and approve installation.\n4. Review hardware and export your configuration."))
        b.append(self._button("Customize appearance →", lambda *_: self.stack.set_visible_child_name("appearance"), True))
        b.append(self._button("Choose software →", lambda *_: self.stack.set_visible_child_name("software")))
        if self.mode == "first-run":
            b.append(Gtk.Separator())
            b.append(self._label("You can finish now and return to Control Center later."))
            b.append(self._button("Finish first run", self._finish))
        return b

    def _finish(self, *_):
        self._save()
        mark_complete()
        self._notify("MeekroOS first-run setup completed!")
        self.mode="control-center"

    def _page_appearance(self):
        b=self._page()
        b.append(self._label("GNOME Appearance", "meekro-title"))
        b.append(self._label("Theme settings are applied to your GNOME user session; no system files are overwritten."))
        current = self.settings["theme"]
        for theme, caption in (("dark","Meekro Dark"),("light","Meekro Light"),("system","Use system default")):
            item = Gtk.CheckButton(label=caption)
            item.set_active(current == theme)
            if hasattr(self, "theme_root"):
                item.set_group(self.theme_root)
            else:
                self.theme_root=item
            item.connect("toggled", lambda x, t=theme: self._theme_selected(t) if x.get_active() else None)
            b.append(item)
        b.append(self._button("Apply GNOME theme + red accent", self._apply_theme, True))
        b.append(Gtk.Separator())
        b.append(self._label("Blur & opacity", "meekro-section"))
        sw=Gtk.Switch(active=bool(self.settings["blur"]))
        sw.connect("notify::active", lambda s, *_: self._blur_selected(s.get_active()))
        h=Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
        h.append(self._label("Blur my Shell (GNOME Shell elements)"))
        h.append(sw)
        b.append(h)
        b.append(self._label("GNOME Wayland has no supported universal window opacity slider. Blur my Shell affects GNOME Shell surfaces such as the overview, dash and panel, not every application window."))
        b.append(self._button("Install selected blur extension", self._install_blur))
        b.append(self._button("Enable installed blur extension", lambda *_: self._notify(enable_blur())))
        b.append(self._label("For advanced extension options, use GNOME Extension Manager after installation."))
        return b

    def _theme_selected(self, theme):
        self.settings["theme"] = theme
        self._save()

    def _blur_selected(self, enable):
        self.settings["blur"] = bool(enable)
        self._save()

    def _apply_theme(self, *_):
        for message in apply_theme(self.settings["theme"]):
            self._notify(message)

    def _install_blur(self, *_):
        self.selected.add("blur")
        if "blur" in self.checks:
            self.checks["blur"].set_active(True)
        self._save()
        self.stack.set_visible_child_name("software")
        self._notify("Blur my Shell added to software selection. Install it from Software.")

    def _page_software(self):
        b = self._page()
        b.append(self._label("Software Center", "meekro-title"))
        b.append(self._label("Install Fedora RPMs with DNF5 and optional user-scoped Flathub applications. All operations require your approval."))
        for category in ("Developer", "Gaming", "Everyday", "Appearance"):
            exp=Gtk.Expander(label=category)
            exp.set_expanded(category in {"Developer", "Gaming"})
            content=Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=7)
            content.set_margin_top(12)
            content.set_margin_bottom(12)
            for item in CATALOG:
                if item.category != category:
                    continue
                line=Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=7)
                checkbox=Gtk.CheckButton(label=item.title)
                checkbox.set_tooltip_text(f"{item.description} · {item.kind.upper()}: {item.package}")
                checkbox.set_active(item.id in self.selected)
                checkbox.connect("toggled", self._app_toggled, item.id)
                self.checks[item.id] = checkbox
                line.append(checkbox)
                if item.kind=="flatpak":
                    line.append(self._label("Flathub", "meekro-subtitle"))
                content.append(line)
            exp.set_child(content)
            b.append(exp)
        h=Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        self.flathub_check=Gtk.CheckButton(label="I agree to add Flathub to my user account for selected apps")
        self.flathub_check.set_active(self.settings["flathub"])
        self.flathub_check.connect("toggled", lambda w: self._flathub_selected(w.get_active()))
        h.append(self.flathub_check)
        b.append(h)
        b.append(self._button("Check installed applications", self._check_installed))
        bar=Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        bar.append(self._button("Preview installation", self._preview_plan))
        self.install_button=self._button("Install selected", self._install, True)
        bar.append(self.install_button)
        self.cancel_button=self._button("Stop after current transaction", self._cancel)
        self.cancel_button.set_sensitive(False)
        bar.append(self.cancel_button)
        b.append(bar)
        self.log=Gtk.TextView(editable=False, cursor_visible=False, monospace=True, wrap_mode=Gtk.WrapMode.WORD_CHAR)
        self.log.add_css_class("meekro-log")
        sc=Gtk.ScrolledWindow(min_content_height=175, vexpand=False)
        sc.set_child(self.log)
        b.append(sc)
        return b

    def _check_installed(self, *_):
        self._notify("Checking Fedora RPMs and user Flatpaks…")
        def worker():
            found=[item.id for item in CATALOG if installed(item.id)]
            GLib.idle_add(self._show_installed, found)
        threading.Thread(target=worker, daemon=True).start()

    def _show_installed(self, found):
        for item_id, widget in self.checks.items():
            widget.set_tooltip_text("Already installed" if item_id in found else "Not detected as installed (or installed system-wide as Flatpak)")
        self._notify(f"Detected {len(found)} installed items. Hover names to see status.")
        return False

    def _app_toggled(self, widget, item_id):
        if widget.get_active():
            self.selected.add(item_id)
        else:
            self.selected.discard(item_id)
        self._save()

    def _flathub_selected(self, enabled):
        self.settings["flathub"]=bool(enabled)
        self._save()

    def _get_plan(self):
        return build_plan(sorted(self.selected), self.settings["flathub"])

    def _preview_plan(self, *_):
        try:
            plan=self._get_plan()
            self._set_log("\n".join(step.title+"\n    "+" ".join(step.argv) for step in plan) or "Nothing selected")
            if missing_programs(plan):
                self._append_log("Missing executables: "+", ".join(missing_programs(plan)))
        except InstallError as exc:
            self._notify(str(exc))

    def _install(self, *_):
        if self.installing:
            return
        try:
            plan=self._get_plan()
        except InstallError as exc:
            self._notify(str(exc))
            return
        if not plan:
            self._notify("Select programs first.")
            return
        missing=missing_programs(plan)
        if missing:
            self._notify("Missing prerequisites: "+", ".join(missing))
            return
        # Explicit review before executing privileged package changes.
        self._confirm_install(plan)

    def _confirm_install(self, plan):
        dlg=Gtk.Window(title="Confirm software installation", transient_for=self, modal=True, default_width=480)
        content=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=16)
        content.set_margin_top(24); content.set_margin_bottom(24);content.set_margin_start(24);content.set_margin_end(24)
        content.append(self._label(f"Run {len(plan)} installation operations?", "meekro-section"))
        content.append(self._label("RPM packages require a polkit authorization dialog. Flatpak applications use the user-scoped Flathub remote. Package management will contact external repositories. Not a rollback-safe transaction."))
        row=Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,spacing=10)
        row.append(self._button("Cancel", lambda *_: dlg.close()))
        def go(*_):
            dlg.close()
            self._start_worker(plan)
        row.append(self._button("Install", go,True))
        content.append(row);dlg.set_child(content);dlg.present()

    def _start_worker(self, plan):
        self.installing=True
        self.stop_after_step=False
        self.install_button.set_sensitive(False)
        self.cancel_button.set_sensitive(True)
        self._set_log("")
        def worker():
            result=run_plan(plan, lambda t: GLib.idle_add(self._append_log,t), lambda: self.stop_after_step)
            GLib.idle_add(self._installed_finished,result)
        threading.Thread(target=worker,daemon=True).start()

    def _installed_finished(self,result):
        self.installing=False
        self.install_button.set_sensitive(True)
        self.cancel_button.set_sensitive(False)
        good=bool(result) and all(code==0 for _,code in result)
        self._notify("All selected operations finished." if good else "Installation stopped or failed; see log.")
        return False

    def _cancel(self, *_):
        self.stop_after_step=True
        self._notify("Stopping safely after current operation completes.")

    def _set_log(self,text):
        self.log_text = [text] if text else []
        self.log.get_buffer().set_text(text)

    def _append_log(self,text):
        if len(self.log_text)>400:
            self.log_text=self.log_text[-350:]
        self.log_text.append(text)
        self.log.get_buffer().set_text("\n".join(self.log_text))
        return False

    def _page_hardware(self):
        b=self._page()
        b.append(self._label("Hardware & Drivers", "meekro-title"))
        b.append(self._label("Read-only detection. No third-party driver repositories or Secure Boot settings are changed without your approval."))
        self.hardware_report=self._label("Click Detect to inspect graphics hardware.")
        self.hardware_report.set_selectable(True)
        b.append(self._button("Detect hardware", self._detect_hardware, True))
        b.append(self.hardware_report)
        b.append(self._button("Select Mesa/Vulkan tools", self._select_graphics))
        b.append(self._label("NVIDIA proprietary drivers are intentionally not installed automatically. Repositories, driver signatures and Secure Boot must be reviewed separately."))
        return b

    def _detect_hardware(self, *_):
        info=collect()
        lines=[f"{key}: {val}" for key,val in info.items()]
        lines.append("\n"+driver_advice(info))
        self.hardware_report.set_text("\n".join(lines))

    def _select_graphics(self, *_):
        self.selected.update({"mesa-vulkan", "vulkan-tools"})
        self._sync_checks()
        self._save()
        self.stack.set_visible_child_name("software")
        self._notify("Mesa/Vulkan tools selected; review and install in Software.")

    def _page_profiles(self):
        b=self._page()
        b.append(self._label("Profiles & Settings", "meekro-title"))
        b.append(self._label("Profiles select software, but do not auto-install anything. Changes can be reviewed in Software."))
        for name, ids in PRESETS.items():
            b.append(self._button(f"Select {name} ({len(ids)} apps)", lambda _x, n=name: self._preset(n)))
        b.append(self._button("Clear software selection", self._clear_apps))
        b.append(Gtk.Separator())
        b.append(self._label("Export / Import", "meekro-section"))
        b.append(self._label("Export contains only theme, selected app IDs and Flathub choice; no passwords or tokens."))
        row=Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        row.append(self._button("Export JSON", self._export))
        row.append(self._button("Import JSON", self._import))
        b.append(row)
        return b

    def _preset(self, name):
        self.selected=set(PRESETS[name])
        self._sync_checks()
        self._save()
        self._notify(name+" profile selected. Review installation in Software.")

    def _clear_apps(self, *_):
        self.selected.clear()
        self._sync_checks()
        self._save()

    def _sync_checks(self):
        for ident, widget in self.checks.items():
            widget.set_active(ident in self.selected)

    def _export(self, *_):
        dialog=Gtk.FileChooserNative(title="Export Meekro settings",transient_for=self,action=Gtk.FileChooserAction.SAVE,accept_label="Export",cancel_label="Cancel")
        dialog.set_current_name("meekro-profile.json")
        def saved(d,response):
            if response==Gtk.ResponseType.ACCEPT:
                file=d.get_file()
                if file and file.get_path():
                    try:
                        write(self._state(),file.get_path())
                        self._notify("Profile exported.")
                    except OSError as exc:
                        self._notify(str(exc))
            d.destroy()
        dialog.connect("response",saved)
        dialog.show()

    def _import(self, *_):
        dialog=Gtk.FileChooserNative(title="Import Meekro settings",transient_for=self,action=Gtk.FileChooserAction.OPEN,accept_label="Import",cancel_label="Cancel")
        def opened(d,response):
            if response==Gtk.ResponseType.ACCEPT:
                file=d.get_file()
                if file and file.get_path():
                    try:
                        self.settings=read(file.get_path())
                        self.selected=set(self.settings["selected"])
                        self._sync_checks()
                        self.flathub_check.set_active(self.settings["flathub"])
                        self._save()
                        self._notify("Settings imported. Click Apply in Appearance to change GNOME theme.")
                    except (OSError,ValueError,SettingsError,json.JSONDecodeError) as exc:
                        self._notify("Could not import JSON: "+str(exc))
            d.destroy()
        dialog.connect("response",opened)
        dialog.show()

    def _page_about(self):
        b=self._page()
        b.append(self._hero("MeekroOS", "Developer • Gamer • Free to customize"))
        b.append(self._label("Version " + __version__))
        b.append(self._label("GNOME workstation on Fedora. Installer powered by Anaconda.\nBuilt for development, games and custom desktops."))
        b.append(self._label("Hint: There's a little secret hidden in the name of its creator…", "meekro-subtitle"))
        return b

    def _state(self):
        return {**self.settings,"selected": sorted(self.selected)}

    def _save(self):
        try:
            self.settings=write(self._state())
        except (OSError,SettingsError) as exc:
            self._notify("Failed to save: "+str(exc))

    def _notify(self,msg):
        self.toast.add_toast(Adw.Toast.new(str(msg)[:250]))

    def _on_key(self,_controller,keyval,_keycode,_state):
        point=Gdk.keyval_to_unicode(keyval)
        if point and self.easter.feed(chr(point)):
            self._easter_dialog()
        return False

    def _easter_dialog(self):
        dialog=Gtk.Window(title="Secret unlocked ✦",transient_for=self,modal=True,default_width=415)
        c=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=14)
        c.set_margin_top(26);c.set_margin_bottom(26);c.set_margin_start(30);c.set_margin_end(30)
        c.append(self._hero("eekrob_", "You found the developer Easter egg!"))
        c.append(self._label("Some secrets are hidden in plain sight.\nMeekroOS • made for those who build and play."))
        c.append(self._button("Keep exploring",lambda *_: dialog.close(),True))
        dialog.set_child(c);dialog.present()

class Application(Adw.Application):
    def __init__(self,mode):
        super().__init__(application_id="org.meekro.Welcome", flags=Gio.ApplicationFlags.DEFAULT_FLAGS)
        self.mode=mode
    def do_activate(self):
        win=self.props.active_window
        if not win:
            win=Window(self,mode=self.mode)
        win.present()

def main():
    args=set(sys.argv[1:])
    if "--live" in args:
        if not live_environment() and not os.environ.get("MEEKRO_DEV_PREVIEW"):
            return 0
        mode="live"
    elif "--first-run" in args:
        if live_environment() or is_complete():
            return 0
        mode="first-run"
    else:
        mode="control-center"
    return Application(mode).run([sys.argv[0]])

if __name__=="__main__":
    raise SystemExit(main())
