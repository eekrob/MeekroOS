"""Audited catalog of packages; no user-supplied command templates."""
from dataclasses import dataclass
from typing import Literal

Kind = Literal["dnf", "flatpak"]

@dataclass(frozen=True)
class Item:
    id: str
    title: str
    category: str
    kind: Kind
    package: str
    description: str = ""

CATALOG: tuple[Item, ...] = (
    Item("python", "Python 3", "Developer", "dnf", "python3", "System Python; create virtual environments for projects"),
    Item("python-pip", "pip + venv", "Developer", "dnf", "python3-pip", "Python package management"),
    Item("uv", "uv", "Developer", "dnf", "uv", "Modern Python package and project manager"),
    Item("nodejs", "Node.js", "Developer", "dnf", "nodejs", "JavaScript runtime"),
    Item("npm", "npm", "Developer", "dnf", "nodejs-npm", "Node package manager"),
    Item("git", "Git", "Developer", "dnf", "git", "Version control"),
    Item("gh", "GitHub CLI", "Developer", "dnf", "gh", "GitHub command-line tools"),
    Item("gcc", "GCC + Make", "Developer", "dnf", "gcc", "C/C++ toolchain"),
    Item("make", "GNU Make", "Developer", "dnf", "make", "Build automation"),
    Item("cmake", "CMake", "Developer", "dnf", "cmake", "Build system"),
    Item("rust", "Rust and Cargo", "Developer", "dnf", "rust", "Rust compiler"),
    Item("cargo", "Cargo", "Developer", "dnf", "cargo", "Rust package manager"),
    Item("golang", "Go", "Developer", "dnf", "golang", "Go toolchain"),
    Item("podman", "Podman", "Developer", "dnf", "podman", "Rootless containers"),
    Item("distrobox", "Distrobox", "Developer", "dnf", "distrobox", "Containerized development environments"),
    Item("vscode", "Visual Studio Code", "Developer", "flatpak", "com.visualstudio.code", "Microsoft VS Code via Flathub; sandbox may limit toolchains"),
    Item("vscodium", "VSCodium", "Developer", "flatpak", "com.vscodium.codium", "Open source editor"),
    Item("zed", "Zed", "Developer", "flatpak", "dev.zed.Zed", "Fast code editor"),
    Item("neovim", "Neovim", "Developer", "dnf", "neovim", "Terminal editor"),
    Item("gnome-builder", "GNOME Builder", "Developer", "flatpak", "org.gnome.Builder", "GNOME-native IDE"),
    Item("steam", "Steam", "Gaming", "flatpak", "com.valvesoftware.Steam", "Steam games; Proton can be configured inside Steam"),
    Item("heroic", "Heroic Games Launcher", "Gaming", "flatpak", "com.heroicgameslauncher.hgl", "Epic/GOG/Amazon library"),
    Item("lutris", "Lutris", "Gaming", "flatpak", "net.lutris.Lutris", "Manage games and runners"),
    Item("bottles", "Bottles", "Gaming", "flatpak", "com.usebottles.bottles", "Manage Wine bottles"),
    Item("protonup", "ProtonUp-Qt", "Gaming", "flatpak", "net.davidotek.pupgui2", "Manage GE-Proton releases"),
    Item("mangohud", "MangoHud", "Gaming", "dnf", "mangohud", "FPS and hardware overlay"),
    Item("gamemode", "GameMode", "Gaming", "dnf", "gamemode", "On-demand game performance mode"),
    Item("wine", "Wine", "Gaming", "dnf", "wine", "Windows compatibility layer"),
    Item("mesa-vulkan", "Mesa Vulkan drivers", "Gaming", "dnf", "mesa-vulkan-drivers", "Open-source graphics Vulkan drivers"),
    Item("vulkan-tools", "Vulkan diagnostics", "Gaming", "dnf", "vulkan-tools", "vulkaninfo and other graphics diagnostics"),
    Item("obs", "OBS Studio", "Gaming", "flatpak", "com.obsproject.Studio", "Streaming and screen recording"),
    Item("firefox", "Firefox", "Everyday", "dnf", "firefox", "Browser"),
    Item("chromium", "Chromium", "Everyday", "dnf", "chromium", "Open-source browser"),
    Item("brave", "Brave", "Everyday", "flatpak", "com.brave.Browser", "Privacy-focused browser"),
    Item("telegram", "Telegram", "Everyday", "flatpak", "org.telegram.desktop", "Messaging"),
    Item("vesktop", "Vesktop", "Everyday", "flatpak", "dev.vencord.Vesktop", "Discord-compatible client"),
    Item("vlc", "VLC", "Everyday", "flatpak", "org.videolan.VLC", "Media player"),
    Item("obsidian", "Obsidian", "Everyday", "flatpak", "md.obsidian.Obsidian", "Notes"),
    Item("krita", "Krita", "Everyday", "flatpak", "org.kde.krita", "Digital painting"),
    Item("blender", "Blender", "Everyday", "flatpak", "org.blender.Blender", "3D creation"),
    Item("libreoffice", "LibreOffice", "Everyday", "dnf", "libreoffice", "Office suite"),
    Item("gnome-tweaks", "GNOME Tweaks", "Appearance", "dnf", "gnome-tweaks", "GNOME appearance controls"),
    Item("extension-manager", "Extension Manager", "Appearance", "flatpak", "com.mattjakeman.ExtensionManager", "GNOME Shell extension manager"),
    Item("blur", "Blur my Shell", "Appearance", "dnf", "gnome-shell-extension-blur-my-shell", "Blur overview, dash, shell UI; not arbitrary app windows"),
)

BY_ID = {item.id: item for item in CATALOG}
PRESETS: dict[str, tuple[str, ...]] = {
    "Developer": ("python", "python-pip", "nodejs", "npm", "git", "gh", "gcc", "make", "cmake", "podman", "vscodium", "neovim"),
    "Gamer": ("steam", "heroic", "lutris", "bottles", "protonup", "mangohud", "gamemode", "obs"),
}
PRESETS["Hybrid"] = tuple(dict.fromkeys(PRESETS["Developer"] + PRESETS["Gamer"]))
