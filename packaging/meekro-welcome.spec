Name:           meekro-welcome
Version:        0.1.0
Release:        1%{?dist}
Summary:        MeekroOS Live Welcome, first run and GNOME Control Center
License:        MIT
URL:            https://github.com/eekrob/MeekroOS
Source0:        %{name}-%{version}.tar.gz
BuildArch:      noarch
Requires:       python3 >= 3.11
Requires:       python3-gobject
Requires:       gtk4
Requires:       libadwaita
Requires:       flatpak
Requires:       polkit
Requires:       dnf5

%description
MeekroOS application for branding the Live Welcome experience, choosing
software, customizing GNOME and installing developer/gaming tools.

%prep
%autosetup -n %{name}-%{version}

%build
# Pure Python, system GTK libraries.

%install
mkdir -p %{buildroot}%{_libexecdir}/meekro
cp -a meekro %{buildroot}%{_libexecdir}/meekro/
install -D -m 0755 scripts/meekro-welcome %{buildroot}%{_bindir}/meekro-welcome
install -D -m 0644 desktop/org.meekro.Welcome.desktop %{buildroot}%{_datadir}/applications/org.meekro.Welcome.desktop
install -D -m 0644 desktop/meekro-live-installer.desktop %{buildroot}%{_datadir}/applications/meekro-live-installer.desktop
install -D -m 0644 desktop/meekro-first-run.desktop %{buildroot}%{_sysconfdir}/xdg/autostart/meekro-first-run.desktop
install -D -m 0644 desktop/meekro-live-autostart.desktop %{buildroot}%{_sysconfdir}/xdg/autostart/meekro-live-autostart.desktop
install -D -m 0644 desktop/org.fedoraproject.welcome-screen.desktop %{buildroot}%{_sysconfdir}/xdg/autostart/org.fedoraproject.welcome-screen.desktop
install -D -m 0644 branding/branding.css %{buildroot}%{_sysconfdir}/cockpit/branding/branding.css
install -D -m 0644 assets/meekro-logo-256.png %{buildroot}%{_datadir}/icons/hicolor/256x256/apps/meekro-welcome.png
mkdir -p %{buildroot}%{_datadir}/meekro/assets
cp -a assets/meekro-logo-*.png %{buildroot}%{_datadir}/meekro/assets/
install -D -m 0644 assets/meekro-logo-256.png %{buildroot}%{_sysconfdir}/cockpit/branding/logo.png

%files
%{_bindir}/meekro-welcome
%{_libexecdir}/meekro/meekro
%{_datadir}/applications/org.meekro.Welcome.desktop
%{_datadir}/applications/meekro-live-installer.desktop
%{_datadir}/icons/hicolor/256x256/apps/meekro-welcome.png
%{_datadir}/meekro/assets
%config(noreplace) %{_sysconfdir}/xdg/autostart/meekro-first-run.desktop
%config(noreplace) %{_sysconfdir}/xdg/autostart/meekro-live-autostart.desktop
%config(noreplace) %{_sysconfdir}/xdg/autostart/org.fedoraproject.welcome-screen.desktop
%config(noreplace) %{_sysconfdir}/cockpit/branding/branding.css
%config(noreplace) %{_sysconfdir}/cockpit/branding/logo.png

%changelog
* Tue Oct 13 2026 MeekroOS Contributors <maintainer@invalid.example> - 0.1.0-1
- Initial preview package
