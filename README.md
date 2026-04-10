# Ultimate Wallpapers Manager

Gestionnaire de fonds d'écran intelligent pour Hyprland/Wayland.  
Change automatiquement le fond d'écran en fonction des médias en lecture et des jeux actifs.

## Fonctionnement

1. Récupère un média aléatoire depuis **Sonarr/Radarr** ou détecte un jeu actif via **Lutris/Steam**
2. Cherche un wallpaper correspondant sur **Wallhaven.cc**
3. Fallback sur le fanart stocké sur le NAS (Sonarr/Radarr)
4. Fallback final sur le dernier fond d'écran utilisé

Deux modes de déclenchement :
- **Watcher** — réagit en temps réel aux changements de piste MPRIS et aux fenêtres de jeux (Hyprland IPC)
- **Timer** — rotation aléatoire toutes les 30 minutes via systemd

---

## Prérequis

| Dépendance | Rôle |
|---|---|
| Python ≥ 3.11 | Runtime |
| `playerctl` | Écoute des événements MPRIS |
| `swww` / `hyprpaper` / `waypaper` | Backend d'affichage (au choix) |
| Hyprland | Détection des fenêtres actives |

Dépendances optionnelles : `lutris`, `steam`, Sonarr, Radarr.

---

## Installation (Arch Linux)

```bash
git clone https://github.com/acidtracks/ultimate_wallpapers_manager
cd ultimate_wallpapers_manager
makepkg -si
```

---

## Configuration

Copier le fichier de configuration exemple et l'éditer :

```bash
mkdir -p ~/.config/ultimate_wallpapers_manager
cp /usr/share/doc/ultimate-wallpapers-manager/config.example.toml \
   ~/.config/ultimate_wallpapers_manager/config.toml
```

### Paramètres principaux

```toml
[wallpaper]
backend = "swww"                        # swww | hyprpaper | waypaper
media_dir = "~/Images/Wallpapers/media" # dossier de stockage local
max_kept_files = 30                     # nombre de fichiers conservés

[sonarr]
url = "http://nas:8989"
api_key = "votre_clé"

[radarr]
url = "http://nas:7878"
api_key = "votre_clé"

[wallhaven]
url = "https://wallhaven.cc/api/v1/search"
api_key = ""  # optionnel, requis pour le contenu adulte

[timings]
cooldown_mpris = 10   # secondes minimum entre deux changements musique
cooldown_game  = 30   # secondes minimum entre deux changements jeu
debounce_mpris = 0.5  # délai de stabilisation MPRIS
debounce_game  = 5.0  # délai de stabilisation fenêtre

[watcher]
# Classes de fenêtres à ignorer (pas de changement de wallpaper)
ignore_window_classes = ["code", "kitty", "firefox", "discord"]
```

---

## Activation des services

```bash
# Daemon swww (démarré automatiquement par uwm-watcher, mais à activer une fois)
systemctl --user enable --now swww-daemon.service

# Watcher (écoute MPRIS + Hyprland en continu)
systemctl --user enable --now uwm-watcher.service

# Timer (rotation automatique toutes les 30 min)
systemctl --user enable --now uwm-rotate.timer
```

### Commandes utiles

```bash
# Vérifier l'état
systemctl --user status uwm-watcher
systemctl --user status uwm-rotate.timer

# Voir les logs en direct
journalctl --user -u uwm-watcher -f

# Forcer une rotation immédiate
systemctl --user start uwm-rotate.service
```

---

## Utilisation manuelle

```bash
# Rotation aléatoire
python -m uwm fetch

# Recherche ciblée
python -m uwm fetch --title "Dune"

# Démarrer le watcher manuellement (debug)
python -m uwm watch
```

---

## Structure du projet

```
uwm/
├── __main__.py       # Entrypoint CLI (python -m uwm)
├── config.py         # Chargement de la configuration
├── state.py          # Persistance de l'état entre rotations
├── fetcher.py        # Logique principale de récupération
├── watcher.py        # Daemon événementiel MPRIS + Hyprland
├── backends/         # Backends d'affichage
│   ├── swww.py
│   ├── hyprpaper.py
│   └── waypaper.py
├── searchers/        # Moteurs de recherche de wallpapers
│   └── wallhaven.py
└── sources/          # Sources de médias
    ├── sonarr.py
    ├── radarr.py
    └── games.py      # Lutris + Steam
```

---

## Désinstallation

```bash
systemctl --user disable --now uwm-watcher.service uwm-rotate.timer
sudo pacman -R ultimate-wallpapers-manager

# Supprimer la configuration (optionnel)
rm -rf ~/.config/ultimate_wallpapers_manager
```
